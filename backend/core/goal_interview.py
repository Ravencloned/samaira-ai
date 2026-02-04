"""
Goal Interview System for SamairaAI.
Implements proactive, structured goal-oriented conversations.
Captures user information through natural dialogue to provide personalized advice.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import json


class GoalCategory(str, Enum):
    """Categories of financial goals."""
    RETIREMENT = "retirement"
    CHILD_EDUCATION = "child_education"
    CHILD_WEDDING = "child_wedding"
    HOME_PURCHASE = "home_purchase"
    EMERGENCY_FUND = "emergency_fund"
    WEALTH_BUILDING = "wealth_building"
    CAR_PURCHASE = "car_purchase"
    TRAVEL = "travel"
    TAX_SAVING = "tax_saving"
    DEBT_PAYOFF = "debt_payoff"
    GENERAL_SAVINGS = "general_savings"


class InterviewPhase(str, Enum):
    """Phases of the goal interview."""
    INITIAL = "initial"              # Just starting
    GOAL_DISCOVERY = "goal_discovery"  # Understanding what they want
    PROFILE_BUILDING = "profile_building"  # Getting personal details
    FINANCIAL_ASSESSMENT = "financial_assessment"  # Understanding current finances
    RISK_PROFILING = "risk_profiling"  # Understanding risk appetite
    RECOMMENDATION = "recommendation"  # Providing advice
    FOLLOW_UP = "follow_up"          # Answering clarifications


@dataclass
class UserProfile:
    """User's financial profile built through interview."""
    # Personal
    name: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    city: Optional[str] = None
    
    # Family
    marital_status: Optional[str] = None
    num_children: int = 0
    children_ages: List[int] = field(default_factory=list)
    dependents: int = 0
    
    # Financial
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    monthly_savings: Optional[float] = None
    existing_investments: Dict[str, float] = field(default_factory=dict)
    existing_loans: Dict[str, float] = field(default_factory=dict)
    emergency_fund: Optional[float] = None
    
    # Banking
    primary_bank: Optional[str] = None
    has_demat: bool = False
    has_ppf: bool = False
    has_nps: bool = False
    
    # Goals
    primary_goal: Optional[GoalCategory] = None
    goal_amount: Optional[float] = None
    goal_timeline_years: Optional[int] = None
    
    # Risk
    risk_tolerance: Optional[str] = None  # conservative, moderate, aggressive
    investment_experience: Optional[str] = None  # none, beginner, intermediate, experienced
    
    def completion_percentage(self) -> float:
        """Calculate how complete the profile is."""
        required_fields = [
            self.age, self.monthly_income, self.monthly_savings,
            self.primary_goal, self.risk_tolerance
        ]
        filled = sum(1 for f in required_fields if f is not None)
        return (filled / len(required_fields)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "age": self.age,
            "occupation": self.occupation,
            "city": self.city,
            "marital_status": self.marital_status,
            "num_children": self.num_children,
            "children_ages": self.children_ages,
            "dependents": self.dependents,
            "monthly_income": self.monthly_income,
            "monthly_expenses": self.monthly_expenses,
            "monthly_savings": self.monthly_savings,
            "existing_investments": self.existing_investments,
            "existing_loans": self.existing_loans,
            "emergency_fund": self.emergency_fund,
            "primary_bank": self.primary_bank,
            "has_demat": self.has_demat,
            "has_ppf": self.has_ppf,
            "has_nps": self.has_nps,
            "primary_goal": self.primary_goal.value if self.primary_goal else None,
            "goal_amount": self.goal_amount,
            "goal_timeline_years": self.goal_timeline_years,
            "risk_tolerance": self.risk_tolerance,
            "investment_experience": self.investment_experience,
            "completion": self.completion_percentage()
        }


@dataclass
class InterviewState:
    """Current state of the goal interview."""
    session_id: str
    phase: InterviewPhase = InterviewPhase.INITIAL
    profile: UserProfile = field(default_factory=UserProfile)
    questions_asked: List[str] = field(default_factory=list)
    questions_pending: List[str] = field(default_factory=list)
    current_topic: Optional[str] = None
    context_gathered: Dict[str, Any] = field(default_factory=dict)
    recommendations_given: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


