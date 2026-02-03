"""
Government schemes data and information for SamairaAI.
Educational information only — not investment advice.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GovernmentScheme:
    """Government savings/investment scheme information."""
    code: str
    name: str
    name_hindi: str
    description: str
    description_hinglish: str
    current_rate: float
    min_investment: float
    max_investment: float
    lock_in_years: Optional[int]
    tax_benefit: str
    risk_level: str
    suitable_for: list[str]
    key_features: list[str]


# Government Schemes Database
SCHEMES = {
    "ppf": GovernmentScheme(
        code="ppf",
        name="Public Provident Fund",
        name_hindi="पब्लिक प्रोविडेंट फंड",
        description="Long-term savings scheme backed by Government of India with tax benefits.",
        description_hinglish="Yeh government-backed scheme hai jisme 15 saal ke liye invest karte hain. Safe hai aur tax benefit bhi milta hai.",
        current_rate=7.1,
        min_investment=500,
        max_investment=150000,  # Per year
        lock_in_years=15,
        tax_benefit="Section 80C (up to ₹1.5 lakhs), Interest tax-free, Maturity tax-free (EEE)",
        risk_level="Very Low (Government Guaranteed)",
        suitable_for=["Long-term savings", "Retirement planning", "Risk-averse investors", "Tax saving"],
        key_features=[
            "15 saal ka lock-in period",
            "Yearly ₹500 se ₹1.5 lakh tak invest kar sakte hain",
            "Interest rate government decide karti hai (currently 7.1%)",
            "Loan facility available after 3rd year",
            "Partial withdrawal after 7th year",
            "EEE tax benefit - invest, interest, maturity sab tax-free"
        ]
    ),
    
    "ssy": GovernmentScheme(
        code="ssy",
        name="Sukanya Samriddhi Yojana",
        name_hindi="सुकन्या समृद्धि योजना",
        description="Savings scheme for girl child with high interest rate and tax benefits.",
        description_hinglish="Beti ke liye special scheme hai. PPF se zyada interest milta hai aur tax benefit bhi hai.",
        current_rate=8.2,
        min_investment=250,
        max_investment=150000,  # Per year
        lock_in_years=21,  # From account opening
        tax_benefit="Section 80C (up to ₹1.5 lakhs), Interest tax-free, Maturity tax-free (EEE)",
        risk_level="Very Low (Government Guaranteed)",
        suitable_for=["Daughter's education", "Daughter's marriage", "Girl child savings"],
        key_features=[
            "Sirf 10 saal se kam umar ki beti ke liye",
            "Account beti ke 21 saal ki hone tak chalta hai",
            "Deposit sirf first 15 years mein kar sakte hain",
            "50% withdrawal allowed for education after 18 years",
            "Highest interest among small savings schemes",
            "Account transfer possible across India"
        ]
    ),
    
    "nps": GovernmentScheme(
        code="nps",
        name="National Pension System",
        name_hindi="नेशनल पेंशन सिस्टम",
        description="Pension scheme with market-linked returns for retirement planning.",
        description_hinglish="Retirement ke liye pension scheme hai. Thoda risk hai kyunki market-linked hai, lekin returns bhi zyada ho sakte hain.",
        current_rate=10.0,  # Approximate, varies by fund choice
        min_investment=500,  # Per contribution
        max_investment=0,  # No upper limit
        lock_in_years=None,  # Till age 60
        tax_benefit="Section 80CCD(1) up to ₹1.5L + Additional 80CCD(1B) up to ₹50K",
        risk_level="Moderate (Market-linked)",
        suitable_for=["Retirement planning", "Long-term wealth creation", "Additional tax saving"],
        key_features=[
            "60 saal tak locked rehta hai",
            "Equity, Corporate Bonds, Government Securities mein invest hota hai",
            "Extra ₹50,000 tax deduction under 80CCD(1B)",
            "At 60: 60% lump sum (tax-free) + 40% annuity (pension)",
            "Low expense ratio compared to mutual funds",
            "Tier I (locked) and Tier II (flexible) accounts"
        ]
    ),
    
    "pmjjby": GovernmentScheme(
        code="pmjjby",
        name="Pradhan Mantri Jeevan Jyoti Bima Yojana",
        name_hindi="प्रधानमंत्री जीवन ज्योति बीमा योजना",
        description="Low-cost life insurance scheme for all Indians.",
        description_hinglish="Sirf ₹436/year mein ₹2 lakh ka life insurance. Bahut affordable scheme hai.",
        current_rate=0,  # Insurance, not investment
        min_investment=436,  # Annual premium
        max_investment=436,
        lock_in_years=1,  # Renewable yearly
        tax_benefit="Section 80C applicable on premium",
        risk_level="Not Applicable (Insurance)",
        suitable_for=["Basic life cover", "Low-income families", "First-time insurance"],
        key_features=[
            "₹2 lakh ka life cover",
            "Sirf ₹436 per year premium (₹1.20/day)",
            "Age 18-55 ke beech enroll kar sakte hain",
            "Cover 55 saal tak available",
            "Bank account se auto-debit hota hai",
            "Death claim nominee ko milta hai"
        ]
    ),
    
    "pmsby": GovernmentScheme(
        code="pmsby",
        name="Pradhan Mantri Suraksha Bima Yojana",
        name_hindi="प्रधानमंत्री सुरक्षा बीमा योजना",
        description="Low-cost accidental insurance scheme.",
        description_hinglish="Sirf ₹20/year mein accidental death aur disability cover. India ki sabse sasti insurance.",
        current_rate=0,  # Insurance
        min_investment=20,
        max_investment=20,
        lock_in_years=1,
        tax_benefit="Section 80C applicable on premium",
        risk_level="Not Applicable (Insurance)",
        suitable_for=["Accidental cover", "Everyone with bank account", "Budget insurance"],
        key_features=[
            "₹2 lakh accidental death cover",
            "₹2 lakh for total permanent disability",
            "₹1 lakh for partial permanent disability",
            "Sirf ₹20 per year (less than ₹2/month)",
            "Age 18-70 ke liye available",
            "Auto-renewal facility"
        ]
    ),
    
    "scss": GovernmentScheme(
        code="scss",
        name="Senior Citizens Savings Scheme",
        name_hindi="वरिष्ठ नागरिक बचत योजना",
        description="High-interest savings scheme for senior citizens.",
        description_hinglish="60+ age waalon ke liye special scheme. Regular income milti hai quarterly.",
        current_rate=8.2,
        min_investment=1000,
        max_investment=3000000,  # ₹30 lakhs
        lock_in_years=5,
        tax_benefit="Section 80C on investment, Interest taxable but TDS threshold ₹50K",
        risk_level="Very Low (Government Guaranteed)",
        suitable_for=["Retirees", "Senior citizens", "Regular income needs"],
        key_features=[
            "60 saal se upar ke liye",
            "Quarterly interest payout",
            "Maximum ₹30 lakhs invest kar sakte hain",
            "5 saal lock-in, 3 saal extension possible",
            "Premature closure with penalty allowed",
            "Joint account with spouse allowed"
        ]
    ),
}


def get_scheme_info(scheme_code: str) -> Optional[GovernmentScheme]:
    """Get scheme details by code."""
    return SCHEMES.get(scheme_code.lower())


def get_all_schemes() -> list[GovernmentScheme]:
    """Get all available schemes."""
    return list(SCHEMES.values())


def get_schemes_for_goal(goal_type: str) -> list[GovernmentScheme]:
    """Get schemes suitable for a specific goal."""
    goal_mapping = {
        "child_education": ["ssy", "ppf", "nps"],
        "daughter_education": ["ssy", "ppf"],
        "wedding": ["ssy", "ppf"],
        "retirement": ["nps", "ppf", "scss"],
        "tax_saving": ["ppf", "nps", "ssy"],
        "life_insurance": ["pmjjby"],
        "accident_insurance": ["pmsby"],
    }
    
    scheme_codes = goal_mapping.get(goal_type.lower(), ["ppf", "nps"])
    return [SCHEMES[code] for code in scheme_codes if code in SCHEMES]


def format_scheme_comparison(scheme_codes: list[str]) -> str:
    """Format a comparison of multiple schemes in Hinglish."""
    schemes = [SCHEMES[code] for code in scheme_codes if code in SCHEMES]
    
    if not schemes:
        return "Koi matching scheme nahi mili."
    
    lines = ["📋 **Government Schemes Comparison**\n"]
    
    for scheme in schemes:
        lines.append(f"**{scheme.name}** ({scheme.name_hindi})")
        lines.append(f"• Interest Rate: {scheme.current_rate}% p.a." if scheme.current_rate > 0 else "• Premium-based (Insurance)")
        lines.append(f"• Lock-in: {scheme.lock_in_years} years" if scheme.lock_in_years else "• Lock-in: Till 60 years")
        lines.append(f"• Risk: {scheme.risk_level}")
        lines.append(f"• Tax: {scheme.tax_benefit[:50]}...")
        lines.append("")
    
    lines.append("*Yeh general information hai. Investment se pehle scheme details zaroor padh lein.*")
    
    return "\n".join(lines)


def get_scheme_explanation_hinglish(scheme_code: str) -> str:
    """Get a Hinglish explanation of a scheme."""
    scheme = SCHEMES.get(scheme_code.lower())
    
    if not scheme:
        return "Yeh scheme mere database mein nahi hai."
    
    features = "\n".join([f"  • {f}" for f in scheme.key_features[:4]])
    
    return f"""**{scheme.name}** ({scheme.name_hindi})

{scheme.description_hinglish}

**Key Features:**
{features}

**Returns:** {scheme.current_rate}% p.a. (current rate)
**Risk Level:** {scheme.risk_level}
**Tax Benefit:** {scheme.tax_benefit}

*Yeh information educational purpose ke liye hai. Scheme rules change ho sakte hain.*"""
