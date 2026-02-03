"""
Intent detection for SamairaAI.
Identifies user intents from Hinglish text for routing and context.
"""

import re
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class IntentType(str, Enum):
    """Types of user intents."""
    # Greetings
    GREETING = "greeting"
    FAREWELL = "farewell"
    
    # Information seeking
    EXPLAIN_CONCEPT = "explain_concept"
    COMPARE_OPTIONS = "compare_options"
    CALCULATE = "calculate"
    
    # Goal planning
    GOAL_PLANNING = "goal_planning"
    GOAL_EDUCATION = "goal_education"
    GOAL_WEDDING = "goal_wedding"
    GOAL_HOME = "goal_home"
    GOAL_RETIREMENT = "goal_retirement"
    
    # Scheme/product info
    SCHEME_INFO = "scheme_info"
    SIP_INFO = "sip_info"
    RD_INFO = "rd_info"
    FD_INFO = "fd_info"
    TAX_INFO = "tax_info"
    
    # Actions
    START_SIP = "start_sip"
    STOP_SIP = "stop_sip"
    
    # Meta
    HELP = "help"
    UNCLEAR = "unclear"
    CHITCHAT = "chitchat"


@dataclass
class IntentResult:
    """Result of intent detection."""
    primary_intent: IntentType
    confidence: float  # 0.0 to 1.0
    entities: dict     # Extracted entities like amounts, years
    secondary_intents: list[IntentType]


# Intent patterns (Hinglish + English)
INTENT_PATTERNS = {
    IntentType.GREETING: [
        r"^(hi|hello|hey|namaste|namaskar|namasté)",
        r"(good\s*(morning|evening|afternoon))",
        r"^(haan|haa|ji)",
    ],
    
    IntentType.FAREWELL: [
        r"(bye|goodbye|alvida|phir milenge|dhanyawad|thanks)",
        r"(ok\s*bye|theek hai|chalo)",
    ],
    
    IntentType.EXPLAIN_CONCEPT: [
        r"(kya\s*(hota|hai|hain)|what\s*is)",
        r"(samjha|samjhao|explain|batao)",
        r"(meaning|matlab|definition)",
        r"(kaise\s*kaam\s*karta)",
    ],
    
    IntentType.COMPARE_OPTIONS: [
        r"(difference|farak|antar)",
        r"(vs|versus|ya|or\s*better)",
        r"(compare|comparison|tulna)",
        r"(kaun\s*sa\s*(better|accha)|which\s*is\s*better)",
    ],
    
    IntentType.CALCULATE: [
        r"(calculate|calculation|kitna\s*(banega|milega|hoga))",
        r"(agar|if)\s*.*\s*(toh|then)\s*(kitna|how\s*much)",
        r"(\d+)\s*(saal|year|month|mahine)",
    ],
    
    IntentType.GOAL_PLANNING: [
        r"(goal|target|planning|plan\s*karna)",
        r"(save|saving|bachana|bachat)",
        r"(future|bhavishya)\s*(ke\s*liye|for)",
    ],
    
    IntentType.GOAL_EDUCATION: [
        r"(bachh?e|bachh?on|beta|beti|son|daughter|child)",
        r"(padhai|education|study|school|college)",
        r"(engineering|medical|mba|abroad)",
    ],
    
    IntentType.GOAL_WEDDING: [
        r"(shadi|shaadi|wedding|marriage|vivah)",
        r"(beti\s*ki\s*shadi)",
    ],
    
    IntentType.GOAL_HOME: [
        r"(ghar|home|house|flat|apartment)",
        r"(down\s*payment|loan)",
        r"(property|real\s*estate)",
    ],
    
    IntentType.GOAL_RETIREMENT: [
        r"(retire|retirement|pension)",
        r"(budh?apa|old\s*age)",
    ],
    
    IntentType.SCHEME_INFO: [
        r"(ppf|nps|ssy|sukanya|pmjjby|pmsby|epf|scss)",
        r"(government\s*scheme|sarkari\s*yojana)",
    ],
    
    IntentType.SIP_INFO: [
        r"\bsip\b",
        r"(systematic\s*investment)",
        r"(mutual\s*fund\s*sip)",
    ],
    
    IntentType.RD_INFO: [
        r"\brd\b",
        r"(recurring\s*deposit)",
    ],
    
    IntentType.FD_INFO: [
        r"\bfd\b",
        r"(fixed\s*deposit)",
    ],
    
    IntentType.TAX_INFO: [
        r"(tax|80c|80d|deduction)",
        r"(old\s*regime|new\s*regime)",
        r"(tax\s*saving|tax\s*benefit)",
    ],
    
    IntentType.START_SIP: [
        r"(start|shuru|begin)\s*(sip|investing)",
        r"(sip\s*(start|shuru|karna))",
    ],
    
    IntentType.STOP_SIP: [
        r"(stop|band|rokna)\s*sip",
        r"(sip\s*(stop|band|rokni))",
    ],
    
    IntentType.HELP: [
        r"(help|madad|sahayata)",
        r"(kya\s*kar\s*sakte\s*ho)",
        r"(what\s*can\s*you\s*do)",
    ],
}

