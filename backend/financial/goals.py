"""
Goal templates and planning utilities for SamairaAI.
Provides structured goal planning for common Indian financial goals.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class GoalCategory(str, Enum):
    """Categories of financial goals."""
    EDUCATION = "education"
    WEDDING = "wedding"
    HOME = "home"
    RETIREMENT = "retirement"
    EMERGENCY = "emergency"
    VEHICLE = "vehicle"
    TRAVEL = "travel"
    OTHER = "other"


@dataclass
class GoalTemplate:
    """Template for a common financial goal."""
    category: GoalCategory
    name: str
    name_hinglish: str
    typical_timeline_years: int
    typical_cost_range: tuple[float, float]  # Min, Max in lakhs
    inflation_rate: float  # Education, healthcare have higher inflation
    recommended_instruments: list[str]
    planning_questions: list[str]
    tips_hinglish: list[str]


# Goal Templates Database
GOAL_TEMPLATES = {
    "child_education": GoalTemplate(
        category=GoalCategory.EDUCATION,
        name="Child's Higher Education",
        name_hinglish="Bachhe ki Padhai",
        typical_timeline_years=15,
        typical_cost_range=(10, 50),  # ₹10L to ₹50L
        inflation_rate=10.0,  # Education inflation is higher
        recommended_instruments=["SIP (Equity)", "PPF", "SSY (for daughter)", "Child ULIP"],
        planning_questions=[
            "Bachhe ki abhi umar kitni hai?",
            "India mein padhana chahte hain ya abroad?",
            "Engineering/Medical/MBA — kya soch rahe hain?",
            "Koi existing savings hai iske liye?"
        ],
        tips_hinglish=[
            "Jaldi start karein — compound interest ka fayda milega",
            "Education inflation 10-12% hoti hai, normal inflation se zyada",
            "Equity exposure rakhein agar 10+ saal hain",
            "Tax-saving instruments use karein (PPF, SSY)"
        ]
    ),
    
    "daughter_wedding": GoalTemplate(
        category=GoalCategory.WEDDING,
        name="Daughter's Wedding",
        name_hinglish="Beti ki Shadi",
        typical_timeline_years=20,
        typical_cost_range=(5, 30),  # ₹5L to ₹30L
        inflation_rate=7.0,
        recommended_instruments=["SSY", "PPF", "Gold (SGB)", "SIP", "RD"],
        planning_questions=[
            "Beti ki abhi umar kitni hai?",
            "Approximately kitne budget mein wedding soch rahe hain?",
            "Gold savings bhi include karna chahte hain?"
        ],
        tips_hinglish=[
            "SSY best option hai beti ke liye — high returns + tax-free",
            "Gold ke liye Sovereign Gold Bonds consider karein",
            "Wedding costs mein 6-7% inflation factor karein",
            "Systematic approach se burden kam lagega"
        ]
    ),
    
    "home_downpayment": GoalTemplate(
        category=GoalCategory.HOME,
        name="Home Down Payment",
        name_hinglish="Ghar ka Down Payment",
        typical_timeline_years=5,
        typical_cost_range=(5, 25),  # ₹5L to ₹25L (20% of home cost)
        inflation_rate=8.0,  # Real estate inflation
        recommended_instruments=["SIP (Balanced)", "RD", "FD", "Debt Funds"],
        planning_questions=[
            "Kitne saal mein ghar lena chahte hain?",
            "Approximately kitne ka ghar soch rahe hain?",
            "Loan kitna lena comfortable hai?",
            "Location decide ho gaya hai?"
        ],
        tips_hinglish=[
            "20% down payment ready rakhein for better loan terms",
            "5 saal se kam time hai toh equity exposure kam rakhein",
            "Home loan EMI income ka 40% se zyada na ho",
            "Registration, stamp duty ke liye extra 7-10% rakhein"
        ]
    ),
    
    "retirement": GoalTemplate(
        category=GoalCategory.RETIREMENT,
        name="Retirement Corpus",
        name_hinglish="Retirement Planning",
        typical_timeline_years=25,
        typical_cost_range=(100, 500),  # ₹1Cr to ₹5Cr
        inflation_rate=6.0,
        recommended_instruments=["NPS", "PPF", "EPF", "SIP (Equity)", "ELSS"],
        planning_questions=[
            "Abhi aapki umar kitni hai?",
            "Kitne saal mein retire hona chahte hain?",
            "Monthly expenses approximately kitne hain?",
            "EPF/Pension koi hai current job mein?"
        ],
        tips_hinglish=[
            "25x annual expenses ka corpus target karein",
            "NPS mein extra ₹50K tax benefit milta hai",
            "Early start bahut zaroori hai — 10 saal ka delay 50% zyada savings maangta hai",
            "Healthcare costs separately plan karein"
        ]
    ),
    
    "emergency_fund": GoalTemplate(
        category=GoalCategory.EMERGENCY,
        name="Emergency Fund",
        name_hinglish="Emergency Fund",
        typical_timeline_years=2,
        typical_cost_range=(1, 5),  # ₹1L to ₹5L (3-6 months expenses)
        inflation_rate=0,  # Keep liquid, not for growth
        recommended_instruments=["Savings Account", "Liquid Funds", "FD (laddered)", "Sweep Account"],
        planning_questions=[
            "Monthly expenses approximately kitne hain?",
            "Abhi kitna emergency fund hai?",
            "Family mein kitne dependents hain?",
            "Health insurance hai?"
        ],
        tips_hinglish=[
            "6 months expenses ka fund sabse pehle banayein",
            "Yeh paisa growth ke liye nahi, safety ke liye hai",
            "Liquid fund better hai savings account se — zyada returns",
            "FD ladder banayein — 1 month, 3 month, 6 month"
        ]
    ),
    
    "car_purchase": GoalTemplate(
        category=GoalCategory.VEHICLE,
        name="Car Purchase",
        name_hinglish="Gaadi Khareedna",
        typical_timeline_years=3,
        typical_cost_range=(5, 20),  # ₹5L to ₹20L
        inflation_rate=5.0,
        recommended_instruments=["RD", "SIP (Hybrid)", "FD"],
        planning_questions=[
            "Kitne saal mein gaadi leni hai?",
            "New car ya used?",
            "Approximate budget kitna hai?",
            "Loan lena chahte hain ya full payment?"
        ],
        tips_hinglish=[
            "Car depreciating asset hai — avoid loan if possible",
            "30% down payment aim karein agar loan le rahe hain",
            "Insurance, maintenance, fuel monthly ₹5-10K extra",
            "Resale value bhi consider karein while choosing"
        ]
    ),
}


def get_goal_template(goal_type: str) -> Optional[GoalTemplate]:
    """Get goal template by type."""
    return GOAL_TEMPLATES.get(goal_type.lower())


def get_all_goal_templates() -> list[GoalTemplate]:
    """Get all available goal templates."""
    return list(GOAL_TEMPLATES.values())


def estimate_future_cost(
    current_cost_lakhs: float,
    years: int,
    inflation_rate: float
) -> float:
    """Estimate future cost considering inflation."""
    return current_cost_lakhs * ((1 + inflation_rate / 100) ** years)


def generate_goal_summary(
    goal_type: str,
    target_amount_lakhs: float,
    timeline_years: int,
    monthly_investment: float
) -> str:
    """Generate a Hinglish summary for a goal plan."""
    template = GOAL_TEMPLATES.get(goal_type.lower())
    
    if not template:
        goal_name = "Financial Goal"
    else:
        goal_name = template.name_hinglish
    
    # Calculate if monthly investment is sufficient
    # Using simple SIP formula with 12% return assumption
    from .calculators import calculate_sip
    projection = calculate_sip(monthly_investment, timeline_years, 12.0)
    projected_lakhs = projection.maturity_value / 100000
    
    gap = target_amount_lakhs - projected_lakhs
    is_sufficient = gap <= 0
    
    summary = f"""🎯 **{goal_name} Plan Summary**