# Interview question templates by goal category
GOAL_QUESTIONS = {
    GoalCategory.RETIREMENT: [
        ("age", "Aapki abhi age kya hai? Retirement planning ke liye ye important hai."),
        ("retirement_age", "Aap kitne saal mein retire hona chahte hain?"),
        ("monthly_expenses", "Abhi aapka monthly kharcha approximately kitna hai?"),
        ("existing_investments", "Retirement ke liye kuch invest kiya hai? PPF, NPS, EPF?"),
        ("risk_tolerance", "Risk lena pasand hai ya safe investments chahiye?"),
    ],
    GoalCategory.CHILD_EDUCATION: [
        ("num_children", "Kitne bachche hain aapke?"),
        ("children_ages", "Bachche kitne saal ke hain?"),
        ("education_type", "India mein padhai ya abroad bhejna chahte hain?"),
        ("goal_timeline", "Kitne saal baad education shuru hogi?"),
        ("goal_amount", "Approximately kitna budget soch rahe hain education ke liye?"),
        ("existing_savings", "Education ke liye kuch save kiya hai already?"),
    ],
    GoalCategory.CHILD_WEDDING: [
        ("num_children", "Kitne bachche hain aapke?"),
        ("children_ages", "Bachche kitne saal ke hain?"),
        ("goal_timeline", "Approximately kitne saal baad shaadi plan kar rahe hain?"),
        ("goal_amount", "Shaadi ka budget kitna soch rahe hain?"),
        ("primary_bank", "Kaun sa bank use karte hain mainly?"),
    ],
    GoalCategory.HOME_PURCHASE: [
        ("city", "Kahan ghar lena chahte hain? Which city?"),
        ("home_budget", "Budget kitna hai ghar ke liye?"),
        ("down_payment", "Down payment ke liye kitna save hai?"),
        ("goal_timeline", "Kitne saal mein ghar lena chahte hain?"),
        ("monthly_income", "Monthly income kitni hai? EMI planning ke liye."),
    ],
    GoalCategory.EMERGENCY_FUND: [
        ("monthly_expenses", "Monthly kharcha kitna hai approximately?"),
        ("existing_savings", "Abhi emergency ke liye kitna save hai?"),
        ("job_stability", "Job stable hai ya kuch uncertainty hai?"),
        ("primary_bank", "Savings kahaan rakhte hain? Konsa bank?"),
    ],
    GoalCategory.TAX_SAVING: [
        ("monthly_income", "Annual income kitni hai approximately?"),
        ("existing_80c", "80C mein kya invest kiya hai? PPF, ELSS, LIC?"),
        ("has_nps", "NPS account hai? Extra 50,000 deduction mil sakta hai."),
        ("age", "Aapki age kya hai?"),
        ("risk_tolerance", "Tax saving ke saath returns bhi chahiye ya sirf safe raho?"),
    ],
}

# General profiling questions
PROFILE_QUESTIONS = [
    ("name", "Main aapko naam se bula sakti hoon? Aapka naam kya hai?"),
    ("age", "Aapki age kya hai?"),
    ("occupation", "Kya karte hain aap? Job ya business?"),
    ("monthly_income", "Monthly income kitni hai approximately?"),
    ("monthly_savings", "Har mahine kitna bacha paate hain?"),
    ("primary_bank", "Kaunsa bank mainly use karte hain?"),
    ("risk_tolerance", "Investments mein risk lena pasand hai ya safe rehna?"),
]

# Follow-up questions based on context
CONTEXTUAL_QUESTIONS = {
    "high_income_no_investment": "Income achhi hai, lekin investments ke baare mein batao - kuch kiya hai?",
    "has_children_no_education_plan": "Bachche hain, toh education planning ke baare mein socha hai?",
    "no_emergency_fund": "Emergency fund hai? 6 months expenses ka backup important hai.",
    "approaching_retirement": "Retirement planning ke baare mein kya status hai?",
    "high_loans": "Loans thode zyada hain, debt reduction plan banana chahiye?",
    "no_insurance": "Life insurance hai? Family ke liye important hai.",
    "no_health_insurance": "Health insurance ka kya scene hai? Medical emergencies ke liye zaruri hai.",
}


