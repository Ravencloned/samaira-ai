"""
Financial Knowledge Base for SamairaAI.
Curated, citation-backed knowledge for RAG-lite retrieval.
Provides authoritative context to ground LLM responses.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class KBCategory(str, Enum):
    """Knowledge base categories."""
    SAVINGS = "savings"
    INVESTMENTS = "investments"
    GOVERNMENT_SCHEMES = "government_schemes"
    INSURANCE = "insurance"
    TAX = "tax"
    BANKING = "banking"
    LOANS = "loans"
    BUDGETING = "budgeting"
    RETIREMENT = "retirement"
    EDUCATION = "education"


@dataclass
class KBArticle:
    """Knowledge base article with citations."""
    id: str
    title: str
    title_hinglish: str
    category: KBCategory
    summary: str
    content: str
    key_points: List[str]
    common_questions: List[str]
    source: str
    source_url: str
    last_updated: str
    keywords: List[str]


# Curated Knowledge Base Articles
KNOWLEDGE_BASE: Dict[str, KBArticle] = {
    # ==== SAVINGS ====
    "emergency_fund": KBArticle(
        id="emergency_fund",
        title="Emergency Fund - Your Financial Safety Net",
        title_hinglish="Emergency Fund - Aapka Financial Safety Net",
        category=KBCategory.SAVINGS,
        summary="Emergency fund is money kept aside for unexpected expenses. Experts recommend 3-6 months of expenses.",
        content="""
Emergency Fund kya hai?
Emergency fund wo paisa hai jo aap unexpected situations ke liye rakhte hain - jaise job loss, medical emergency, ya urgent repairs. Ye aapka financial safety net hai.

Kitna rakhna chahiye?
- Minimum: 3 months ka monthly kharcha
- Ideal: 6 months ka monthly kharcha  
- Single income family: 6-12 months recommended
- Business owners/Freelancers: 12 months recommended

Kahaan rakhein?
1. High-yield Savings Account (IDFC First, Kotak 811 - 4-6% interest)
2. Liquid Mutual Funds (Instant redemption available)
3. FD with premature withdrawal facility
4. Combination of above

Emergency Fund vs Regular Savings:
Emergency fund SIRF emergencies ke liye hai - job loss, medical, accidents. Regular savings goals ke liye hai - vacation, gadgets, etc.

Kaise banayein?
1. Calculate monthly expenses (rent, EMI, food, utilities, insurance)
2. Multiply by 6 (for 6 months buffer)
3. Start with Rs 1,000/month if needed
4. Automate transfers on salary day
5. Don't touch for non-emergencies!
        """,
        key_points=[
            "6 months of expenses is the ideal target",
            "Keep in high-liquidity instruments",
            "Don't invest this in equity/stocks",
            "Automate monthly contributions",
            "Replenish immediately after using"
        ],
        common_questions=[
            "Emergency fund kitna hona chahiye?",
            "Emergency fund kahaan rakhein?",
            "FD mein emergency fund rakh sakte hain?",
            "Emergency fund vs savings account"
        ],
        source="Financial Planning Standards Board India",
        source_url="https://www.fpsb.co.in",
        last_updated="2026-01-15",
        keywords=["emergency", "safety net", "backup", "rainy day", "contingency", "liquid"]
    ),
    
    # ==== INVESTMENTS ====
    "sip_basics": KBArticle(
        id="sip_basics",
        title="SIP - Systematic Investment Plan Explained",
        title_hinglish="SIP - Systematic Investment Plan Samjhiye",
        category=KBCategory.INVESTMENTS,
        summary="SIP is a method to invest fixed amount regularly in mutual funds. It helps in rupee cost averaging and building wealth over time.",
        content="""
SIP kya hai?
SIP (Systematic Investment Plan) mutual funds mein regular investment karne ka tarika hai. Har month fixed amount invest hota hai automatically.

SIP ke fayde:
1. Rupee Cost Averaging - Market high ho ya low, average price milta hai
2. Discipline - Automatic deduction, no manual effort
3. Power of Compounding - Long term mein wealth create
4. Flexibility - Rs 500 se shuru kar sakte hain
5. No timing needed - Don't need to time the market

SIP vs Lumpsum:
- SIP: Salaried people ke liye best, market volatility kam
- Lumpsum: Bonus/windfall ke liye, if market is low

SIP kaise shuru karein?
1. KYC complete karein (PAN, Aadhaar, Bank details)
2. AMC website ya app se register
3. Fund select karein (based on goal & risk)
4. SIP amount aur date set karein
5. Bank mandate (auto-debit) activate karein

