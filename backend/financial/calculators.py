"""
Deterministic financial calculators for SamairaAI.
All calculations are illustrative and use hardcoded/configurable rates.
NO LLM involvement in math — pure deterministic logic.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class InvestmentType(str, Enum):
    """Types of investment vehicles."""
    SIP = "sip"              # Systematic Investment Plan (Mutual Funds)
    RD = "rd"                # Recurring Deposit
    FD = "fd"                # Fixed Deposit
    PPF = "ppf"              # Public Provident Fund
    SSY = "ssy"              # Sukanya Samriddhi Yojana
    NPS = "nps"              # National Pension System


# Default interest rates (as of 2024-2025)
# These should be configurable in production
DEFAULT_RATES = {
    InvestmentType.SIP: 12.0,    # Historical equity MF average
    InvestmentType.RD: 6.5,      # Bank RD average
    InvestmentType.FD: 7.0,      # Bank FD average
    InvestmentType.PPF: 7.1,     # Current PPF rate
    InvestmentType.SSY: 8.2,     # Current SSY rate
    InvestmentType.NPS: 10.0,    # NPS equity average
}


@dataclass
class ProjectionResult:
    """Result of a financial projection calculation."""
    investment_type: InvestmentType
    monthly_investment: float
    tenure_years: int
    rate_of_return: float
    total_invested: float
    maturity_value: float
    total_returns: float
    returns_percentage: float
    
    def to_dict(self) -> dict:
        return {
            "investment_type": self.investment_type.value,
            "monthly_investment": self.monthly_investment,
            "tenure_years": self.tenure_years,
            "rate_of_return": self.rate_of_return,
            "total_invested": round(self.total_invested, 2),
            "maturity_value": round(self.maturity_value, 2),
            "total_returns": round(self.total_returns, 2),
            "returns_percentage": round(self.returns_percentage, 2),
        }
    
    def format_summary_hinglish(self) -> str:
        """Format result in Hinglish for display."""
        invested_lakhs = self.total_invested / 100000
        maturity_lakhs = self.maturity_value / 100000
        returns_lakhs = self.total_returns / 100000
        
        return (
            f"📊 **{self.investment_type.value.upper()} Projection**\n"
            f"• Monthly investment: ₹{self.monthly_investment:,.0f}\n"
            f"• Tenure: {self.tenure_years} years\n"
            f"• Expected rate: {self.rate_of_return}% p.a.\n"
            f"• Total invested: ₹{invested_lakhs:.2f} lakhs\n"
            f"• Maturity value: ₹{maturity_lakhs:.2f} lakhs\n"
            f"• Total returns: ₹{returns_lakhs:.2f} lakhs ({self.returns_percentage:.1f}%)"
        )


def calculate_sip(
    monthly_amount: float,
    years: int,
    annual_rate: float = DEFAULT_RATES[InvestmentType.SIP]
) -> ProjectionResult:
    """
    Calculate SIP maturity value using compound interest formula.
    
    Formula: M = P × ({[1 + r]^n – 1} / r) × (1 + r)
    Where:
        M = Maturity amount
        P = Monthly investment
        r = Monthly rate of return (annual_rate / 12 / 100)
        n = Number of months (years × 12)
    """
    monthly_rate = annual_rate / 12 / 100
    months = years * 12
    
    # SIP Future Value formula
    if monthly_rate > 0:
        maturity = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    else:
        maturity = monthly_amount * months
    
    total_invested = monthly_amount * months
    total_returns = maturity - total_invested
    returns_pct = (total_returns / total_invested) * 100 if total_invested > 0 else 0
    
    return ProjectionResult(
        investment_type=InvestmentType.SIP,
        monthly_investment=monthly_amount,
        tenure_years=years,
        rate_of_return=annual_rate,
        total_invested=total_invested,
        maturity_value=maturity,
        total_returns=total_returns,
        returns_percentage=returns_pct
    )


def calculate_rd(
    monthly_amount: float,
    years: int,
    annual_rate: float = DEFAULT_RATES[InvestmentType.RD]
) -> ProjectionResult:
    """
    Calculate RD (Recurring Deposit) maturity value.
    RD compounds quarterly in most Indian banks.
    
    Formula: M = P * [(1 + r/n)^(n*t) - 1] / (1 - (1 + r/n)^(-1/3))
    Simplified for monthly deposits with quarterly compounding.
    """
    # Quarterly compounding
    quarters_per_year = 4
    quarterly_rate = annual_rate / 4 / 100
    total_quarters = years * quarters_per_year
    months = years * 12
    
    # Simplified RD calculation (monthly deposit, quarterly compound)
    maturity = 0
    for month in range(months):
        quarters_remaining = (months - month) / 3
        maturity += monthly_amount * ((1 + quarterly_rate) ** quarters_remaining)
    
    total_invested = monthly_amount * months
    total_returns = maturity - total_invested
    returns_pct = (total_returns / total_invested) * 100 if total_invested > 0 else 0
    
    return ProjectionResult(
        investment_type=InvestmentType.RD,
        monthly_investment=monthly_amount,
        tenure_years=years,
        rate_of_return=annual_rate,
        total_invested=total_invested,
        maturity_value=maturity,
        total_returns=total_returns,
        returns_percentage=returns_pct
    )


def calculate_fd(
    principal: float,
    years: int,
    annual_rate: float = DEFAULT_RATES[InvestmentType.FD],
    compounding: str = "quarterly"
) -> ProjectionResult:
    """
    Calculate FD (Fixed Deposit) maturity value.
    
    Formula: A = P(1 + r/n)^(nt)
    """
    compound_freq = {
        "monthly": 12,
        "quarterly": 4,
        "half-yearly": 2,
        "yearly": 1
    }
    n = compound_freq.get(compounding, 4)
    
    maturity = principal * ((1 + annual_rate / (100 * n)) ** (n * years))
    total_returns = maturity - principal
    returns_pct = (total_returns / principal) * 100 if principal > 0 else 0
    
    return ProjectionResult(
        investment_type=InvestmentType.FD,
        monthly_investment=0,  # FD is lump sum
        tenure_years=years,
        rate_of_return=annual_rate,
        total_invested=principal,
        maturity_value=maturity,
        total_returns=total_returns,
        returns_percentage=returns_pct
    )


def calculate_ppf(
    yearly_amount: float,
    years: int = 15,  # PPF has 15-year lock-in
    annual_rate: float = DEFAULT_RATES[InvestmentType.PPF]
) -> ProjectionResult:
    """
    Calculate PPF maturity value.
    PPF compounds annually, max 15 years initial term.
    """
    maturity = 0
    for year in range(years):
        years_to_mature = years - year
        maturity += yearly_amount * ((1 + annual_rate / 100) ** years_to_mature)
    
    total_invested = yearly_amount * years
    total_returns = maturity - total_invested
    returns_pct = (total_returns / total_invested) * 100 if total_invested > 0 else 0
    
    # Convert to monthly equivalent for consistency
    monthly_equivalent = yearly_amount / 12
    
    return ProjectionResult(
        investment_type=InvestmentType.PPF,
        monthly_investment=monthly_equivalent,
        tenure_years=years,
        rate_of_return=annual_rate,
        total_invested=total_invested,
        maturity_value=maturity,
        total_returns=total_returns,
        returns_percentage=returns_pct
    )


def calculate_ssy(
    yearly_amount: float,
    years: int = 21,  # SSY matures when girl turns 21
    annual_rate: float = DEFAULT_RATES[InvestmentType.SSY]
) -> ProjectionResult:
    """
    Calculate SSY (Sukanya Samriddhi Yojana) maturity.
    Deposits allowed for first 15 years, matures at 21 years from account opening.
    """
    deposit_years = min(years, 15)  # Can only deposit for 15 years
    
    maturity = 0
    for year in range(deposit_years):
        years_to_mature = years - year
        maturity += yearly_amount * ((1 + annual_rate / 100) ** years_to_mature)
    
    total_invested = yearly_amount * deposit_years
    total_returns = maturity - total_invested
    returns_pct = (total_returns / total_invested) * 100 if total_invested > 0 else 0
    
    monthly_equivalent = yearly_amount / 12
    
    return ProjectionResult(
        investment_type=InvestmentType.SSY,
        monthly_investment=monthly_equivalent,
        tenure_years=years,
        rate_of_return=annual_rate,
        total_invested=total_invested,
        maturity_value=maturity,
        total_returns=total_returns,
        returns_percentage=returns_pct
    )


def compare_sip_vs_rd(
    monthly_amount: float,
    years: int
) -> dict:
    """
    Compare SIP vs RD for same monthly investment.
    Returns comparison data for educational purposes.
    """
    sip_result = calculate_sip(monthly_amount, years)
    rd_result = calculate_rd(monthly_amount, years)
    
    difference = sip_result.maturity_value - rd_result.maturity_value
    difference_pct = (difference / rd_result.maturity_value) * 100 if rd_result.maturity_value > 0 else 0
    
    return {
        "sip": sip_result.to_dict(),
        "rd": rd_result.to_dict(),
        "difference": {
            "amount": round(difference, 2),
            "percentage": round(difference_pct, 2),
            "sip_advantage": difference > 0
        },
        "summary_hinglish": (
            f"₹{monthly_amount:,.0f}/month for {years} years:\n\n"
            f"**SIP** (expected ~{sip_result.rate_of_return}%): ₹{sip_result.maturity_value/100000:.2f} lakhs\n"
            f"**RD** (fixed ~{rd_result.rate_of_return}%): ₹{rd_result.maturity_value/100000:.2f} lakhs\n\n"
            f"Difference: ₹{abs(difference)/100000:.2f} lakhs "
            f"({'SIP' if difference > 0 else 'RD'} mein zyada)\n\n"
            f"*Note: SIP returns market pe depend karte hain, RD guaranteed hai but lower returns.*"
        )
    }


def calculate_goal_corpus(
    target_amount: float,
    years: int,
    expected_rate: float = 12.0
) -> dict:
    """
    Calculate required monthly investment to reach a goal.
    Reverse SIP calculation.
    """
    monthly_rate = expected_rate / 12 / 100
    months = years * 12
    
    # Required monthly investment formula (reverse of SIP)
    if monthly_rate > 0:
        required_monthly = target_amount / (
            (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        )
    else:
        required_monthly = target_amount / months
    
    total_investment = required_monthly * months
    
    return {
        "target_amount": target_amount,
        "years": years,
        "expected_rate": expected_rate,
        "required_monthly": round(required_monthly, 0),
        "total_investment": round(total_investment, 0),
        "summary_hinglish": (
            f"🎯 **Goal Planning**\n"
            f"• Target: ₹{target_amount/100000:.2f} lakhs\n"
            f"• Timeline: {years} years\n"
            f"• Assumed returns: {expected_rate}% p.a.\n"
            f"• Required monthly: ₹{required_monthly:,.0f}\n\n"
            f"*Agar aap har mahine ₹{required_monthly:,.0f} invest karte hain, "
            f"toh {years} saal mein approximately ₹{target_amount/100000:.2f} lakhs ban sakte hain.*"
        )
    }


def format_amount_indian(amount: float) -> str:
    """Format amount in Indian numbering system (lakhs/crores)."""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} crores"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} lakhs"
    else:
        return f"₹{amount:,.0f}"