class GoalInterviewManager:
    """
    Manages goal-oriented interviews with users.
    Tracks state, generates contextual questions, and captures answers.
    """
    
    def __init__(self):
        self._sessions: Dict[str, InterviewState] = {}
    
    def get_or_create_state(self, session_id: str) -> InterviewState:
        """Get or create interview state for session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = InterviewState(session_id=session_id)
        return self._sessions[session_id]
    
    def detect_goal_from_message(self, message: str) -> Optional[GoalCategory]:
        """Detect financial goal from user message."""
        message_lower = message.lower()
        
        goal_keywords = {
            GoalCategory.RETIREMENT: ["retire", "pension", "budhapa", "old age", "retirement"],
            GoalCategory.CHILD_EDUCATION: ["education", "padhai", "college", "school", "beta ki padhai", "beti ki padhai", "bachche ki"],
            GoalCategory.CHILD_WEDDING: ["shaadi", "wedding", "marriage", "beta ki shaadi", "beti ki shaadi"],
            GoalCategory.HOME_PURCHASE: ["ghar", "house", "flat", "home", "property", "makan", "apartment"],
            GoalCategory.EMERGENCY_FUND: ["emergency", "rainy day", "backup", "contingency"],
            GoalCategory.WEALTH_BUILDING: ["wealth", "ameer", "rich", "grow money", "paisa badhao"],
            GoalCategory.CAR_PURCHASE: ["car", "gaadi", "vehicle"],
            GoalCategory.TRAVEL: ["travel", "vacation", "trip", "ghoomna"],
            GoalCategory.TAX_SAVING: ["tax", "80c", "tax saving", "tax bachao"],
            GoalCategory.DEBT_PAYOFF: ["loan", "debt", "karz", "emi"],
        }
        
        for goal, keywords in goal_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return goal
        
        return None
    
    def extract_info_from_message(self, message: str, state: InterviewState) -> Dict[str, Any]:
        """Extract profile information from user message."""
        import re
        extracted = {}
        message_lower = message.lower()
        
        # Age extraction
        age_match = re.search(r'(\d{1,2})\s*(?:saal|years?|yrs?|ki umar)', message_lower)
        if age_match:
            age = int(age_match.group(1))
            if 18 <= age <= 80:
                extracted["age"] = age
                state.profile.age = age
        
        # Name extraction
        name_patterns = [
            r'(?:my name is|mera naam|i am|main)\s+([A-Z][a-z]+)',
            r'(?:call me|mujhe bolo)\s+([A-Z][a-z]+)',
            r'^([A-Z][a-z]+)$'
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, message, re.IGNORECASE)
            if name_match:
                extracted["name"] = name_match.group(1).title()
                state.profile.name = extracted["name"]
                break
        
        # Income extraction
        income_patterns = [
            r'(?:income|salary|kamaai|kamata|kamati)\s*(?:hai|is)?\s*(?:₹|rs\.?|rupees?)?\s*([\d,]+)',
            r'([\d,]+)\s*(?:₹|rs\.?|rupees?)\s*(?:per month|monthly|mahine)',
            r'([\d,]+)\s*(?:lakh|lac)\s*(?:per|p\.?a\.?|yearly|saal)',
        ]
        for pattern in income_patterns:
            income_match = re.search(pattern, message_lower)
            if income_match:
                income_str = income_match.group(1).replace(',', '')
                income = float(income_str)
                if 'lakh' in message_lower or 'lac' in message_lower:
                    income *= 100000 / 12  # Convert annual lakhs to monthly
                extracted["monthly_income"] = income
                state.profile.monthly_income = income
                break
        
        # Savings extraction
        savings_patterns = [
            r'(?:save|bachat|bachata|bachati)\s*(?:karta|karti|kar sakta)?\s*(?:₹|rs\.?|rupees?)?\s*([\d,]+)',
            r'([\d,]+)\s*(?:₹|rs\.?|rupees?)?\s*(?:save|bachat)',
        ]
        for pattern in savings_patterns:
            savings_match = re.search(pattern, message_lower)
            if savings_match:
                savings_str = savings_match.group(1).replace(',', '')
                extracted["monthly_savings"] = float(savings_str)
                state.profile.monthly_savings = float(savings_str)
                break
        
        # Children extraction
        children_match = re.search(r'(\d)\s*(?:bachche|bachcha|kids?|children|beta|beti)', message_lower)
        if children_match:
            extracted["num_children"] = int(children_match.group(1))
            state.profile.num_children = int(children_match.group(1))
        
        # Bank extraction
        bank_keywords = {
            "sbi": ["sbi", "state bank"],
            "hdfc": ["hdfc"],
            "icici": ["icici"],
            "axis": ["axis"],
            "kotak": ["kotak"],
            "pnb": ["pnb", "punjab national"],
            "bob": ["bob", "bank of baroda", "baroda"],
            "post_office": ["post office", "india post"],
            "idfc": ["idfc"],
            "yes": ["yes bank"],
        }
        for bank_code, keywords in bank_keywords.items():
            if any(kw in message_lower for kw in keywords):
                extracted["primary_bank"] = bank_code
                state.profile.primary_bank = bank_code
                break
        
        # Risk tolerance extraction
        if any(w in message_lower for w in ["safe", "surakshit", "guaranteed", "risk nahi", "kam risk"]):
            extracted["risk_tolerance"] = "conservative"
            state.profile.risk_tolerance = "conservative"
        elif any(w in message_lower for w in ["moderate", "thoda risk", "balanced"]):
            extracted["risk_tolerance"] = "moderate"
            state.profile.risk_tolerance = "moderate"
        elif any(w in message_lower for w in ["aggressive", "high risk", "zyada risk", "risk le sakta"]):
            extracted["risk_tolerance"] = "aggressive"
            state.profile.risk_tolerance = "aggressive"
        
        # Goal amount extraction
        amount_match = re.search(r'([\d,]+)\s*(?:lakh|lac|crore)', message_lower)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            if 'crore' in message_lower:
                amount *= 10000000
            else:
                amount *= 100000
            extracted["goal_amount"] = amount
            state.profile.goal_amount = amount
        
        # Timeline extraction
        timeline_match = re.search(r'(\d{1,2})\s*(?:saal|years?|yrs?)\s*(?:mein|baad|me|later)?', message_lower)
        if timeline_match:
            extracted["goal_timeline_years"] = int(timeline_match.group(1))
            state.profile.goal_timeline_years = int(timeline_match.group(1))
        
        return extracted
    
    def get_next_question(self, session_id: str) -> Optional[Tuple[str, str]]:
        """
        Get the next relevant question to ask.
        Returns tuple of (question_key, question_text) or None if complete.
        """
        state = self.get_or_create_state(session_id)
        profile = state.profile
        
        # If goal is set, prioritize goal-specific questions
        if profile.primary_goal and profile.primary_goal in GOAL_QUESTIONS:
            goal_qs = GOAL_QUESTIONS[profile.primary_goal]
            for key, question in goal_qs:
                if key not in state.questions_asked:
                    # Check if we already have this info
                    if not self._has_info(profile, key):
                        return (key, question)
        
        # Otherwise, use general profiling questions
        for key, question in PROFILE_QUESTIONS:
            if key not in state.questions_asked:
                if not self._has_info(profile, key):
                    return (key, question)
        
        # Check for contextual questions
        contextual = self._get_contextual_question(profile)
        if contextual:
            return contextual
        
        return None
    
    def _has_info(self, profile: UserProfile, key: str) -> bool:
        """Check if we already have certain information."""
        info_map = {
            "name": profile.name,
            "age": profile.age,
            "occupation": profile.occupation,
            "monthly_income": profile.monthly_income,
            "monthly_savings": profile.monthly_savings,
            "monthly_expenses": profile.monthly_expenses,
            "primary_bank": profile.primary_bank,
            "risk_tolerance": profile.risk_tolerance,
            "num_children": profile.num_children if profile.num_children > 0 else None,
            "children_ages": profile.children_ages if profile.children_ages else None,
            "goal_amount": profile.goal_amount,
            "goal_timeline": profile.goal_timeline_years,
            "retirement_age": None,  # Special handling
            "existing_investments": profile.existing_investments if profile.existing_investments else None,
            "existing_savings": profile.emergency_fund,
        }
        return info_map.get(key) is not None
    
    def _get_contextual_question(self, profile: UserProfile) -> Optional[Tuple[str, str]]:
        """Get contextual follow-up question based on profile."""
        # High income but no investment info
        if profile.monthly_income and profile.monthly_income > 50000 and not profile.existing_investments:
            return ("existing_investments", CONTEXTUAL_QUESTIONS["high_income_no_investment"])
        
        # Has children but no education plan
        if profile.num_children > 0 and profile.primary_goal != GoalCategory.CHILD_EDUCATION:
            return ("education_plan", CONTEXTUAL_QUESTIONS["has_children_no_education_plan"])
        
        # No emergency fund mentioned
        if profile.monthly_income and not profile.emergency_fund:
            return ("emergency_fund", CONTEXTUAL_QUESTIONS["no_emergency_fund"])
        
        return None
    
    def mark_question_asked(self, session_id: str, question_key: str):
        """Mark a question as asked."""
        state = self.get_or_create_state(session_id)
        if question_key not in state.questions_asked:
            state.questions_asked.append(question_key)
        state.last_updated = datetime.now()
    
    def set_goal(self, session_id: str, goal: GoalCategory):
        """Set the primary goal for the session."""
        state = self.get_or_create_state(session_id)
        state.profile.primary_goal = goal
        state.phase = InterviewPhase.GOAL_DISCOVERY
        state.last_updated = datetime.now()
    
    def update_phase(self, session_id: str, phase: InterviewPhase):
        """Update the interview phase."""
        state = self.get_or_create_state(session_id)
        state.phase = phase
        state.last_updated = datetime.now()
    
    def get_profile_summary(self, session_id: str) -> str:
        """Get a summary of the user profile for LLM context."""
        state = self.get_or_create_state(session_id)
        profile = state.profile
        
        parts = []
        
        if profile.name:
            parts.append(f"Name: {profile.name}")
        if profile.age:
            parts.append(f"Age: {profile.age} years")
        if profile.occupation:
            parts.append(f"Occupation: {profile.occupation}")
        if profile.monthly_income:
            parts.append(f"Monthly Income: Rs {profile.monthly_income:,.0f}")
        if profile.monthly_savings:
            parts.append(f"Monthly Savings: Rs {profile.monthly_savings:,.0f}")
        if profile.num_children:
            parts.append(f"Children: {profile.num_children}")
        if profile.primary_bank:
            parts.append(f"Primary Bank: {profile.primary_bank.upper()}")
        if profile.risk_tolerance:
            parts.append(f"Risk Tolerance: {profile.risk_tolerance}")
        if profile.primary_goal:
            parts.append(f"Primary Goal: {profile.primary_goal.value.replace('_', ' ').title()}")
        if profile.goal_amount:
            parts.append(f"Goal Amount: Rs {profile.goal_amount:,.0f}")
        if profile.goal_timeline_years:
            parts.append(f"Timeline: {profile.goal_timeline_years} years")
        
        if not parts:
            return "No profile information collected yet."
        
        return "**User Profile:**\n" + "\n".join(f"- {p}" for p in parts)
    
    def get_interview_context(self, session_id: str) -> str:
        """
        Get complete interview context for LLM injection.
        Includes profile, pending questions, and conversation guidance.
        """
        state = self.get_or_create_state(session_id)
        profile = state.profile
        
        context_parts = []
        
        # Profile summary
        profile_summary = self.get_profile_summary(session_id)
        if profile_summary:
            context_parts.append(profile_summary)
        
        # Current phase guidance
        phase_guidance = {
            InterviewPhase.INITIAL: "User just started. Be warm, introduce yourself, and understand their goal.",
            InterviewPhase.GOAL_DISCOVERY: "Focus on understanding their financial goal in detail.",
            InterviewPhase.PROFILE_BUILDING: "Gather personal details needed for personalized advice.",
            InterviewPhase.FINANCIAL_ASSESSMENT: "Understand their current financial situation.",
            InterviewPhase.RISK_PROFILING: "Assess their risk tolerance and investment experience.",
            InterviewPhase.RECOMMENDATION: "Provide specific, actionable recommendations based on their profile.",
            InterviewPhase.FOLLOW_UP: "Answer their questions and clarify recommendations.",
        }
        context_parts.append(f"\n**Current Phase:** {phase_guidance.get(state.phase, 'General conversation')}")
        
        # Next question to ask (if any)
        next_q = self.get_next_question(session_id)
        if next_q:
            context_parts.append(f"\n**Suggested Question:** Ask about {next_q[0]}: '{next_q[1]}'")
        
        # Profile completion
        completion = profile.completion_percentage()
        if completion < 100:
            context_parts.append(f"\n**Profile Completion:** {completion:.0f}% - Need more info for personalized advice.")
        else:
            context_parts.append(f"\n**Profile Complete:** Ready to give detailed recommendations.")
        
        return "\n".join(context_parts)
    
    def should_ask_question(self, session_id: str) -> bool:
        """Check if we should ask a proactive question."""
        state = self.get_or_create_state(session_id)
        
        # Don't ask too many questions in a row
        if len(state.questions_asked) > 0 and len(state.questions_asked) % 3 == 0:
            return False
        
        # Check if there are pending questions
        return self.get_next_question(session_id) is not None


# Global instance
goal_interview = GoalInterviewManager()