SIP returns expectations:
- Large Cap Funds: 10-12% long term average
- Mid Cap Funds: 12-15% long term average
- Small Cap Funds: 15-18% (but high risk)
- Debt Funds: 6-8%

Important: Past returns guarantee nahi hain. Market risks hain.
        """,
        key_points=[
            "Start with Rs 500 minimum in most funds",
            "Longer duration = better compounding",
            "Don't stop SIP during market crashes",
            "Choose direct plans for lower expense ratio",
            "SIP date doesn't matter much - stay consistent"
        ],
        common_questions=[
            "SIP kya hai?",
            "SIP kaise start karein?",
            "SIP mein minimum kitna invest kar sakte hain?",
            "SIP vs RD kya better hai?",
            "SIP se kitna return milta hai?"
        ],
        source="AMFI India",
        source_url="https://www.amfiindia.com",
        last_updated="2026-01-15",
        keywords=["sip", "mutual fund", "systematic", "investment", "monthly", "compounding"]
    ),
    
    "fd_basics": KBArticle(
        id="fd_basics",
        title="Fixed Deposit - Safe Investment Option",
        title_hinglish="Fixed Deposit - Safe Investment Option",
        category=KBCategory.SAVINGS,
        summary="FD is a safe investment where you deposit money for a fixed tenure at a guaranteed interest rate.",
        content="""
FD kya hai?
Fixed Deposit (FD) mein aap bank ya post office mein paisa fixed time ke liye rakhte hain. Interest rate fix hota hai, guaranteed returns milte hain.

FD ke types:
1. Regular FD - Normal interest, anytime withdrawal (with penalty)
2. Tax Saver FD - 5 year lock-in, 80C benefit, up to Rs 1.5 lakh
3. Senior Citizen FD - Extra 0.25-0.50% interest for 60+ age
4. Flexi FD - Linked to savings, auto sweep
5. Cumulative vs Non-Cumulative - Interest at maturity vs quarterly/monthly

Current FD rates (Feb 2026):
- SBI: 6.50-7.00% (general), 7.00-7.50% (senior)
- HDFC: 6.75-7.10%
- Post Office: 6.90-7.50%
- Small Finance Banks: 7.50-8.50%

FD vs RD:
- FD: Lumpsum one-time deposit
- RD: Monthly deposit like SIP

Tax on FD:
- Interest is fully taxable as per your slab
- TDS at 10% if interest > Rs 40,000/year (Rs 50,000 for seniors)
- Submit Form 15G/15H to avoid TDS if income below taxable limit

FD laddering strategy:
Instead of one big FD, split into multiple FDs with different maturities (1yr, 2yr, 3yr). This gives liquidity and averages interest rates.
        """,
        key_points=[
            "Guaranteed returns - no market risk",
            "Senior citizens get 0.25-0.50% extra",
            "Tax Saver FD gives 80C benefit",
            "Premature withdrawal has 0.5-1% penalty",
            "Compare rates - private banks often give more"
        ],
        common_questions=[
            "FD ka interest rate kitna hai?",
            "FD vs RD kya better hai?",
            "Tax saving FD kya hai?",
            "Senior citizen FD rates?",
            "FD todne par kitna loss hota hai?"
        ],
        source="RBI & Bank Websites",
        source_url="https://rbi.org.in",
        last_updated="2026-02-01",
        keywords=["fd", "fixed deposit", "safe", "guaranteed", "interest", "bank"]
    ),
    
    # ==== GOVERNMENT SCHEMES ====
    "ppf_guide": KBArticle(
        id="ppf_guide",
        title="PPF - Public Provident Fund Complete Guide",
        title_hinglish="PPF - Public Provident Fund Complete Guide",
        category=KBCategory.GOVERNMENT_SCHEMES,
        summary="PPF is a 15-year government savings scheme with tax-free returns. One of the safest investment options.",
        content="""
PPF kya hai?
Public Provident Fund government ki guaranteed savings scheme hai. 15 saal ka tenure, tax-free returns, aur sovereign guarantee.

PPF key features:
- Interest Rate: 7.1% p.a. (compounded yearly)
- Tenure: 15 years (extendable in 5-year blocks)
- Min Investment: Rs 500/year
- Max Investment: Rs 1,50,000/year
- Tax Benefit: EEE (Exempt-Exempt-Exempt)
  - Investment: 80C deduction
  - Interest: Tax-free
  - Maturity: Tax-free

