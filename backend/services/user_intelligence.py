"""
User Intelligence Service - Collects and analyzes user data for personalized responses.
Features:
- User profile extraction from conversations
- Financial goal tracking
- Investment preference learning
- Personalized recommendation engine
- Chart/graph data generation
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import re


@dataclass
class UserProfile:
    """User's financial profile extracted from conversations."""
    # Demographics
    age_range: Optional[str] = None  # "20-30", "30-40", etc.
    family_status: Optional[str] = None  # "single", "married", "married_with_kids"
    occupation: Optional[str] = None
    income_range: Optional[str] = None  # "low", "medium", "high"
    
    # Financial goals
    goals: List[str] = field(default_factory=list)  # ["retirement", "education", "home"]
    risk_appetite: Optional[str] = None  # "conservative", "moderate", "aggressive"
    investment_horizon: Optional[str] = None  # "short", "medium", "long"
    
    # Knowledge level
    financial_literacy: Optional[str] = None  # "beginner", "intermediate", "advanced"
    topics_interested: List[str] = field(default_factory=list)
    topics_discussed: List[str] = field(default_factory=list)
    
    # Preferences
    preferred_language: str = "hinglish"
    wants_detailed_explanations: bool = True
    prefers_examples: bool = True
    
    # Extracted data points
    monthly_savings: Optional[float] = None
    existing_investments: List[str] = field(default_factory=list)
    dependents: int = 0
    
    # Metadata
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    conversation_count: int = 0


@dataclass 
class ChartData:
    """Data structure for generating charts/graphs."""
    chart_type: str  # "line", "bar", "pie", "comparison"
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = field(default_factory=dict)


