"""
Bank rates API endpoints for SamairaAI.
Provides endpoints to query bank FD/RD rates, compare banks, and get scheme details.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from services.data_hub import data_hub


router = APIRouter()


# Response Models
class FDRateResponse(BaseModel):
    """Response for FD rate query."""
    bank_name: str
    bank_code: str
    tenure_days: int
    tenure_label: str
    rate_general: float
    rate_senior: float
    last_updated: str


class BankInfoResponse(BaseModel):
    """Full bank information response."""
    name: str
    code: str
    type: str
    fd_rates: dict
    rd_rate: Optional[float]
    savings_rate: Optional[float]
    special_notes: str
    last_updated: str


class ComparisonResponse(BaseModel):
    """Bank comparison response."""
    tenure_days: int
    tenure_label: str
    banks: List[dict]
    best_for_general: dict
    best_for_senior: dict


class SchemeRatesResponse(BaseModel):
    """Government scheme rates response."""
    scheme: str
    full_name: str
    current_rate: float
    min_amount: int
    max_amount: Optional[int]
    lock_in_years: int
    tax_benefit: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/banks/list")
async def list_all_banks():
    """Get list of all banks with basic info."""
    from services.data_hub import BANK_DATA
    
    banks = []
    for code, bank in BANK_DATA.items():
        banks.append({
            "code": code,
            "name": bank.name,
            "name_hindi": bank.name_hindi,
            "type": bank.type,
            "savings_rate": bank.savings_rate,
            "rd_rate": bank.rd_rate,
            "has_fd": bool(bank.fd_rates),
            "features": bank.features,
            "website": bank.website
        })
    
    return {
        "success": True,
        "count": len(banks),
        "banks": sorted(banks, key=lambda x: x["name"])
    }


@router.get("/banks/{bank_code}/fd-rate")
async def get_bank_fd_rate_endpoint(
    bank_code: str,
    tenure_months: int = Query(12, description="Tenure in months (e.g., 12 for 1 year)")
):
    """Get FD rate for a specific bank and tenure."""
    rate = data_hub.get_bank_fd_rate(bank_code, tenure_months)
    
    if not rate:
        raise HTTPException(
            status_code=404, 
            detail=f"Bank '{bank_code}' not found or no rates available"
        )
    
    return {
        "success": True,
        "data": rate
    }


@router.get("/banks/compare")
async def compare_bank_rates(
    tenure_months: int = Query(12, description="Tenure in months"),
    bank_type: Optional[str] = Query(None, description="Filter by type: public, private, small_finance, post_office"),
    top_n: int = Query(5, description="Number of top banks to return")
):
    """Compare FD rates across banks for a specific tenure."""
    from services.data_hub import BANK_DATA
    
    all_rates = data_hub.get_all_bank_rates(tenure_months)
    
    # Filter by type if specified
    if bank_type:
        all_rates = [r for r in all_rates if r.get("bank_type") == bank_type]
    
    # Get top N
    comparison = all_rates[:top_n]
    
    # Find best rates
    best_general = max(comparison, key=lambda x: x["general_rate"]) if comparison else None
    best_senior = max(comparison, key=lambda x: x["senior_rate"]) if comparison else None
    
    return {
        "success": True,
        "tenure_months": tenure_months,
        "count": len(comparison),
        "banks": comparison,
        "best_for_general": best_general,
        "best_for_senior": best_senior
    }


@router.get("/banks/best-fd-rates")
async def get_best_fd_rates_endpoint(
    tenure_months: int = Query(12, description="Tenure in months"),
    is_senior: bool = Query(False, description="Senior citizen rates"),
    top_n: int = Query(5, description="Number of top banks")
):
    """Get the best FD rates across all banks."""
    best = data_hub.get_best_fd_rates(tenure_months, is_senior, top_n)
    
    return {
        "success": True,
        "tenure_months": tenure_months,
        "is_senior": is_senior,
        "best_rates": best
    }


@router.get("/banks/{bank_code}/details")
async def get_bank_details(bank_code: str):
    """Get full details for a specific bank."""
    bank = data_hub.get_bank_info(bank_code)
    
    if not bank:
        raise HTTPException(status_code=404, detail=f"Bank '{bank_code}' not found")
    
    # Convert FD rates to serializable format
    fd_rates_list = []
    for rate in bank.fd_rates:
        fd_rates_list.append({
            "tenure_months": rate.tenure_months,
            "general_rate": rate.general_rate,
            "senior_rate": rate.senior_citizen_rate,
            "min_amount": rate.min_amount,
            "last_updated": rate.last_updated
        })
    
    return {
        "success": True,
        "data": {
            "name": bank.name,
            "name_hindi": bank.name_hindi,
            "code": bank.code,
            "type": bank.type,
            "fd_rates": fd_rates_list,
            "rd_rate": bank.rd_rate,
            "savings_rate": bank.savings_rate,
            "features": bank.features,
            "website": bank.website
        }
    }


@router.get("/schemes/all-rates")
async def get_scheme_rates():
    """Get current rates for all government schemes."""
    return {
        "success": True,
        "schemes": data_hub.scheme_rates,
        "note": "Rates as of Q4 FY 2024-25. Updated quarterly."
    }


@router.get("/schemes/{scheme_code}")
async def get_scheme_details(scheme_code: str):
    """Get details for a specific scheme."""
    scheme = data_hub.scheme_rates.get(scheme_code.lower())
    
    if not scheme:
        available = list(data_hub.scheme_rates.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Scheme '{scheme_code}' not found. Available: {available}"
        )
    
    return {
        "success": True,
        "scheme": scheme_code.lower(),
        "data": scheme
    }


@router.get("/tax/slabs")
async def get_tax_slabs(
    regime: str = Query("new", description="Tax regime: new or old")
):
    """Get income tax slabs for specified regime."""
    slabs = data_hub.tax_slabs.get(regime)
    
    if not slabs:
        raise HTTPException(status_code=400, detail="Regime must be 'new' or 'old'")
    
    return {
        "success": True,
        "regime": regime,
        "fy": "2025-26",
        "slabs": slabs
    }


@router.get("/inflation")
async def get_inflation_data():
    """Get current inflation rates."""
    return {
        "success": True,
        "data": data_hub.inflation_data,
        "note": "Use education/medical inflation for specific goal planning"
    }


@router.post("/calculate/fd-maturity")
async def calculate_fd_maturity(
    principal: float = Query(..., description="Principal amount"),
    rate: float = Query(..., description="Interest rate (e.g., 7.0 for 7%)"),
    tenure_years: float = Query(..., description="Tenure in years"),
    compounding: str = Query("quarterly", description="Compounding: quarterly, monthly, annually")
):
    """Calculate FD maturity amount."""
    # Compounding periods per year
    n_map = {"quarterly": 4, "monthly": 12, "annually": 1}
    n = n_map.get(compounding, 4)
    
    # Compound interest formula: A = P(1 + r/n)^(nt)
    r = rate / 100
    t = tenure_years
    
    maturity = principal * ((1 + r/n) ** (n * t))
    interest_earned = maturity - principal
    
    return {
        "success": True,
        "principal": principal,
        "rate": rate,
        "tenure_years": tenure_years,
        "compounding": compounding,
        "maturity_amount": round(maturity, 2),
        "interest_earned": round(interest_earned, 2),
        "effective_rate": round((interest_earned / principal) * 100 / tenure_years, 2)
    }


@router.post("/calculate/sip")
async def calculate_sip_returns(
    monthly_sip: float = Query(..., description="Monthly SIP amount"),
    expected_return: float = Query(12.0, description="Expected annual return (%)"),
    years: int = Query(..., description="Investment period in years")
):
    """Calculate SIP returns with compound growth."""
    # Monthly rate
    r = expected_return / 100 / 12
    n = years * 12  # Total months
    
    # SIP Future Value: FV = P * [(1+r)^n - 1] / r * (1+r)
    if r > 0:
        fv = monthly_sip * (((1 + r) ** n - 1) / r) * (1 + r)
    else:
        fv = monthly_sip * n
    
    total_invested = monthly_sip * n
    wealth_gained = fv - total_invested
    
    return {
        "success": True,
        "monthly_sip": monthly_sip,
        "expected_return": expected_return,
        "years": years,
        "total_invested": round(total_invested, 2),
        "expected_corpus": round(fv, 2),
        "wealth_gained": round(wealth_gained, 2),
        "wealth_gain_ratio": round(wealth_gained / total_invested, 2)
    }


@router.post("/calculate/goal-corpus")
async def calculate_goal_corpus(
    current_cost: float = Query(..., description="Current cost of the goal"),
    years: int = Query(..., description="Years until goal"),
    inflation: float = Query(6.0, description="Expected inflation rate (%)")
):
    """Calculate future corpus needed for a goal considering inflation."""
    # Future Value with inflation
    future_cost = current_cost * ((1 + inflation/100) ** years)
    
    return {
        "success": True,
        "current_cost": current_cost,
        "years": years,
        "inflation_assumed": inflation,
        "future_cost": round(future_cost, 2),
        "note": f"After {years} years at {inflation}% inflation, you'll need Rs {round(future_cost/100000, 2)} lakhs"
    }