PPF account kaise kholein:
1. Post Office ya Bank mein jaayein (SBI, HDFC, ICICI, etc.)
2. Documents: PAN, Aadhaar, Passport photo
3. Minimum Rs 500 se account khul jaata hai
4. Online bhi khol sakte hain net banking se

PPF withdrawal rules:
- Partial withdrawal: 7th year se, 50% of balance
- Loan: 3rd to 6th year, against PPF balance
- Premature closure: After 5 years (special cases only)

PPF vs other options:
- PPF vs FD: PPF gives tax-free returns, FD is taxable
- PPF vs SIP: PPF is safe but lower returns, SIP has market risk but higher potential
- PPF vs SSY: SSY for daughters only, higher rate (8.2%)

Who should invest in PPF?
- Risk-averse investors
- Long-term goal planners (15+ years)
- Tax saving seekers
- Retirement planners
        """,
        key_points=[
            "7.1% interest - government guaranteed",
            "EEE tax status - completely tax-free",
            "15 year lock-in - long term commitment",
            "Max Rs 1.5 lakh per year investment",
            "Partial withdrawal from 7th year"
        ],
        common_questions=[
            "PPF interest rate kya hai?",
            "PPF account kaise kholein?",
            "PPF mein maximum kitna invest kar sakte hain?",
            "PPF vs FD kya better hai?",
            "PPF se paise kab nikal sakte hain?"
        ],
        source="Ministry of Finance, Government of India",
        source_url="https://www.nsiindia.gov.in",
        last_updated="2026-01-01",
        keywords=["ppf", "public provident fund", "government", "tax free", "15 years", "80c"]
    ),
    
    "ssy_guide": KBArticle(
        id="ssy_guide",
        title="Sukanya Samriddhi Yojana - For Your Daughter's Future",
        title_hinglish="Sukanya Samriddhi Yojana - Beti Ke Future Ke Liye",
        category=KBCategory.GOVERNMENT_SCHEMES,
        summary="SSY is a government scheme for girl child with highest small savings interest rate. Perfect for daughter's education and marriage.",
        content="""
Sukanya Samriddhi Yojana kya hai?
Beti Bachao Beti Padhao initiative ke under ye scheme hai. Girl child ke future ke liye savings scheme with highest interest among small savings.

SSY key features:
- Interest Rate: 8.2% p.a. (highest among small savings!)
- Eligibility: Girl child below 10 years
- Account Tenure: 21 years from opening
- Deposit Period: First 15 years only
- Min Deposit: Rs 250/year
- Max Deposit: Rs 1,50,000/year
- Tax Benefit: EEE (completely tax-free)

SSY account kaise kholein:
1. Post Office ya authorized bank mein jaayein
2. Documents: Birth certificate (girl child), Parent's ID
3. Maximum 2 accounts (2 daughters ke liye)
4. Third account only for twins/triplets

Withdrawal rules:
- 50% withdrawal: After girl turns 18 (for education)
- Full maturity: When girl turns 21
- Marriage withdrawal: After 18 years of age
- Premature closure: Death, serious illness only

SSY vs PPF:
- SSY: 8.2% vs PPF: 7.1%
- SSY: Only for girl child
- SSY: 21 year tenure vs PPF: 15 years
- Both have EEE tax benefit

Example calculation:
If you invest Rs 1.5 lakh/year for 15 years:
- Total invested: Rs 22.5 lakhs
- Maturity (21 years): ~Rs 70 lakhs
- Interest earned: ~Rs 47.5 lakhs (tax-free!)
        """,
        key_points=[
            "8.2% interest - highest small savings rate",
            "Only for girls below 10 years",
            "50% early withdrawal for education at 18",
            "EEE tax benefit like PPF",
            "Maximum Rs 1.5 lakh per year"
        ],
        common_questions=[
            "Sukanya Samriddhi Yojana interest rate kya hai?",
            "SSY account kaise kholein?",
            "SSY se paise kab nikal sakte hain?",
            "SSY vs PPF kya better hai beti ke liye?",
            "SSY mein kitna return milega?"
        ],
        source="Ministry of Finance, Government of India",
        source_url="https://www.nsiindia.gov.in",
        last_updated="2026-01-01",
        keywords=["ssy", "sukanya", "samriddhi", "yojana", "daughter", "beti", "girl child"]
    ),
    
    "nps_guide": KBArticle(
        id="nps_guide",
        title="NPS - National Pension System for Retirement",
        title_hinglish="NPS - National Pension System Retirement Ke Liye",
        category=KBCategory.RETIREMENT,
        summary="NPS is a market-linked pension scheme for retirement. Offers extra Rs 50,000 tax deduction under 80CCD(1B).",
        content="""