**Target:** ₹{target_amount_lakhs:.1f} lakhs in {timeline_years} years
**Your Investment:** ₹{monthly_investment:,.0f}/month

**Projection** (assuming 12% returns):
→ Estimated corpus: ₹{projected_lakhs:.1f} lakhs

"""
    
    if is_sufficient:
        summary += f"✅ Bahut accha! Aapka plan on track hai. Target se ₹{abs(gap):.1f} lakhs extra bhi ban sakte hain."
    else:
        additional_needed = (gap * 100000) / (timeline_years * 12)  # Rough additional monthly
        summary += f"⚠️ Target se ₹{gap:.1f} lakhs ka gap hai. Monthly ₹{additional_needed:,.0f} extra invest karna padega."
    
    if template:
        summary += f"\n\n**Tips:**\n"
        for tip in template.tips_hinglish[:2]:
            summary += f"• {tip}\n"
    
    summary += "\n*Yeh projection illustrative hai. Actual returns vary ho sakte hain.*"
    
    return summary


def get_goal_planning_questions(goal_type: str) -> list[str]:
    """Get clarifying questions for a goal type."""
    template = GOAL_TEMPLATES.get(goal_type.lower())
    if template:
        return template.planning_questions
    return [
        "Approximately kitna amount chahiye?",
        "Kitne saal mein achieve karna hai?",
        "Monthly kitna invest kar sakte hain?"
    ]


def suggest_instruments_for_goal(goal_type: str, timeline_years: int) -> list[str]:
    """Suggest investment instruments based on goal and timeline."""
    template = GOAL_TEMPLATES.get(goal_type.lower())
    
    if template:
        base_instruments = template.recommended_instruments
    else:
        base_instruments = ["SIP", "PPF", "RD"]
    
    # Adjust based on timeline
    if timeline_years < 3:
        # Short term — low risk
        return ["RD", "FD", "Liquid Funds", "Short-term Debt Funds"]
    elif timeline_years < 7:
        # Medium term — moderate risk
        return ["Balanced/Hybrid Funds", "RD", "FD Ladder", "PPF"]
    else:
        # Long term — can take equity risk
        return base_instruments


def detect_goal_from_text(text: str) -> Optional[str]:
    """Detect goal type from user's Hinglish text."""
    text_lower = text.lower()
    
    # Education keywords
    if any(kw in text_lower for kw in ["padhai", "education", "college", "school", "bachhe", "bachha", "beta", "beti", "study"]):
        if any(kw in text_lower for kw in ["beti", "daughter", "ladki"]):
            return "child_education"  # Could be SSY eligible
        return "child_education"
    
    # Wedding keywords
    if any(kw in text_lower for kw in ["shadi", "shaadi", "wedding", "marriage", "vivah"]):
        return "daughter_wedding"
    
    # Home keywords
    if any(kw in text_lower for kw in ["ghar", "home", "house", "flat", "apartment", "property", "down payment"]):
        return "home_downpayment"
    
    # Retirement keywords
    if any(kw in text_lower for kw in ["retire", "retirement", "pension", "budhaapa", "old age"]):
        return "retirement"
    
    # Emergency keywords
    if any(kw in text_lower for kw in ["emergency", "backup", "rainy day", "safety"]):
        return "emergency_fund"
    
    # Vehicle keywords
    if any(kw in text_lower for kw in ["car", "gaadi", "bike", "vehicle", "scooty"]):
        return "car_purchase"
    
    return None
