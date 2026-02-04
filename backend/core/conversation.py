"""
Conversation orchestrator for SamairaAI.
Coordinates between intent detection, safety checks, calculations, and LLM.
Enhanced with data hub, goal interview, and knowledge base for deeper advice.
"""

from typing import Optional
from dataclasses import dataclass

from core.state import SessionState, GoalType, ConversationPhase
from core.intent import detect_intent, IntentType, IntentResult
from core.postprocess import clean_response
from core.safety import (
    check_safety, 
    SafetyCheckResult, 
    SafetyTriggerType,
    format_handoff_response,
    inject_disclaimer,
    detect_projection_in_response,
    detect_calculation_in_response
)
from services.llm_service import llm_service
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

# Import new modules for enhanced advisor
from services.data_hub import data_hub
from core.goal_interview import goal_interview, GoalCategory
from financial.knowledge_base import knowledge_base


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
        llm_response = await llm_service.chat(
            user_message, session, context
        )
        
        # Step 6: Inject disclaimers if needed
        has_projection = detect_projection_in_response(llm_response)
        has_calculation = detect_calculation_in_response(llm_response)
        
        if has_projection or has_calculation:
            llm_response = inject_disclaimer(llm_response, has_projection, has_calculation)
            session.disclaimers_shown += 1
        
        # Step 7: Clean response (remove re-introductions after turn 1)
        turn_number = len(session.conversation_history) // 2 + 1
        llm_response = clean_response(llm_response, turn_number=turn_number)
        
        # Step 8: Update session state
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
            response_text = await llm_service.chat(user_message, session, context)
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
        """Build rich context for LLM based on intent, data hub, and knowledge base."""
        
        context_parts = []
        calculation_data = None
        
        # === GOAL INTERVIEW INTEGRATION ===
        # Extract info from user message and update profile
        interview_state = goal_interview.get_or_create_state(session.session_id)
        extracted = goal_interview.extract_info_from_message(user_message, interview_state)
        
        # Detect goal from message
        detected_goal_cat = goal_interview.detect_goal_from_message(user_message)
        if detected_goal_cat:
            goal_interview.set_goal(session.session_id, detected_goal_cat)
        
        # Add interview context (user profile + suggested questions)
        interview_context = goal_interview.get_interview_context(session.session_id)
        if interview_context:
            context_parts.append(interview_context)
        
        # === KNOWLEDGE BASE RETRIEVAL ===
        kb_context = knowledge_base.get_context_for_query(user_message)
        if kb_context:
            context_parts.append(kb_context)
        
        # === DATA HUB - LIVE RATES ===
        # Detect if user mentioned a bank
        user_bank = interview_state.profile.primary_bank
        if not user_bank:
            bank_code = data_hub.resolve_bank_name(user_message)
            if bank_code:
                user_bank = bank_code
                interview_state.profile.primary_bank = bank_code
        
        # Add relevant financial data based on intent/query
        query_type = self._detect_query_type(user_message, intent)
        data_context = data_hub.get_context_for_llm(user_bank, query_type)
        if data_context:
            context_parts.append(data_context)
        
        # === SPECIFIC FD/BANK RATE QUERIES ===
        if "fd" in user_message.lower() or "fixed deposit" in user_message.lower():
            if user_bank:
                rate_info = data_hub.get_bank_fd_rate(user_bank)
                if rate_info:
                    context_parts.append(
                        f"\n**{rate_info['bank']} FD Rates:**\n"
                        f"- 1 Year: {rate_info['general_rate']}% (Senior: {rate_info['senior_rate']}%)\n"
                        f"Source: {rate_info['source']}"
                    )
            else:
                # Show best FD rates
                best_rates = data_hub.get_best_fd_rates(12, False, 5)
                if best_rates:
                    rates_text = "\n**Top FD Rates (1 Year):**\n"
                    for r in best_rates[:5]:
                        rates_text += f"- {r['bank']}: {r['rate']}%\n"
                    context_parts.append(rates_text)
        
        # === COMPARISON REQUESTS ===
        if intent.primary_intent == IntentType.COMPARE_OPTIONS:
            if "sip" in user_message.lower() and "rd" in user_message.lower():
                amount = intent.entities.get("amount", 5000)
                years = intent.entities.get("duration_years", 10)
                comparison = compare_sip_vs_rd(amount, years)
                context_parts.append(f"Calculation context: {comparison['summary_hinglish']}")
                calculation_data = comparison
            
            # Bank comparison
            elif any(word in user_message.lower() for word in ["bank", "fd rate", "best rate"]):
                comparison = data_hub.get_all_bank_rates(12)
                context_parts.append(data_hub.format_bank_comparison_hinglish({
                    "tenure_months": 12,
                    "comparison": comparison[:5],
                    "best_bank": comparison[0] if comparison else None
                }))
        
        # === CALCULATION REQUESTS ===
        elif intent.primary_intent == IntentType.CALCULATE:
            amount = intent.entities.get("amount")
            years = intent.entities.get("duration_years")
            
            if amount and years:
                sip_result = calculate_sip(amount, years)
                rd_result = calculate_rd(amount, years)
                context_parts.append(
                    f"SIP Calculation: {sip_result.format_summary_hinglish()}\n"
                    f"For comparison - RD would give: Rs {rd_result.maturity_value:,.0f}"
                )
                calculation_data = sip_result.to_dict()
        
        # === GOAL PLANNING ===
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
                    # Get next interview question for this goal
                    next_q = goal_interview.get_next_question(session.session_id)
                    
                    context_parts.append(
                        f"User is planning for: {template.name_hinglish}. "
                        f"Typical timeline: {template.typical_timeline_years} years. "
                        f"Typical cost: Rs {template.typical_cost_range[0]}-{template.typical_cost_range[1]} lakhs. "
                    )
                    
                    if next_q:
                        context_parts.append(f"**Ask this question naturally:** {next_q[1]}")
                        goal_interview.mark_question_asked(session.session_id, next_q[0])
                    
                    # Update session goal
                    goal_type_map = {
                        "child_education": GoalType.CHILD_EDUCATION,
                        "daughter_wedding": GoalType.WEDDING,
                        "home_downpayment": GoalType.HOME_DOWNPAYMENT,
                        "retirement": GoalType.RETIREMENT,
                    }
                    if detected_goal in goal_type_map:
                        session.set_goal(goal_type_map[detected_goal])
        
        # === SCHEME INFO ===
        elif intent.primary_intent == IntentType.SCHEME_INFO:
            for scheme_code in ["ppf", "ssy", "nps", "pmjjby", "pmsby", "scss"]:
                if scheme_code in user_message.lower():
                    explanation = get_scheme_explanation_hinglish(scheme_code)
                    # Add current rate from data hub
                    scheme_rate = data_hub.get_scheme_rate(scheme_code)
                    if scheme_rate:
                        context_parts.append(
                            f"Scheme information: {explanation}\n"
                            f"**Current Rate:** {scheme_rate['rate']}% p.a. (as of {scheme_rate['updated']})"
                        )
                    else:
                        context_parts.append(f"Scheme information: {explanation}")
                    break
        
        # === SIP INFO ===
        elif intent.primary_intent == IntentType.SIP_INFO:
            context_parts.append(
                "User wants to know about SIP. Key points: "
                "SIP = Systematic Investment Plan in mutual funds. "
                "Can start with Rs 500/month. Rupee cost averaging benefit. "
                "Market-linked returns (historical avg ~10-12%). "
                "Good for long-term goals (5+ years)."
            )
        
        # === RD INFO ===
        elif intent.primary_intent == IntentType.RD_INFO:
            # Get actual RD rates from data hub
            best_rd_banks = ["hdfc", "sbi", "icici"]
            rd_rates = []
            for bank in best_rd_banks:
                info = data_hub.get_bank_info(bank)
                if info:
                    rd_rates.append(f"{info.name}: {info.rd_rate}%")
            
            context_parts.append(
                f"User wants to know about RD. Key points: "
                f"RD = Recurring Deposit in bank. "
                f"Current RD rates: {', '.join(rd_rates)}. "
                f"Government guarantee up to Rs 5 lakhs (DICGC). "
                f"Good for short-term goals or risk-averse users."
            )
        
        # === PROACTIVE QUESTION INJECTION ===
        # If profile is incomplete and we should ask a question
        if goal_interview.should_ask_question(session.session_id):
            next_q = goal_interview.get_next_question(session.session_id)
            if next_q and next_q[0] not in ["name"]:  # Don't force name question
                context_parts.append(
                    f"\n**Suggestion:** Naturally ask about {next_q[0]} to give better advice: '{next_q[1]}'"
                )
        
        context = "\n\n".join(context_parts) if context_parts else None
        return context, calculation_data
    
    def _detect_query_type(self, message: str, intent: IntentResult) -> Optional[str]:
        """Detect the type of financial query for data hub context."""
        message_lower = message.lower()
        
        if any(w in message_lower for w in ["fd", "fixed deposit", "bank rate"]):
            return "fd"
        elif any(w in message_lower for w in ["invest", "sip", "mutual fund", "stock"]):
            return "investment"
        elif any(w in message_lower for w in ["compare", "vs", "better", "difference"]):
            return "compare"
        elif any(w in message_lower for w in ["goal", "retire", "education", "wedding", "ghar"]):
            return "goal"
        elif any(w in message_lower for w in ["tax", "80c", "deduction"]):
            return "tax"
        
        return None
    
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