NPS kya hai?
National Pension System retirement ke liye pension scheme hai. Market-linked hai, toh returns equity/debt mein invest hone ke basis par milte hain.

NPS key features:
- Returns: 8-12% based on asset allocation
- Tier I: Main pension account (locked till 60)
- Tier II: Voluntary savings (no lock-in, no tax benefit)
- Tax Benefits:
  - 80CCD(1): Up to Rs 1.5 lakh (within 80C limit)
  - 80CCD(1B): Additional Rs 50,000 (exclusive!)
  - 80CCD(2): Employer contribution up to 10% of salary

NPS Asset Classes:
- Class E (Equity): Up to 75% exposure, highest risk/return
- Class C (Corporate Bonds): Moderate risk
- Class G (Government Securities): Lowest risk
- Class A (Alternative): REITs, InvITs (limited)

Active vs Auto Choice:
- Active: You decide allocation (max 75% equity till 50 yrs)
- Auto: Based on age - Aggressive/Moderate/Conservative

NPS at retirement (60 years):
- 60% lump sum (tax-free since 2019)
- 40% mandatory annuity (pension for life, taxable)

Who should invest?
- Salaried wanting extra tax saving
- Self-employed retirement planning
- Long-term investors okay with market risk
        """,
        key_points=[
            "Extra Rs 50,000 tax deduction under 80CCD(1B)",
            "Market-linked - potential for higher returns",
            "60% lump sum at retirement is tax-free",
            "40% must be used for annuity (pension)",
            "Lowest fund management charges"
        ],
        common_questions=[
            "NPS kya hai?",
            "NPS mein tax benefit kitna hai?",
            "NPS vs PPF kya better hai?",
            "NPS se pension kitni milegi?",
            "NPS kaise start karein?"
        ],
        source="Pension Fund Regulatory and Development Authority",
        source_url="https://www.npscra.nsdl.co.in",
        last_updated="2026-01-01",
        keywords=["nps", "pension", "retirement", "80ccd", "annuity", "pfrda"]
    ),
    
    # ==== INSURANCE ====
    "term_insurance": KBArticle(
        id="term_insurance",
        title="Term Life Insurance - Pure Protection",
        title_hinglish="Term Life Insurance - Pure Protection",
        category=KBCategory.INSURANCE,
        summary="Term insurance provides high coverage at low premium. Essential for family protection.",
        content="""
Term Insurance kya hai?
Term insurance pure life cover hai - agar policyholder ki death ho jaaye term ke andar, family ko sum assured milta hai. No maturity benefit.

Why term insurance is important:
- High coverage at low cost (Rs 1 crore cover for ~Rs 10,000/year at 30 yrs)
- Replaces your income for family
- Debt/loan coverage
- Children's education/marriage security

How much cover do you need?
Formula: Annual income x 10-15 times
Or: Total financial liabilities + Future goals corpus

Example: Rs 10 lakh income
- Cover needed: Rs 1-1.5 crore
- Premium: ~Rs 12,000-15,000/year

Term vs Traditional Insurance:
- Term: Pure protection, no returns, low premium
- LIC Endowment: Lower cover, some returns, high premium
- ULIP: Market-linked, high charges, complicated

Riders to consider:
- Critical Illness: Lump sum on diagnosis
- Accidental Death: Additional sum assured
- Waiver of Premium: No premium if disabled

When to buy:
- As early as possible (lower premium)
- Before taking loans/EMIs
- After marriage/having children
- While healthy (no medical loading)
        """,
        key_points=[
            "Cover should be 10-15x annual income",
            "Buy early - premium is lower",
            "Pure protection - no investment component",
            "Add critical illness rider if possible",
            "Compare quotes online before buying"
        ],
        common_questions=[
            "Term insurance kitna lena chahiye?",
            "Term insurance vs LIC policy kya better?",
            "Term insurance ka premium kitna hai?",
            "Best term insurance company kaun si hai?",
            "Term insurance mein claim kaise milta hai?"
        ],
        source="IRDAI",
        source_url="https://www.irdai.gov.in",
        last_updated="2026-01-01",
        keywords=["term", "life insurance", "protection", "premium", "coverage", "death benefit"]
    ),
    
    # ==== TAX ====
    "section_80c": KBArticle(
        id="section_80c",
        title="Section 80C - Tax Saving Options",
        title_hinglish="Section 80C - Tax Bachane Ke Options",
        category=KBCategory.TAX,
        summary="Section 80C allows deduction up to Rs 1.5 lakh from taxable income. Multiple investment options available.",
        content="""
