"""
Safety and compliance layer for SamairaAI.
Detects advisory boundaries, triggers handoffs, and injects disclaimers.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pathlib import Path


class SafetyTriggerType(str, Enum):
    """Types of safety triggers."""
    ADVISORY_BOUNDARY = "advisory_boundary"
    TAX_ADVISORY = "tax_advisory"
    LEGAL_MATTER = "legal_matter"
    COMPLAINT = "complaint"
    HANDOFF_REQUEST = "handoff_request"
    HIGH_VALUE = "high_value"
    NONE = "none"


@dataclass
class SafetyCheckResult:
    """Result of a safety check on user input."""
    is_safe: bool
    trigger_type: SafetyTriggerType
    matched_pattern: Optional[str] = None
    suggested_response: Optional[str] = None
    should_handoff: bool = False


# Compiled regex patterns for efficiency
ADVISORY_PATTERNS = [
    r"kaunsa\s+fund",
    r"which\s+fund",
    r"best\s+(fund|mutual\s*fund|scheme)",
    r"recommend\s+karo",
    r"suggest\s+karo",
    r"konsa\s+scheme",
    r"exact\s+fund",
    r"specific\s+stock",
    r"kauns[ai]\s+share",
    r"stock\s+(pick|tip)",
    r"guarantee\s+return",
    r"pakka\s+return",
    r"sure\s+profit",
    r"fixed\s+return\s+guarantee",
]

TAX_PATTERNS = [
    r"tax\s+file\s+karo",
    r"itr\s+bhar",
    r"capital\s+gains?\s+calculate",
    r"huf\s+tax",
    r"nri\s+tax",
    r"tax\s+audit",
    r"gst\s+filing",
]

LEGAL_PATTERNS = [
    r"will\s+banan[ai]",
    r"estate\s+planning",
    r"property\s+dispute",
    r"legal\s+action",
    r"court\s+case",
    r"inheritance",
]

COMPLAINT_PATTERNS = [
    r"complaint",
    r"grievance",
    r"fraud\s+hua",
    r"scam",
    r"money\s+stuck",
    r"refund\s+chahiye",
    r"manager\s+se\s+baat",
    r"escalate",
]

HANDOFF_PATTERNS = [
    r"advisor\s+se\s+baat",
    r"human\s+se\s+connect",
    r"real\s+person",
    r"asli\s+aadmi",
    r"manager\s+chahiye",
    r"call\s+back",
    r"phone\s+karo",
]

HIGH_VALUE_PATTERNS = [
    r"\d+\s*crore",
    r"50\s*lakh",
    r"large\s+amount",
    r"bahut\s+paisa",
    r"life\s+savings",
    r"retirement\s+corpus\s+invest",
]


# Handoff response templates
HANDOFF_RESPONSES = {
    SafetyTriggerType.ADVISORY_BOUNDARY: (
        "{name} ji, specific fund ya scheme recommend karna mere scope mein nahi hai — "
        "yeh SEBI-registered advisor ka kaam hai. Main aapko concepts samjha sakti hoon, "
        "lekin final decision ke liye ek certified advisor se baat karna better rahega. "
        "Kya main aapko hamare advisor se connect karwa doon?"
    ),
    SafetyTriggerType.TAX_ADVISORY: (
        "{name} ji, tax filing aur detailed tax planning ke liye ek CA ya tax professional "
        "se consult karna chahiye. Main general tax-saving options samjha sakti hoon, "
        "lekin aapki specific situation ke liye expert advice zaroori hai. "
        "Kya aap hamare tax advisor se baat karna chahenge?"
    ),
    SafetyTriggerType.LEGAL_MATTER: (
        "{name} ji, yeh legal matter hai jisme mujhe help karna possible nahi hai. "
        "Iske liye aapko ek lawyer ya legal expert se consult karna chahiye. "
        "Kya main aapko kisi aur cheez mein help kar sakti hoon?"
    ),
    SafetyTriggerType.COMPLAINT: (
        "{name} ji, aapki complaint sunke dukh hua. Yeh matter humari customer support team "
        "better handle kar sakti hai. Main abhi aapko unse connect karwa deti hoon. "
        "Kya aap apna registered phone number confirm kar sakte hain?"
    ),
    SafetyTriggerType.HANDOFF_REQUEST: (
        "Zaroor {name} ji! Main aapko hamare financial advisor se connect karwa deti hoon. "
        "Woh aapki specific situation samajh kar better guidance de payenge. "
        "Kya aap apna preferred time bata sakte hain callback ke liye?"
    ),
    SafetyTriggerType.HIGH_VALUE: (
        "{name} ji, itni badi investment ke liye ek dedicated relationship manager se baat "
        "karna better rahega. Woh aapko personalized portfolio strategy bana kar de sakte hain. "
        "Kya main appointment schedule karwa doon?"
    ),
}

# Disclaimer templates
PROJECTION_DISCLAIMER = (
    "\n\n⚠️ *Yeh sirf ek illustration hai. Actual returns market conditions pe depend "
    "karte hain. Past performance future returns ki guarantee nahi hai. "
    "Yeh investment advice nahi hai.*"
)

CALCULATION_DISCLAIMER = (
    "\n\n📊 *Note: Yeh calculation approximate hai aur illustrative purpose ke liye hai. "
    "Actual returns vary ho sakte hain.*"
)


def _check_patterns(text: str, patterns: list[str]) -> Optional[str]:
    """Check text against a list of regex patterns. Returns matched pattern or None."""
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return pattern
    return None


def check_safety(user_input: str) -> SafetyCheckResult:
    """
    Check user input for safety triggers.
    Returns SafetyCheckResult with trigger type and suggested response.
    """
    text = user_input.lower().strip()
    
    # Check each category in order of severity
    
    # 1. Complaints (highest priority - user needs immediate help)
    if matched := _check_patterns(text, COMPLAINT_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            trigger_type=SafetyTriggerType.COMPLAINT,
            matched_pattern=matched,
            suggested_response=HANDOFF_RESPONSES[SafetyTriggerType.COMPLAINT],
            should_handoff=True
        )
    
    # 2. Explicit handoff requests
    if matched := _check_patterns(text, HANDOFF_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            trigger_type=SafetyTriggerType.HANDOFF_REQUEST,
            matched_pattern=matched,
            suggested_response=HANDOFF_RESPONSES[SafetyTriggerType.HANDOFF_REQUEST],
            should_handoff=True
        )
    
    # 3. Legal matters
    if matched := _check_patterns(text, LEGAL_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            trigger_type=SafetyTriggerType.LEGAL_MATTER,
            matched_pattern=matched,
            suggested_response=HANDOFF_RESPONSES[SafetyTriggerType.LEGAL_MATTER],
            should_handoff=True
        )
    
    # 4. High value investments
    if matched := _check_patterns(text, HIGH_VALUE_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            trigger_type=SafetyTriggerType.HIGH_VALUE,
            matched_pattern=matched,
            suggested_response=HANDOFF_RESPONSES[SafetyTriggerType.HIGH_VALUE],
            should_handoff=True
        )
    
    # 5. Tax advisory
    if matched := _check_patterns(text, TAX_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            trigger_type=SafetyTriggerType.TAX_ADVISORY,
            matched_pattern=matched,
            suggested_response=HANDOFF_RESPONSES[SafetyTriggerType.TAX_ADVISORY],
            should_handoff=True
        )
    
    # 6. Advisory boundary (specific recommendations)
    if matched := _check_patterns(text, ADVISORY_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            trigger_type=SafetyTriggerType.ADVISORY_BOUNDARY,
            matched_pattern=matched,
            suggested_response=HANDOFF_RESPONSES[SafetyTriggerType.ADVISORY_BOUNDARY],
            should_handoff=False  # Can still educate, just can't recommend
        )
    
    # All clear
    return SafetyCheckResult(
        is_safe=True,
        trigger_type=SafetyTriggerType.NONE
    )


def inject_disclaimer(response: str, has_projection: bool = False, has_calculation: bool = False) -> str:
    """
    Inject appropriate disclaimers into a response.
    
    Args:
        response: The AI response text
        has_projection: Whether response contains future projections
        has_calculation: Whether response contains financial calculations
    
    Returns:
        Response with disclaimers appended if needed
    """
    # Check if disclaimer already present
    if "illustration" in response.lower() or "⚠️" in response:
        return response
    
    if has_projection:
        return response + PROJECTION_DISCLAIMER
    elif has_calculation:
        return response + CALCULATION_DISCLAIMER
    
    return response


def detect_projection_in_response(response: str) -> bool:
    """Check if response contains financial projections that need disclaimer."""
    projection_indicators = [
        r"₹[\d,]+\s*(lakh|crore)",  # Amount projections
        r"\d+\s*%\s*(return|growth)",  # Return percentages
        r"after\s+\d+\s+years?",  # Future timeframes
        r"\d+\s+saal\s+(baad|mein)",  # Hindi future timeframes
        r"ban\s+(sakte|jayenge|sakta)",  # "will become" phrases
        r"ho\s+(sakte|jayenge|sakta)",  # "can be" phrases
        r"mil\s+(sakte|jayenge|sakta)",  # "can get" phrases
    ]
    
    response_lower = response.lower()
    for pattern in projection_indicators:
        if re.search(pattern, response_lower):
            return True
    return False


def detect_calculation_in_response(response: str) -> bool:
    """Check if response contains calculations that need disclaimer."""
    calculation_indicators = [
        r"₹[\d,]+",  # Any rupee amount
        r"\d+\s*%",  # Any percentage
        r"(calculate|calculation|formula)",
        r"(total|sum|corpus)",
    ]
    
    response_lower = response.lower()
    matches = 0
    for pattern in calculation_indicators:
        if re.search(pattern, response_lower):
            matches += 1
    
    # Need at least 2 indicators to consider it a calculation
    return matches >= 2


def format_handoff_response(trigger_type: SafetyTriggerType, user_name: Optional[str] = None) -> str:
    """Get formatted handoff response with user name."""
    name = user_name or "Aap"
    template = HANDOFF_RESPONSES.get(trigger_type, HANDOFF_RESPONSES[SafetyTriggerType.HANDOFF_REQUEST])
    return template.format(name=name)