class UserIntelligenceService:
    """
    Analyzes user conversations to build profiles and generate personalized content.
    """
    
    # Keywords for profile extraction
    GOAL_KEYWORDS = {
        'retirement': ['retire', 'pension', 'old age', 'budhapa', 'retirement'],
        'education': ['education', 'padhai', 'college', 'school', 'beta', 'beti', 'bachche'],
        'home': ['ghar', 'house', 'home', 'flat', 'apartment', 'property'],
        'emergency': ['emergency', 'rainy day', 'backup', 'mushkil'],
        'wealth': ['wealth', 'ameer', 'rich', 'paisa', 'grow money'],
        'wedding': ['shaadi', 'wedding', 'marriage', 'dulhan'],
        'travel': ['travel', 'vacation', 'trip', 'ghoomna'],
        'car': ['car', 'gaadi', 'vehicle', 'bike']
    }
    
    RISK_KEYWORDS = {
        'conservative': ['safe', 'secure', 'guaranteed', 'risk nahi', 'no risk', 'low risk', 'kam risk'],
        'moderate': ['balanced', 'medium risk', 'thoda risk'],
        'aggressive': ['high return', 'zyada return', 'aggressive', 'risk le sakta']
    }
    
    LITERACY_KEYWORDS = {
        'beginner': ['kya hota hai', 'what is', 'samjhao', 'naya hu', 'beginner', 'shuru'],
        'intermediate': ['compare', 'difference', 'better', 'which one'],
        'advanced': ['portfolio', 'diversify', 'tax optimization', 'rebalancing']
    }
    
    def __init__(self):
        self.profiles: Dict[str, UserProfile] = {}
    
    def get_or_create_profile(self, session_id: str) -> UserProfile:
        """Get existing profile or create new one."""
        if session_id not in self.profiles:
            self.profiles[session_id] = UserProfile()
        return self.profiles[session_id]
    
    def analyze_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Analyze user message to extract profile information.
        Returns extracted insights.
        """
        profile = self.get_or_create_profile(session_id)
        message_lower = message.lower()
        insights = {}
        
        # Extract goals
        for goal, keywords in self.GOAL_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                if goal not in profile.goals:
                    profile.goals.append(goal)
                    insights['new_goal'] = goal
        
        # Extract risk appetite
        for risk_level, keywords in self.RISK_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                profile.risk_appetite = risk_level
                insights['risk_appetite'] = risk_level
        
        # Extract literacy level
        for level, keywords in self.LITERACY_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                profile.financial_literacy = level
                insights['literacy_level'] = level
        
        # Extract age mentions
        age_match = re.search(r'(\d{1,2})\s*(saal|years?|age)', message_lower)
        if age_match:
            age = int(age_match.group(1))
            if age < 25:
                profile.age_range = "18-25"
            elif age < 35:
                profile.age_range = "25-35"
            elif age < 45:
                profile.age_range = "35-45"
            elif age < 55:
                profile.age_range = "45-55"
            else:
                profile.age_range = "55+"
            insights['age_range'] = profile.age_range
        
        # Extract family status
        if any(word in message_lower for word in ['shaadi', 'married', 'wife', 'husband', 'biwi', 'pati']):
            profile.family_status = 'married'
            insights['family_status'] = 'married'
        if any(word in message_lower for word in ['beta', 'beti', 'bachcha', 'child', 'kids', 'son', 'daughter']):
            profile.family_status = 'married_with_kids'
            insights['family_status'] = 'married_with_kids'
        
        # Extract savings amounts
        amount_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:rs|rupees?|₹|per month|monthly|mahine)', message_lower)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            try:
                profile.monthly_savings = float(amount_str)
                insights['monthly_savings'] = profile.monthly_savings
            except ValueError:
                pass
        
        # Track topics discussed
        topic_keywords = {
            'sip': ['sip', 'systematic investment'],
            'mutual_fund': ['mutual fund', 'mf'],
            'fd': ['fd', 'fixed deposit'],
            'rd': ['rd', 'recurring deposit'],
            'ppf': ['ppf', 'public provident'],
            'nps': ['nps', 'national pension'],
            'stocks': ['stock', 'share', 'equity'],
            'insurance': ['insurance', 'bima', 'lic'],
            'tax': ['tax', 'income tax', '80c'],
            'gold': ['gold', 'sona', 'sovereign'],
            'real_estate': ['real estate', 'property', 'flat', 'ghar']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                if topic not in profile.topics_discussed:
                    profile.topics_discussed.append(topic)
        
        profile.conversation_count += 1
        profile.last_updated = datetime.now().isoformat()
        
        return insights
    
    def get_personalization_context(self, session_id: str) -> str:
        """
        Generate personalization context to inject into LLM prompts.
        """
        profile = self.get_or_create_profile(session_id)
        
        context_parts = []
        
        if profile.age_range:
            context_parts.append(f"User is in {profile.age_range} age group")
        
        if profile.family_status:
            status_map = {
                'single': 'single',
                'married': 'married',
                'married_with_kids': 'married with children'
            }
            context_parts.append(f"User is {status_map.get(profile.family_status, profile.family_status)}")
        
        if profile.goals:
            context_parts.append(f"User's financial goals: {', '.join(profile.goals)}")
        
        if profile.risk_appetite:
            context_parts.append(f"Risk appetite: {profile.risk_appetite}")
        
        if profile.financial_literacy:
            literacy_guidance = {
                'beginner': 'Explain concepts in very simple terms with examples',
                'intermediate': 'User has basic knowledge, can discuss comparisons',
                'advanced': 'User understands financial concepts well'
            }
            context_parts.append(literacy_guidance.get(profile.financial_literacy, ''))
        
        if profile.monthly_savings:
            context_parts.append(f"User saves approximately ₹{profile.monthly_savings:,.0f} per month")
        
        if profile.topics_discussed:
            context_parts.append(f"Previously discussed: {', '.join(profile.topics_discussed[-5:])}")
        
        return ". ".join(context_parts) if context_parts else ""
    
    def generate_chart_data(
        self, 
        chart_type: str,
        scenario: str,
        params: Dict[str, Any]
    ) -> Optional[ChartData]:
        """
        Generate chart data for visualization.
        
        Supported scenarios:
        - sip_growth: SIP investment growth over time
        - fd_vs_sip: Compare FD vs SIP returns
        - goal_planning: Track progress towards a goal
        - asset_allocation: Recommended portfolio allocation
        - loan_emi: EMI breakdown (principal vs interest)
        """
        
        if scenario == 'sip_growth':
            return self._generate_sip_growth_chart(params)
        elif scenario == 'fd_vs_sip':
            return self._generate_fd_vs_sip_chart(params)
        elif scenario == 'asset_allocation':
            return self._generate_allocation_chart(params)
        elif scenario == 'goal_planning':
            return self._generate_goal_chart(params)
        elif scenario == 'loan_emi':
            return self._generate_emi_chart(params)
        
        return None
    
    def _generate_sip_growth_chart(self, params: Dict[str, Any]) -> ChartData:
        """Generate SIP growth projection chart."""
        monthly_sip = params.get('monthly_amount', 5000)
        years = params.get('years', 10)
        expected_return = params.get('return_rate', 12) / 100
        
        labels = []
        invested = []
        value = []
        
        monthly_rate = expected_return / 12
        total_invested = 0
        current_value = 0
        
        for year in range(1, years + 1):
            for month in range(12):
                total_invested += monthly_sip
                current_value = (current_value + monthly_sip) * (1 + monthly_rate)
            
            labels.append(f"Year {year}")
            invested.append(total_invested)
            value.append(round(current_value))
        
        return ChartData(
            chart_type="line",
            title=f"SIP Growth: ₹{monthly_sip:,}/month @ {expected_return*100:.0f}% return",
            labels=labels,
            datasets=[
                {
                    "label": "Amount Invested",
                    "data": invested,
                    "borderColor": "#6b7280",
                    "backgroundColor": "rgba(107, 114, 128, 0.1)",
                    "fill": True
                },
                {
                    "label": "Portfolio Value",
                    "data": value,
                    "borderColor": "#ea580c",
                    "backgroundColor": "rgba(234, 88, 12, 0.1)",
                    "fill": True
                }
            ],
            options={
                "scales": {"y": {"beginAtZero": True}},
                "plugins": {"tooltip": {"callbacks": {"label": "₹{value}"}}}
            }
        )
    
    def _generate_fd_vs_sip_chart(self, params: Dict[str, Any]) -> ChartData:
        """Compare FD vs SIP returns."""
        amount = params.get('amount', 10000)
        years = params.get('years', 10)
        fd_rate = params.get('fd_rate', 7) / 100
        sip_rate = params.get('sip_rate', 12) / 100
        
        labels = []
        fd_values = []
        sip_values = []
        
        fd_value = 0
        sip_value = 0
        monthly_rate = sip_rate / 12
        
        for year in range(1, years + 1):
            # FD: Compound annually
            fd_value = (fd_value + amount * 12) * (1 + fd_rate)
            
            # SIP: Compound monthly
            for month in range(12):
                sip_value = (sip_value + amount) * (1 + monthly_rate)
            
            labels.append(f"Year {year}")
            fd_values.append(round(fd_value))
            sip_values.append(round(sip_value))
        
        return ChartData(
            chart_type="bar",
            title=f"FD ({fd_rate*100:.0f}%) vs SIP ({sip_rate*100:.0f}%) - ₹{amount:,}/month",
            labels=labels,
            datasets=[
                {
                    "label": f"FD @ {fd_rate*100:.0f}%",
                    "data": fd_values,
                    "backgroundColor": "#6b7280"
                },
                {
                    "label": f"SIP @ {sip_rate*100:.0f}%",
                    "data": sip_values,
                    "backgroundColor": "#ea580c"
                }
            ]
        )
    
    def _generate_allocation_chart(self, params: Dict[str, Any]) -> ChartData:
        """Generate recommended asset allocation pie chart."""
        risk_profile = params.get('risk_profile', 'moderate')
        age = params.get('age', 30)
        
        # Rule of thumb: 100 - age = equity allocation
        equity_pct = max(20, min(80, 100 - age))
        
        # Adjust based on risk profile
        if risk_profile == 'conservative':
            equity_pct = max(20, equity_pct - 20)
        elif risk_profile == 'aggressive':
            equity_pct = min(80, equity_pct + 15)
        
        debt_pct = 100 - equity_pct - 10  # Keep 10% in gold/others
        gold_pct = 10
        
        return ChartData(
            chart_type="pie",
            title=f"Recommended Asset Allocation ({risk_profile.title()} Profile)",
            labels=["Equity (Stocks/MF)", "Debt (FD/Bonds)", "Gold/Others"],
            datasets=[{
                "data": [equity_pct, debt_pct, gold_pct],
                "backgroundColor": ["#ea580c", "#6b7280", "#fbbf24"]
            }]
        )
    
    def _generate_goal_chart(self, params: Dict[str, Any]) -> ChartData:
        """Generate goal planning progress chart."""
        goal_amount = params.get('goal_amount', 1000000)
        current_savings = params.get('current_savings', 0)
        monthly_sip = params.get('monthly_sip', 10000)
        years = params.get('years', 5)
        return_rate = params.get('return_rate', 12) / 100
        
        labels = ['Current']
        values = [current_savings]
        
        monthly_rate = return_rate / 12
        value = current_savings
        
        for year in range(1, years + 1):
            for month in range(12):
                value = (value + monthly_sip) * (1 + monthly_rate)
            labels.append(f"Year {year}")
            values.append(round(value))
        
        return ChartData(
            chart_type="line",
            title=f"Goal: ₹{goal_amount:,} in {years} years",
            labels=labels,
            datasets=[
                {
                    "label": "Projected Savings",
                    "data": values,
                    "borderColor": "#ea580c",
                    "fill": False
                },
                {
                    "label": "Goal Amount",
                    "data": [goal_amount] * len(labels),
                    "borderColor": "#10b981",
                    "borderDash": [5, 5],
                    "fill": False
                }
            ],
            options={
                "plugins": {
                    "annotation": {
                        "annotations": {
                            "goalLine": {
                                "type": "line",
                                "yMin": goal_amount,
                                "yMax": goal_amount,
                                "borderColor": "#10b981",
                                "borderWidth": 2
                            }
                        }
                    }
                }
            }
        )
    
    def _generate_emi_chart(self, params: Dict[str, Any]) -> ChartData:
        """Generate loan EMI breakdown chart."""
        principal = params.get('principal', 1000000)
        rate = params.get('rate', 8.5) / 100 / 12
        tenure_months = params.get('tenure_years', 20) * 12
        
        # EMI calculation
        emi = principal * rate * (1 + rate)**tenure_months / ((1 + rate)**tenure_months - 1)
        
        total_payment = emi * tenure_months
        total_interest = total_payment - principal
        
        return ChartData(
            chart_type="pie",
            title=f"Loan EMI Breakdown (₹{emi:,.0f}/month)",
            labels=["Principal", "Interest"],
            datasets=[{
                "data": [round(principal), round(total_interest)],
                "backgroundColor": ["#10b981", "#ef4444"]
            }],
            options={
                "summary": {
                    "emi": round(emi),
                    "total_payment": round(total_payment),
                    "total_interest": round(total_interest)
                }
            }
        )
    
    def get_profile_dict(self, session_id: str) -> Dict[str, Any]:
        """Get profile as dictionary for JSON serialization."""
        profile = self.get_or_create_profile(session_id)
        return asdict(profile)
    
    def suggest_topics(self, session_id: str) -> List[str]:
        """Suggest relevant topics based on user profile."""
        profile = self.get_or_create_profile(session_id)
        suggestions = []
        
        # Based on goals
        goal_suggestions = {
            'retirement': ['NPS vs PPF comparison', 'Retirement corpus calculator'],
            'education': ['Sukanya Samriddhi Yojana', 'Education planning SIP'],
            'home': ['Home loan EMI calculator', 'Down payment saving strategy'],
            'emergency': ['Emergency fund building', 'Liquid funds vs savings account'],
            'wealth': ['Equity mutual funds', 'Direct stocks vs mutual funds'],
        }
        
        for goal in profile.goals:
            if goal in goal_suggestions:
                suggestions.extend(goal_suggestions[goal])
        
        # Based on literacy level
        if profile.financial_literacy == 'beginner':
            suggestions.extend(['What is SIP?', 'FD vs RD difference', 'Insurance basics'])
        elif profile.financial_literacy == 'intermediate':
            suggestions.extend(['Portfolio rebalancing', 'Tax saving investments', 'Index funds'])
        
        # Remove already discussed topics
        discussed_keywords = set()
        for topic in profile.topics_discussed:
            discussed_keywords.add(topic.lower())
        
        suggestions = [s for s in suggestions if not any(kw in s.lower() for kw in discussed_keywords)]
        
        return suggestions[:4]  # Return top 4 suggestions


# Global instance
user_intelligence = UserIntelligenceService()
