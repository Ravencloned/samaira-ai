"""
Conversation orchestrator for SamairaAI.
Coordinates between intent detection, safety checks, calculations, and LLM.
"""

from typing import Optional
from dataclasses import dataclass

from core.state import SessionState, GoalType, ConversationPhase
from core.intent import detect_intent, IntentType, IntentResult
from core.safety import (
    check_safety, 
    SafetyCheckResult, 
    SafetyTriggerType,
    format_handoff_response,
    inject_disclaimer,
    detect_projection_in_response,
    detect_calculation_in_response
)
from services.gemini_client import gemini_client
from financial.calculators import (
    calculate_sip, 
    calculate_rd, 
    compare_sip_vs_rd,
    calculate_goal_corpus,
    format_amount_indian
)
from financial.goals import (
    get_goal_template,
    detect_goal_from_text,
    generate_goal_summary,
    get_goal_planning_questions
)
from financial.schemes import (
    get_scheme_info,
    get_scheme_explanation_hinglish,
    format_scheme_comparison
)


@dataclass
class ConversationResponse:
    """Response from the conversation orchestrator."""
    text: str
    intent: IntentResult
    safety_check: SafetyCheckResult
    calculation_data: Optional[dict] = None
    should_speak: bool = True
    metadata: dict = None
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "intent": self.intent.primary_intent.value,
            "confidence": self.intent.confidence,
            "entities": self.intent.entities,
            "is_safe": self.safety_check.is_safe,
            "safety_trigger": self.safety_check.trigger_type.value,
            "handoff_requested": self.safety_check.should_handoff,
            "calculation_data": self.calculation_data,
            "should_speak": self.should_speak,
            "metadata": self.metadata or {}
        }