# Entity extraction patterns
ENTITY_PATTERNS = {
    "amount": [
        r"₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(lakh|lac|lakhs?|crore|crores?|k|thousand)?",
        r"(\d+(?:,\d+)*)\s*rupees?",
    ],
    "duration_years": [
        r"(\d+)\s*(saal|years?|yr)",
    ],
    "duration_months": [
        r"(\d+)\s*(mahine|months?|mo)",
    ],
    "percentage": [
        r"(\d+(?:\.\d+)?)\s*(%|percent|pratishat)",
    ],
    "age": [
        r"(\d+)\s*(saal|years?)\s*(ki|ka|ke|old)?\s*(umar|age)?",
        r"(umar|age)\s*(\d+)",
    ],
}


def detect_intent(text: str) -> IntentResult:
    """
    Detect user intent from text.
    
    Args:
        text: User's input text (Hinglish supported)
    
    Returns:
        IntentResult with primary intent, confidence, and entities
    """
    text_lower = text.lower().strip()
    
    # Track matches
    matches: dict[IntentType, int] = {}
    
    # Check each intent pattern
    for intent_type, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches[intent_type] = matches.get(intent_type, 0) + 1
    
    # Extract entities
    entities = extract_entities(text)
    
    # Determine primary intent
    if not matches:
        # Check if it's a calculation question based on entities
        if entities.get("amount") or entities.get("duration_years"):
            primary = IntentType.CALCULATE
            confidence = 0.6
        else:
            primary = IntentType.UNCLEAR
            confidence = 0.3
    else:
        # Sort by match count
        sorted_intents = sorted(matches.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_intents[0][0]
        
        # Calculate confidence based on match count and specificity
        max_matches = sorted_intents[0][1]
        confidence = min(0.5 + (max_matches * 0.15), 0.95)
    
    # Get secondary intents
    secondary = [
        intent for intent, count in matches.items()
        if intent != primary
    ][:3]  # Top 3 secondary
    
    return IntentResult(
        primary_intent=primary,
        confidence=confidence,
        entities=entities,
        secondary_intents=secondary
    )


def extract_entities(text: str) -> dict:
    """
    Extract entities (amounts, durations, etc.) from text.
    """
    entities = {}
    text_lower = text.lower()
    
    # Extract amounts
    for pattern in ENTITY_PATTERNS["amount"]:
        match = re.search(pattern, text_lower)
        if match:
            amount = float(match.group(1).replace(",", ""))
            unit = match.group(2) if len(match.groups()) > 1 else None
            
            # Convert to base amount
            if unit:
                unit = unit.lower()
                if unit in ["lakh", "lac", "lakhs"]:
                    amount *= 100000
                elif unit in ["crore", "crores"]:
                    amount *= 10000000
                elif unit in ["k", "thousand"]:
                    amount *= 1000
            
            entities["amount"] = amount
            break
    
    # Extract duration in years
    for pattern in ENTITY_PATTERNS["duration_years"]:
        match = re.search(pattern, text_lower)
        if match:
            entities["duration_years"] = int(match.group(1))
            break
    
    # Extract duration in months
    for pattern in ENTITY_PATTERNS["duration_months"]:
        match = re.search(pattern, text_lower)
        if match:
            entities["duration_months"] = int(match.group(1))
            break
    
    # Extract percentage
    for pattern in ENTITY_PATTERNS["percentage"]:
        match = re.search(pattern, text_lower)
        if match:
            entities["percentage"] = float(match.group(1))
            break
    
    # Extract age
    for pattern in ENTITY_PATTERNS["age"]:
        match = re.search(pattern, text_lower)
        if match:
            # Find the numeric group
            for group in match.groups():
                if group and group.isdigit():
                    entities["age"] = int(group)
                    break
            break
    
    return entities


def get_intent_description(intent: IntentType) -> str:
    """Get human-readable description of an intent."""
    descriptions = {
        IntentType.GREETING: "User is greeting",
        IntentType.FAREWELL: "User is saying goodbye",
        IntentType.EXPLAIN_CONCEPT: "User wants explanation of a concept",
        IntentType.COMPARE_OPTIONS: "User wants to compare options",
        IntentType.CALCULATE: "User wants a calculation",
        IntentType.GOAL_PLANNING: "User wants to plan for a financial goal",
        IntentType.GOAL_EDUCATION: "User wants to plan for education",
        IntentType.GOAL_WEDDING: "User wants to plan for wedding",
        IntentType.GOAL_HOME: "User wants to plan for home purchase",
        IntentType.GOAL_RETIREMENT: "User wants to plan for retirement",
        IntentType.SCHEME_INFO: "User wants information about govt schemes",
        IntentType.SIP_INFO: "User wants information about SIP",
        IntentType.RD_INFO: "User wants information about RD",
        IntentType.FD_INFO: "User wants information about FD",
        IntentType.TAX_INFO: "User wants tax-related information",
        IntentType.START_SIP: "User wants to start a SIP",
        IntentType.STOP_SIP: "User wants to stop a SIP",
        IntentType.HELP: "User needs help",
        IntentType.UNCLEAR: "Intent is unclear",
        IntentType.CHITCHAT: "General conversation",
    }
    return descriptions.get(intent, "Unknown intent")
