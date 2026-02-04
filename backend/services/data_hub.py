"""
Financial Data Hub for SamairaAI.
Centralized source for bank rates, scheme rates, tax slabs, and market data.
All data is curated and updated periodically with source citations.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from pathlib import Path


@dataclass
class BankFDRate:
    """Fixed Deposit rate for a specific bank and tenure."""
    bank_code: str
    bank_name: str
    tenure_months: int
    general_rate: float
    senior_citizen_rate: float
    min_amount: float
    max_amount: Optional[float]
    last_updated: str
    source_url: str


@dataclass  
class BankInfo:
    """Bank information with all FD rates."""
    code: str
    name: str
    name_hindi: str
    type: str  # public, private, small_finance, post_office
    fd_rates: List[BankFDRate]
    rd_rate: float
    savings_rate: float
    features: List[str]
    website: str


# Comprehensive Bank FD Rates Database (as of Feb 2026)
# Sources: RBI, Bank websites
BANK_DATA: Dict[str, BankInfo] = {
    "sbi": BankInfo(
        code="sbi",
        name="State Bank of India",
        name_hindi="भारतीय स्टेट बैंक",
        type="public",
        fd_rates=[
            BankFDRate("sbi", "SBI", 12, 6.80, 7.30, 1000, None, "2026-02-01", "https://sbi.co.in"),
            BankFDRate("sbi", "SBI", 24, 7.00, 7.50, 1000, None, "2026-02-01", "https://sbi.co.in"),
            BankFDRate("sbi", "SBI", 36, 6.75, 7.25, 1000, None, "2026-02-01", "https://sbi.co.in"),
            BankFDRate("sbi", "SBI", 60, 6.50, 7.00, 1000, None, "2026-02-01", "https://sbi.co.in"),
        ],
        rd_rate=6.50,
        savings_rate=2.70,
        features=["Largest branch network", "YONO app", "Government backed"],
        website="https://sbi.co.in"
    ),
    "hdfc": BankInfo(
        code="hdfc",
        name="HDFC Bank",
        name_hindi="एचडीएफसी बैंक",
        type="private",
        fd_rates=[
            BankFDRate("hdfc", "HDFC Bank", 12, 7.00, 7.50, 5000, None, "2026-02-01", "https://hdfcbank.com"),
            BankFDRate("hdfc", "HDFC Bank", 24, 7.10, 7.60, 5000, None, "2026-02-01", "https://hdfcbank.com"),
            BankFDRate("hdfc", "HDFC Bank", 36, 7.00, 7.50, 5000, None, "2026-02-01", "https://hdfcbank.com"),
            BankFDRate("hdfc", "HDFC Bank", 60, 7.00, 7.50, 5000, None, "2026-02-01", "https://hdfcbank.com"),
        ],
        rd_rate=6.75,
        savings_rate=3.00,
        features=["Best digital banking", "Wide ATM network", "Premium services"],
        website="https://hdfcbank.com"
    ),
    "icici": BankInfo(
        code="icici",
        name="ICICI Bank",
        name_hindi="आईसीआईसीआई बैंक",
        type="private",
        fd_rates=[
            BankFDRate("icici", "ICICI Bank", 12, 6.90, 7.40, 10000, None, "2026-02-01", "https://icicibank.com"),
            BankFDRate("icici", "ICICI Bank", 24, 7.00, 7.50, 10000, None, "2026-02-01", "https://icicibank.com"),
            BankFDRate("icici", "ICICI Bank", 36, 7.00, 7.50, 10000, None, "2026-02-01", "https://icicibank.com"),
            BankFDRate("icici", "ICICI Bank", 60, 6.90, 7.40, 10000, None, "2026-02-01", "https://icicibank.com"),
        ],
        rd_rate=6.70,
        savings_rate=3.00,
        features=["iMobile app", "Instant banking", "Wide network"],
        website="https://icicibank.com"
    ),
    "axis": BankInfo(
        code="axis",
        name="Axis Bank",
        name_hindi="एक्सिस बैंक",
        type="private",
        fd_rates=[
            BankFDRate("axis", "Axis Bank", 12, 7.00, 7.50, 5000, None, "2026-02-01", "https://axisbank.com"),
            BankFDRate("axis", "Axis Bank", 24, 7.10, 7.60, 5000, None, "2026-02-01", "https://axisbank.com"),
            BankFDRate("axis", "Axis Bank", 36, 7.00, 7.50, 5000, None, "2026-02-01", "https://axisbank.com"),
            BankFDRate("axis", "Axis Bank", 60, 7.00, 7.50, 5000, None, "2026-02-01", "https://axisbank.com"),
        ],
        rd_rate=6.75,
        savings_rate=3.00,
        features=["Axis mobile app", "Good customer service", "Priority banking"],
        website="https://axisbank.com"
    ),
    "kotak": BankInfo(
        code="kotak",
        name="Kotak Mahindra Bank",
        name_hindi="कोटक महिंद्रा बैंक",
        type="private",
        fd_rates=[
            BankFDRate("kotak", "Kotak Mahindra Bank", 12, 7.10, 7.60, 5000, None, "2026-02-01", "https://kotak.com"),
            BankFDRate("kotak", "Kotak Mahindra Bank", 24, 7.15, 7.65, 5000, None, "2026-02-01", "https://kotak.com"),
            BankFDRate("kotak", "Kotak Mahindra Bank", 36, 7.10, 7.60, 5000, None, "2026-02-01", "https://kotak.com"),
            BankFDRate("kotak", "Kotak Mahindra Bank", 60, 6.75, 7.25, 5000, None, "2026-02-01", "https://kotak.com"),
        ],
        rd_rate=6.80,
        savings_rate=3.50,
        features=["811 zero balance account", "Good savings rate", "Kotak app"],
        website="https://kotak.com"
    ),
    "pnb": BankInfo(
        code="pnb",
        name="Punjab National Bank",
        name_hindi="पंजाब नेशनल बैंक",
        type="public",
        fd_rates=[
            BankFDRate("pnb", "Punjab National Bank", 12, 6.80, 7.30, 1000, None, "2026-02-01", "https://pnbindia.in"),
            BankFDRate("pnb", "Punjab National Bank", 24, 6.80, 7.30, 1000, None, "2026-02-01", "https://pnbindia.in"),
            BankFDRate("pnb", "Punjab National Bank", 36, 6.50, 7.00, 1000, None, "2026-02-01", "https://pnbindia.in"),
            BankFDRate("pnb", "Punjab National Bank", 60, 6.50, 7.00, 1000, None, "2026-02-01", "https://pnbindia.in"),
        ],
        rd_rate=6.50,
        savings_rate=2.70,
        features=["Government bank", "Wide rural presence", "PNB ONE app"],
        website="https://pnbindia.in"
    ),
    "bob": BankInfo(
        code="bob",
        name="Bank of Baroda",
        name_hindi="बैंक ऑफ बड़ौदा",
        type="public",
        fd_rates=[
            BankFDRate("bob", "Bank of Baroda", 12, 6.85, 7.35, 1000, None, "2026-02-01", "https://bankofbaroda.in"),
            BankFDRate("bob", "Bank of Baroda", 24, 7.05, 7.55, 1000, None, "2026-02-01", "https://bankofbaroda.in"),
            BankFDRate("bob", "Bank of Baroda", 36, 6.80, 7.30, 1000, None, "2026-02-01", "https://bankofbaroda.in"),
            BankFDRate("bob", "Bank of Baroda", 60, 6.50, 7.00, 1000, None, "2026-02-01", "https://bankofbaroda.in"),
        ],
        rd_rate=6.50,
        savings_rate=2.75,
        features=["International presence", "bob World app", "Good rates"],
        website="https://bankofbaroda.in"
    ),
    "canara": BankInfo(
        code="canara",
        name="Canara Bank",
        name_hindi="केनरा बैंक",
        type="public",
        fd_rates=[
            BankFDRate("canara", "Canara Bank", 12, 6.85, 7.35, 1000, None, "2026-02-01", "https://canarabank.com"),
            BankFDRate("canara", "Canara Bank", 24, 7.00, 7.50, 1000, None, "2026-02-01", "https://canarabank.com"),
            BankFDRate("canara", "Canara Bank", 36, 6.70, 7.20, 1000, None, "2026-02-01", "https://canarabank.com"),
            BankFDRate("canara", "Canara Bank", 60, 6.50, 7.00, 1000, None, "2026-02-01", "https://canarabank.com"),
        ],
        rd_rate=6.50,
        savings_rate=2.90,
        features=["South India strong presence", "CANARA ai1", "Government bank"],
        website="https://canarabank.com"
    ),
    "union": BankInfo(
        code="union",
        name="Union Bank of India",
        name_hindi="यूनियन बैंक ऑफ इंडिया",
        type="public",
        fd_rates=[
            BankFDRate("union", "Union Bank of India", 12, 6.80, 7.30, 1000, None, "2026-02-01", "https://unionbankofindia.co.in"),
            BankFDRate("union", "Union Bank of India", 24, 7.00, 7.50, 1000, None, "2026-02-01", "https://unionbankofindia.co.in"),
            BankFDRate("union", "Union Bank of India", 36, 6.70, 7.20, 1000, None, "2026-02-01", "https://unionbankofindia.co.in"),
            BankFDRate("union", "Union Bank of India", 60, 6.50, 7.00, 1000, None, "2026-02-01", "https://unionbankofindia.co.in"),
        ],
        rd_rate=6.50,
        savings_rate=2.75,
        features=["Wide network", "Vyom app", "Government bank"],
        website="https://unionbankofindia.co.in"
    ),
    "post_office": BankInfo(
        code="post_office",
        name="Post Office",
        name_hindi="पोस्ट ऑफिस",
        type="post_office",
        fd_rates=[
            BankFDRate("post_office", "Post Office TD", 12, 6.90, 6.90, 1000, None, "2026-02-01", "https://indiapost.gov.in"),
            BankFDRate("post_office", "Post Office TD", 24, 7.00, 7.00, 1000, None, "2026-02-01", "https://indiapost.gov.in"),
            BankFDRate("post_office", "Post Office TD", 36, 7.10, 7.10, 1000, None, "2026-02-01", "https://indiapost.gov.in"),
            BankFDRate("post_office", "Post Office TD", 60, 7.50, 7.50, 1000, None, "2026-02-01", "https://indiapost.gov.in"),
        ],
        rd_rate=6.70,
        savings_rate=4.00,
        features=["Government guaranteed", "Tax saving FD available", "Rural reach", "Highest safety"],
        website="https://indiapost.gov.in"
    ),
    "idfc": BankInfo(
        code="idfc",
        name="IDFC First Bank",
        name_hindi="आईडीएफसी फर्स्ट बैंक",
        type="private",
        fd_rates=[
            BankFDRate("idfc", "IDFC First Bank", 12, 7.25, 7.75, 10000, None, "2026-02-01", "https://idfcfirstbank.com"),
            BankFDRate("idfc", "IDFC First Bank", 24, 7.25, 7.75, 10000, None, "2026-02-01", "https://idfcfirstbank.com"),
            BankFDRate("idfc", "IDFC First Bank", 36, 7.00, 7.50, 10000, None, "2026-02-01", "https://idfcfirstbank.com"),
            BankFDRate("idfc", "IDFC First Bank", 60, 7.00, 7.50, 10000, None, "2026-02-01", "https://idfcfirstbank.com"),
        ],
        rd_rate=7.00,
        savings_rate=6.00,
        features=["Highest savings rate", "Zero fee banking", "Modern app"],
        website="https://idfcfirstbank.com"
    ),
    "yes": BankInfo(
        code="yes",
        name="Yes Bank",
        name_hindi="यस बैंक",
        type="private",
        fd_rates=[
            BankFDRate("yes", "Yes Bank", 12, 7.25, 7.75, 10000, None, "2026-02-01", "https://yesbank.in"),
            BankFDRate("yes", "Yes Bank", 24, 7.25, 7.75, 10000, None, "2026-02-01", "https://yesbank.in"),
            BankFDRate("yes", "Yes Bank", 36, 7.00, 7.50, 10000, None, "2026-02-01", "https://yesbank.in"),
            BankFDRate("yes", "Yes Bank", 60, 7.00, 7.50, 10000, None, "2026-02-01", "https://yesbank.in"),
        ],
        rd_rate=6.75,
        savings_rate=4.00,
        features=["Good FD rates", "Digital first", "YES PAY wallet"],
        website="https://yesbank.in"
    ),
    "indusind": BankInfo(
        code="indusind",
        name="IndusInd Bank",
        name_hindi="इंडसइंड बैंक",
        type="private",
        fd_rates=[
            BankFDRate("indusind", "IndusInd Bank", 12, 7.25, 7.75, 10000, None, "2026-02-01", "https://indusind.com"),
            BankFDRate("indusind", "IndusInd Bank", 24, 7.25, 7.75, 10000, None, "2026-02-01", "https://indusind.com"),
            BankFDRate("indusind", "IndusInd Bank", 36, 7.25, 7.75, 10000, None, "2026-02-01", "https://indusind.com"),
            BankFDRate("indusind", "IndusInd Bank", 60, 7.00, 7.50, 10000, None, "2026-02-01", "https://indusind.com"),
        ],
        rd_rate=7.00,
        savings_rate=4.00,
        features=["Good FD rates", "IndusMobile app", "Pioneer in fingerprint banking"],
        website="https://indusind.com"
    ),
}

# Government Scheme Rates (Small Savings)
SCHEME_RATES = {
    "ppf": {"rate": 7.1, "min": 500, "max": 150000, "tenure": "15 years", "tax": "EEE", "updated": "2026-01-01"},
    "ssy": {"rate": 8.2, "min": 250, "max": 150000, "tenure": "21 years", "tax": "EEE", "updated": "2026-01-01"},
    "nsc": {"rate": 7.7, "min": 1000, "max": None, "tenure": "5 years", "tax": "80C", "updated": "2026-01-01"},
    "kvp": {"rate": 7.5, "min": 1000, "max": None, "tenure": "115 months", "tax": "Taxable", "updated": "2026-01-01"},
    "scss": {"rate": 8.2, "min": 1000, "max": 3000000, "tenure": "5 years", "tax": "80C", "updated": "2026-01-01"},
    "mis": {"rate": 7.4, "min": 1000, "max": 900000, "tenure": "5 years", "tax": "Taxable", "updated": "2026-01-01"},
    "td_1yr": {"rate": 6.9, "min": 1000, "max": None, "tenure": "1 year", "tax": "80C (5yr)", "updated": "2026-01-01"},
    "td_5yr": {"rate": 7.5, "min": 1000, "max": None, "tenure": "5 years", "tax": "80C", "updated": "2026-01-01"},
    "nps_equity": {"rate": 10.0, "min": 500, "max": None, "tenure": "Till 60", "tax": "80CCD", "updated": "2026-01-01"},
    "nps_govt": {"rate": 8.5, "min": 500, "max": None, "tenure": "Till 60", "tax": "80CCD", "updated": "2026-01-01"},
    "epf": {"rate": 8.15, "min": None, "max": None, "tenure": "Till retirement", "tax": "EEE", "updated": "2026-01-01"},
}

# Income Tax Slabs (New Regime FY 2025-26)
TAX_SLABS_NEW = [
    {"min": 0, "max": 300000, "rate": 0, "description": "No tax"},
    {"min": 300001, "max": 700000, "rate": 5, "description": "5% tax"},
    {"min": 700001, "max": 1000000, "rate": 10, "description": "10% tax"},
    {"min": 1000001, "max": 1200000, "rate": 15, "description": "15% tax"},
    {"min": 1200001, "max": 1500000, "rate": 20, "description": "20% tax"},
    {"min": 1500001, "max": float('inf'), "rate": 30, "description": "30% tax"},
]

# Income Tax Slabs (Old Regime FY 2025-26)
TAX_SLABS_OLD = [
    {"min": 0, "max": 250000, "rate": 0, "description": "No tax"},
    {"min": 250001, "max": 500000, "rate": 5, "description": "5% tax"},
    {"min": 500001, "max": 1000000, "rate": 20, "description": "20% tax"},
    {"min": 1000001, "max": float('inf'), "rate": 30, "description": "30% tax"},
]

# Inflation Data (Average CPI)
INFLATION_DATA = {
    "current": 5.5,
    "5yr_avg": 5.2,
    "10yr_avg": 5.8,
    "education_inflation": 10.0,
    "medical_inflation": 12.0,
    "food_inflation": 6.5,
}

# Bank name aliases for matching
BANK_ALIASES = {
    "state bank": "sbi", "sbi": "sbi", "स्टेट बैंक": "sbi",
    "hdfc": "hdfc", "एचडीएफसी": "hdfc",
    "icici": "icici", "आईसीआईसीआई": "icici",
    "axis": "axis", "एक्सिस": "axis",
    "kotak": "kotak", "कोटक": "kotak",
    "pnb": "pnb", "punjab national": "pnb", "पंजाब नेशनल": "pnb",
    "bank of baroda": "bob", "bob": "bob", "baroda": "bob", "बड़ौदा": "bob",
    "canara": "canara", "केनरा": "canara",
    "union bank": "union", "union": "union", "यूनियन": "union",
    "post office": "post_office", "post": "post_office", "पोस्ट ऑफिस": "post_office", "india post": "post_office",
    "idfc": "idfc", "idfc first": "idfc",
    "yes bank": "yes", "yes": "yes",
    "indusind": "indusind",
}


class FinancialDataHub:
    """
    Centralized financial data service.
    Provides rates, comparisons, and citations for the advisor.
    """
    
    def __init__(self):
        self._cache = {}
    
    # Expose module constants as properties for easy access
    @property
    def scheme_rates(self) -> Dict[str, Dict]:
        return SCHEME_RATES
    
    @property
    def tax_slabs(self) -> Dict[str, List]:
        return {"new": TAX_SLABS_NEW, "old": TAX_SLABS_OLD}
    
    @property
    def inflation_data(self) -> Dict[str, float]:
        return INFLATION_DATA
    
    def resolve_bank_name(self, query: str) -> Optional[str]:
        """Resolve bank name/alias to bank code."""
        query_lower = query.lower().strip()
        for alias, code in BANK_ALIASES.items():
            if alias in query_lower or query_lower in alias:
                return code
        return None
    
    def get_bank_info(self, bank_code: str) -> Optional[BankInfo]:
        """Get complete bank information."""
        return BANK_DATA.get(bank_code.lower())
    
    def get_bank_fd_rate(
        self, 
        bank_code: str, 
        tenure_months: int = 12,
        is_senior: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get FD rate for specific bank and tenure."""
        bank = BANK_DATA.get(bank_code.lower())
        if not bank:
            return None
        
        # Find closest tenure
        closest_rate = None
        min_diff = float('inf')
        
        for rate in bank.fd_rates:
            diff = abs(rate.tenure_months - tenure_months)
            if diff < min_diff:
                min_diff = diff
                closest_rate = rate
        
        if not closest_rate:
            return None
        
        return {
            "bank": bank.name,
            "bank_hindi": bank.name_hindi,
            "tenure_months": closest_rate.tenure_months,
            "rate": closest_rate.senior_citizen_rate if is_senior else closest_rate.general_rate,
            "general_rate": closest_rate.general_rate,
            "senior_rate": closest_rate.senior_citizen_rate,
            "min_amount": closest_rate.min_amount,
            "source": closest_rate.source_url,
            "last_updated": closest_rate.last_updated,
        }
    
    def get_all_bank_rates(self, tenure_months: int = 12, is_senior: bool = False) -> List[Dict[str, Any]]:
        """Get FD rates from all banks for comparison."""
        rates = []
        for code, bank in BANK_DATA.items():
            rate_info = self.get_bank_fd_rate(code, tenure_months, is_senior)
            if rate_info:
                rate_info["bank_code"] = code
                rate_info["bank_type"] = bank.type
                rates.append(rate_info)
        
        # Sort by rate (highest first)
        rates.sort(key=lambda x: x["rate"], reverse=True)
        return rates
    
    def get_best_fd_rates(self, tenure_months: int = 12, is_senior: bool = False, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top N best FD rates."""
        all_rates = self.get_all_bank_rates(tenure_months, is_senior)
        return all_rates[:top_n]
    
    def compare_banks(self, bank_codes: List[str], tenure_months: int = 12) -> Dict[str, Any]:
        """Compare FD rates between specific banks."""
        comparison = []
        for code in bank_codes:
            rate = self.get_bank_fd_rate(code, tenure_months)
            if rate:
                comparison.append(rate)
        
        comparison.sort(key=lambda x: x["rate"], reverse=True)
        
        return {
            "tenure_months": tenure_months,
            "banks_compared": len(comparison),
            "comparison": comparison,
            "best_bank": comparison[0] if comparison else None,
            "rate_difference": round(comparison[0]["rate"] - comparison[-1]["rate"], 2) if len(comparison) > 1 else 0
        }
    
    def get_scheme_rate(self, scheme_code: str) -> Optional[Dict[str, Any]]:
        """Get government scheme rate."""
        scheme = SCHEME_RATES.get(scheme_code.lower())
        if scheme:
            scheme["code"] = scheme_code
        return scheme
    
    def get_all_scheme_rates(self) -> Dict[str, Dict[str, Any]]:
        """Get all government scheme rates."""
        return SCHEME_RATES.copy()
    
    def get_tax_slabs(self, regime: str = "new") -> List[Dict[str, Any]]:
        """Get income tax slabs."""
        return TAX_SLABS_NEW if regime.lower() == "new" else TAX_SLABS_OLD
    
    def calculate_tax(self, income: float, regime: str = "new") -> Dict[str, Any]:
        """Calculate income tax for given income."""
        slabs = self.get_tax_slabs(regime)
        tax = 0
        breakdown = []
        
        remaining_income = income
        for slab in slabs:
            if remaining_income <= 0:
                break
            
            slab_min = slab["min"]
            slab_max = slab["max"]
            rate = slab["rate"]
            
            if income > slab_min:
                taxable_in_slab = min(remaining_income, slab_max - slab_min)
                tax_in_slab = taxable_in_slab * rate / 100
                tax += tax_in_slab
                
                if taxable_in_slab > 0 and rate > 0:
                    breakdown.append({
                        "slab": f"{slab_min:,} - {slab_max:,}" if slab_max != float('inf') else f"{slab_min:,}+",
                        "rate": rate,
                        "taxable": taxable_in_slab,
                        "tax": tax_in_slab
                    })
                
                remaining_income -= taxable_in_slab
        
        # Add cess (4% health and education cess)
        cess = tax * 0.04
        total_tax = tax + cess
        
        return {
            "income": income,
            "regime": regime,
            "tax_before_cess": round(tax, 2),
            "cess": round(cess, 2),
            "total_tax": round(total_tax, 2),
            "effective_rate": round((total_tax / income) * 100, 2) if income > 0 else 0,
            "breakdown": breakdown
        }
    
    def get_inflation_rate(self, category: str = "current") -> float:
        """Get inflation rate."""
        return INFLATION_DATA.get(category, INFLATION_DATA["current"])
    
    def format_bank_comparison_hinglish(self, comparison: Dict[str, Any]) -> str:
        """Format bank comparison in Hinglish for LLM context."""
        if not comparison.get("comparison"):
            return "Bank comparison data not available."
        
        lines = [f"**{comparison['tenure_months']} mahine ke FD rates comparison:**\n"]
        
        for i, bank in enumerate(comparison["comparison"], 1):
            lines.append(
                f"{i}. **{bank['bank']}**: {bank['rate']}% "
                f"(Senior: {bank['senior_rate']}%)"
            )
        
        if comparison.get("best_bank"):
            best = comparison["best_bank"]
            lines.append(f"\n**Best rate:** {best['bank']} mein {best['rate']}% mil raha hai.")
        
        return "\n".join(lines)
    
    def format_scheme_rates_hinglish(self) -> str:
        """Format all scheme rates in Hinglish for LLM context."""
        lines = ["**Current Government Scheme Rates (Feb 2026):**\n"]
        
        scheme_names = {
            "ppf": "PPF (Public Provident Fund)",
            "ssy": "SSY (Sukanya Samriddhi Yojana)",
            "nsc": "NSC (National Savings Certificate)",
            "scss": "SCSS (Senior Citizen Savings Scheme)",
            "nps_equity": "NPS Equity Fund (avg)",
            "epf": "EPF (Employee Provident Fund)",
        }
        
        for code, name in scheme_names.items():
            if code in SCHEME_RATES:
                rate = SCHEME_RATES[code]
                lines.append(f"- {name}: **{rate['rate']}%** p.a. ({rate['tax']} tax benefit)")
        
        return "\n".join(lines)
    
    def get_context_for_llm(self, user_bank: str = None, query_type: str = None) -> str:
        """
        Build context string with relevant financial data for LLM injection.
        """
        context_parts = []
        
        # Always include current scheme rates
        context_parts.append(self.format_scheme_rates_hinglish())
        
        # If user mentioned a bank, include their rates
        if user_bank:
            bank_code = self.resolve_bank_name(user_bank)
            if bank_code:
                bank = BANK_DATA.get(bank_code)
                if bank:
                    context_parts.append(f"\n**{bank.name} Rates:**")
                    context_parts.append(f"- FD (1 year): {bank.fd_rates[0].general_rate}% (Senior: {bank.fd_rates[0].senior_citizen_rate}%)")
                    context_parts.append(f"- RD: {bank.rd_rate}%")
                    context_parts.append(f"- Savings: {bank.savings_rate}%")
        
        # Include best FD rates for comparison
        if query_type in ["fd", "investment", "compare"]:
            best_rates = self.get_best_fd_rates(12, False, 3)
            if best_rates:
                context_parts.append("\n**Top 3 FD Rates (1 year):**")
                for rate in best_rates:
                    context_parts.append(f"- {rate['bank']}: {rate['rate']}%")
        
        # Include inflation for goal planning
        if query_type in ["goal", "retirement", "education"]:
            context_parts.append(f"\n**Inflation Rates:**")
            context_parts.append(f"- General: {INFLATION_DATA['current']}%")
            context_parts.append(f"- Education: {INFLATION_DATA['education_inflation']}%")
            context_parts.append(f"- Medical: {INFLATION_DATA['medical_inflation']}%")
        
        return "\n".join(context_parts)


# Global instance
data_hub = FinancialDataHub()
