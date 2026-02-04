"""
Post-processing for LLM responses.
Strips re-introductions, enforces concise style, cleans output.
"""

import re
from typing import Optional


# Patterns that indicate the model is re-introducing itself
# These are applied repeatedly from the START of the text until no more matches
INTRO_PATTERNS = [
    # Greetings (must be at start)
    r'^Namaste!?\s*',
    r'^Hello!?\s*',
    r'^Hi!?\s*',
    r'^Hey!?\s*',
    r'^Namaskar!?\s*',
    # Self-introductions (at start after greeting stripped)
    r'^Main SamairaAI hoon[,.]?\s*',
    r'^Mera naam SamairaAI hai[,.]?\s*',
    r'^I am SamairaAI[,.]?\s*',
    r'^I\'m SamairaAI[,.]?\s*',
    r'^This is SamairaAI[,.]?\s*',
    # Role descriptions (at start) - with and without possessive
    r'^aapki? (personal\s+)?financial (advisor|assistant|companion|literacy companion)[,.]?\s*',
    r'^your (personal\s+)?financial (advisor|assistant|companion)[,.]?\s*',
    r'^I am your (personal\s+)?financial (advisor|assistant|companion)[,.]?\s*',
    r'^I\'m your (personal\s+)?financial (advisor|assistant|companion)[,.]?\s*',
    r'^Main aapki? (personal\s+)?financial (advisor|assistant|companion|literacy companion) hoon[,.]?\s*',
    # Purpose statements (at start)
    r'^Main aapki? financial needs samajhkar guidance provide karne ke liye (yahaan|yahan) hoon[,.]?\s*',
    r'^Main yahaan aapki madad karne ke liye hoon[,.]?\s*',
    r'^Main aapki? (samaJHkar|samajhkar)? guidance provide karne ke liye (yahaan|yahan) hoon[,.]?\s*',
    # Politeness (at start)
    r'^Kaise ho\??\s*',
    r'^Kaise hain\??\s*',
    r'^Aap kaise hain\??\s*',
    r'^Main aapki kaise madad kar sakti hoon\??\s*',
    r'^Main aapki kaise madad kar sakta hoon\??\s*',
    r'^Aapko kis tarah ki (financial\s+)?help chahiye\??\s*',
    r'^Kya aap (investment|savings|SIP|mutual fund|future planning)[^?]*\??\s*',
]

# Compiled patterns for performance
COMPILED_INTRO_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INTRO_PATTERNS]


def clean_response(text: str, turn_number: int = 1, for_voice: bool = False) -> str:
    """
    Clean an LLM response by removing re-introductions and enforcing style.
    
    Args:
        text: Raw LLM response
        turn_number: Current conversation turn (1 = first message, intro OK)
        for_voice: If True, also trim for voice output (shorter)
    
    Returns:
        Cleaned response text
    """
    if not text:
        return text
    
    cleaned = text.strip()
    
    # Only strip intros after turn 1
    if turn_number > 1:
        cleaned = _strip_introductions(cleaned)
    
    # Clean up any resulting issues
    cleaned = _clean_formatting(cleaned)
    
    # For voice, optionally trim long responses
    if for_voice:
        cleaned = _trim_for_voice(cleaned)
    
    return cleaned


def _strip_introductions(text: str) -> str:
    """Remove greeting/introduction patterns from start of text.
    
    Loops until no more patterns match, handling multi-part intros like:
    'Namaste! Main SamairaAI hoon, aapki financial advisor. Real content...'
    """
    result = text
    max_iterations = 10  # Safety limit
    
    for _ in range(max_iterations):
        previous = result
        
        # Apply all patterns (each pattern has ^ anchor, matches at start)
        for pattern in COMPILED_INTRO_PATTERNS:
            result = pattern.sub('', result)
        
        # Clean up leading whitespace/punctuation after each pass
        result = re.sub(r'^[\s,.:!;]+', '', result)
        
        # If no changes this iteration, we're done
        if result == previous:
            break
    
    # Capitalize first letter if it's now lowercase
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    
    return result if result else text  # Return original if nothing left


def _clean_formatting(text: str) -> str:
    """Fix common formatting issues."""
    # Remove multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Fix space before punctuation
    text = re.sub(r' ([,.!?])', r'\1', text)
    
    return text.strip()


def _trim_for_voice(text: str, max_sentences: int = 5) -> str:
    """
    Trim response for voice output.
    Keeps first few sentences to avoid overly long TTS.
    """
    # Split by sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    if len(sentences) <= max_sentences:
        return text
    
    # Keep first N sentences
    trimmed = ' '.join(sentences[:max_sentences])
    
    # Ensure it ends properly
    if not trimmed.endswith(('.', '!', '?')):
        trimmed += '.'
    
    return trimmed


def is_unclear_audio_response(text: str) -> bool:
    """Check if the text indicates unclear audio (from ASR)."""
    unclear_markers = [
        "[Audio unclear",
        "[Unclear audio",
        "Audio unclear",
        "please try again",
    ]
    text_lower = text.lower()
    return any(marker.lower() in text_lower for marker in unclear_markers)