class ConversationOrchestrator:
    """
    Main conversation controller.
    Routes user input through safety, intent, and response generation.
    """
    
    def __init__(self):
        pass
    
    async def process_message(
        self,
        user_message: str,
        session: SessionState
    ) -> ConversationResponse:
        """
        Process a user message and generate response.
        
        Flow:
        1. Safety check
        2. Intent detection
        3. Context building (calculations if needed)
        4. LLM response generation
        5. Disclaimer injection
        6. Update session state
        """
        # Step 1: Safety check
        safety_result = check_safety(user_message)
        
        # Step 2: Intent detection
        intent_result = detect_intent(user_message)
        
        # Step 3: Handle safety triggers
        if not safety_result.is_safe:
            response = await self._handle_safety_trigger(
                safety_result, session, user_message
            )
            return response
        
        # Step 4: Build context and get calculations if needed
        context, calculation_data = await self._build_context(
            intent_result, user_message, session
        )
        
        # Step 5: Get LLM response
        llm_response = await gemini_client.chat(
            user_message, session, context
        )
        
        # Step 6: Inject disclaimers if needed
        has_projection = detect_projection_in_response(llm_response)
        has_calculation = detect_calculation_in_response(llm_response)
        
        if has_projection or has_calculation:
            llm_response = inject_disclaimer(llm_response, has_projection, has_calculation)
            session.disclaimers_shown += 1
        
        # Step 7: Update session state
        self._update_session(session, user_message, llm_response, intent_result)
        
        return ConversationResponse(
            text=llm_response,
            intent=intent_result,
            safety_check=safety_result,
            calculation_data=calculation_data,
            metadata={
                "phase": session.current_phase.value,
                "has_goal": session.current_goal is not None
            }
        )
    
    async def _handle_safety_trigger(
        self,
        safety_result: SafetyCheckResult,
        session: SessionState,
        user_message: str
    ) -> ConversationResponse:
        """Handle messages that trigger safety boundaries."""
        
        # Get formatted handoff response
        response_text = format_handoff_response(
            safety_result.trigger_type,
            session.user_name
        )
        
        # For advisory boundary, we can still be helpful
        if safety_result.trigger_type == SafetyTriggerType.ADVISORY_BOUNDARY:
            # Let LLM provide educational context while maintaining boundary
            context = (
                "User is asking for specific recommendations which you cannot provide. "
                "Politely decline specific recommendations but offer to educate about "
                "how to evaluate options themselves. Maintain warm, helpful tone."
            )
            response_text = await gemini_client.chat(user_message, session, context)
            session.mark_advisory_boundary()
        
        # For hard handoff triggers, use template response
        if safety_result.should_handoff:
            session.trigger_handoff(safety_result.trigger_type.value)
        
        # Create intent result for safety-triggered response
        intent_result = IntentResult(
            primary_intent=IntentType.UNCLEAR,
            confidence=0.0,
            entities={},
            secondary_intents=[]
        )
        
        # Update session
        session.add_message("user", user_message)
        session.add_message("assistant", response_text)
        
        return ConversationResponse(
            text=response_text,
            intent=intent_result,
            safety_check=safety_result,
            metadata={"safety_triggered": True}
        )
    
    async def _build_context(
        self,
        intent: IntentResult,
        user_message: str,
        session: SessionState
    ) -> tuple[Optional[str], Optional[dict]]:
        """Build context for LLM based on intent and entities."""
        
        context_parts = []
        calculation_data = None
        
        # Handle comparison requests
        if intent.primary_intent == IntentType.COMPARE_OPTIONS:
            if "sip" in user_message.lower() and "rd" in user_message.lower():
                # SIP vs RD comparison
                amount = intent.entities.get("amount", 5000)
                years = intent.entities.get("duration_years", 10)
                comparison = compare_sip_vs_rd(amount, years)
                context_parts.append(f"Calculation context: {comparison['summary_hinglish']}")
                calculation_data = comparison
        
        # Handle calculation requests
        elif intent.primary_intent == IntentType.CALCULATE:
            amount = intent.entities.get("amount")
            years = intent.entities.get("duration_years")
            
            if amount and years:
                sip_result = calculate_sip(amount, years)
                context_parts.append(f"SIP Calculation: {sip_result.format_summary_hinglish()}")
                calculation_data = sip_result.to_dict()
        
        # Handle goal planning
        elif intent.primary_intent in [
            IntentType.GOAL_PLANNING, 
            IntentType.GOAL_EDUCATION,
            IntentType.GOAL_WEDDING,
            IntentType.GOAL_HOME,
            IntentType.GOAL_RETIREMENT
        ]:
            detected_goal = detect_goal_from_text(user_message)
            if detected_goal:
                template = get_goal_template(detected_goal)
                if template:
                    context_parts.append(
                        f"User is planning for: {template.name_hinglish}. "
                        f"Typical timeline: {template.typical_timeline_years} years. "
                        f"Typical cost: ₹{template.typical_cost_range[0]}-{template.typical_cost_range[1]} lakhs. "
                        f"Ask clarifying questions: {template.planning_questions[0]}"
                    )
                    
                    # Update session goal
                    goal_type_map = {
                        "child_education": GoalType.CHILD_EDUCATION,
                        "daughter_wedding": GoalType.WEDDING,
                        "home_downpayment": GoalType.HOME_DOWNPAYMENT,
                        "retirement": GoalType.RETIREMENT,
                    }
                    if detected_goal in goal_type_map:
                        session.set_goal(goal_type_map[detected_goal])
        
        # Handle scheme info requests
        elif intent.primary_intent == IntentType.SCHEME_INFO:
            # Detect which scheme
            for scheme_code in ["ppf", "ssy", "nps", "pmjjby", "pmsby", "scss"]:
                if scheme_code in user_message.lower():
                    explanation = get_scheme_explanation_hinglish(scheme_code)
                    context_parts.append(f"Scheme information: {explanation}")
                    break
        
        # Handle SIP info
        elif intent.primary_intent == IntentType.SIP_INFO:
            context_parts.append(
                "User wants to know about SIP. Key points: "
                "SIP = Systematic Investment Plan in mutual funds. "
                "Can start with ₹500/month. Rupee cost averaging benefit. "
                "Market-linked returns (~10-12% historical). "
                "Good for long-term goals (5+ years)."
            )
        
        # Handle RD info
        elif intent.primary_intent == IntentType.RD_INFO:
            context_parts.append(
                "User wants to know about RD. Key points: "
                "RD = Recurring Deposit in bank. "
                "Fixed returns (~6-7% currently). "
                "Government guarantee up to ₹5 lakhs. "
                "Good for short-term goals or risk-averse users."
            )
        
        context = " | ".join(context_parts) if context_parts else None
        return context, calculation_data
    
    def _update_session(
        self,
        session: SessionState,
        user_message: str,
        response: str,
        intent: IntentResult
    ):
        """Update session state after processing."""
        # Add messages to history
        session.add_message("user", user_message)
        session.add_message("assistant", response)
        
        # Track detected intents
        if intent.primary_intent not in [IntentType.UNCLEAR, IntentType.CHITCHAT]:
            if intent.primary_intent.value not in session.detected_intents:
                session.detected_intents.append(intent.primary_intent.value)
        
        # Update phase based on intent
        if intent.primary_intent == IntentType.GREETING:
            session.current_phase = ConversationPhase.GREETING
        elif intent.primary_intent in [
            IntentType.GOAL_PLANNING, IntentType.GOAL_EDUCATION,
            IntentType.GOAL_WEDDING, IntentType.GOAL_HOME, IntentType.GOAL_RETIREMENT
        ]:
            session.current_phase = ConversationPhase.GOAL_DISCOVERY
        elif intent.primary_intent in [IntentType.EXPLAIN_CONCEPT, IntentType.SCHEME_INFO]:
            session.current_phase = ConversationPhase.EDUCATING
        elif intent.primary_intent == IntentType.CALCULATE:
            session.current_phase = ConversationPhase.CALCULATING
        
        # Try to extract user name if mentioned
        self._extract_user_name(user_message, session)
    
    def _extract_user_name(self, text: str, session: SessionState):
        """Try to extract user's name from message."""
        if session.user_name:
            return
        
        # Common patterns: "mera naam X hai", "I am X", "main X hoon"
        import re
        patterns = [
            r"(?:mera\s+naam|my\s+name\s+is|i\s+am|main)\s+([A-Za-z]+)",
            r"([A-Za-z]+)\s+(?:bol\s+raha|speaking)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 2 and name.lower() not in ["hai", "hoon", "hun", "the"]:
                    session.user_name = name
                    break


# Global orchestrator instance
orchestrator = ConversationOrchestrator()