Section 80C kya hai?
Income Tax Act ka 80C section aapko Rs 1.5 lakh tak ki deduction deta hai taxable income se. Ye Old Tax Regime mein available hai.

80C options (best to worst for most people):
1. EPF (Employee Provident Fund) - Salaried automatically contribute
2. PPF (Public Provident Fund) - 7.1%, tax-free, 15 years
3. ELSS (Equity Linked Savings Scheme) - Mutual fund, 3 year lock-in, potential 12%+ returns
4. SSY (Sukanya Samriddhi) - 8.2%, for daughters
5. NPS - Additional 50K under 80CCD(1B)
6. Tax Saver FD - 5 year lock-in, guaranteed returns
7. Life Insurance Premium - Term plan is best
8. Children's Tuition Fees - School/college fees
9. Home Loan Principal - Part of EMI
10. NSC - 7.7%, 5 years

80C strategy:
- First: EPF contribution (automatic)
- Then: PPF for safety OR ELSS for growth
- Optional: SSY if you have daughter
- Don't: Buy insurance just for 80C

Beyond 80C:
- 80CCD(1B): NPS extra Rs 50,000
- 80D: Health insurance Rs 25,000-50,000
- 80E: Education loan interest (no limit)
- 80TTA: Savings interest up to Rs 10,000

New vs Old Regime:
- New: Lower rates, no deductions
- Old: Higher rates, 80C and other deductions
- Calculate which is better for your income level
        """,
        key_points=[
            "Maximum Rs 1.5 lakh deduction",
            "EPF counts automatically if salaried",
            "ELSS has only 3-year lock-in",
            "PPF is safest with EEE benefit",
            "Don't buy insurance just for 80C"
        ],
        common_questions=[
            "80C mein kya kya aata hai?",
            "80C limit kitni hai?",
            "ELSS vs PPF kya better hai tax saving ke liye?",
            "80C ke alawa aur kaise tax bachayein?",
            "New tax regime mein 80C milta hai kya?"
        ],
        source="Income Tax Department",
        source_url="https://www.incometax.gov.in",
        last_updated="2026-01-01",
        keywords=["80c", "tax saving", "deduction", "elss", "ppf", "tax benefit"]
    ),
}


class FinancialKnowledgeBase:
    """
    Knowledge base manager for RAG-lite retrieval.
    Provides relevant articles based on user queries.
    """
    
    def __init__(self):
        self._articles = KNOWLEDGE_BASE
    
    def search(self, query: str, top_k: int = 3) -> List[KBArticle]:
        """
        Search knowledge base for relevant articles.
        Simple keyword matching (can be upgraded to embeddings later).
        """
        query_lower = query.lower()
        scores = []
        
        for article_id, article in self._articles.items():
            score = 0
            
            # Keyword matching
            for keyword in article.keywords:
                if keyword in query_lower:
                    score += 2
            
            # Title matching
            if any(word in article.title.lower() for word in query_lower.split()):
                score += 1
            
            # Common question matching
            for question in article.common_questions:
                if any(word in question.lower() for word in query_lower.split() if len(word) > 3):
                    score += 1
            
            if score > 0:
                scores.append((score, article))
        
        # Sort by score and return top_k
        scores.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in scores[:top_k]]
    
    def get_article(self, article_id: str) -> Optional[KBArticle]:
        """Get specific article by ID."""
        return self._articles.get(article_id)
    
    def get_by_category(self, category: KBCategory) -> List[KBArticle]:
        """Get all articles in a category."""
        return [a for a in self._articles.values() if a.category == category]
    
    def get_context_for_query(self, query: str, include_full_content: bool = False) -> str:
        """
        Get formatted context for LLM from relevant articles.
        """
        articles = self.search(query, top_k=2)
        
        if not articles:
            return ""
        
        context_parts = ["**Relevant Knowledge:**\n"]
        
        for article in articles:
            context_parts.append(f"**{article.title_hinglish}**")
            context_parts.append(f"Summary: {article.summary}")
            
            if include_full_content:
                context_parts.append(f"Details: {article.content[:500]}...")
            else:
                context_parts.append("Key Points:")
                for point in article.key_points[:3]:
                    context_parts.append(f"- {point}")
            
            context_parts.append(f"Source: {article.source}\n")
        
        return "\n".join(context_parts)
    
    def get_all_articles(self) -> List[KBArticle]:
        """Get all articles."""
        return list(self._articles.values())


# Global instance
knowledge_base = FinancialKnowledgeBase()
