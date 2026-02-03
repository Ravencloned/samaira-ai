"""
Tests for Intent Detection
"""

import pytest
from backend.core.intent import (
    detect_intent,
    IntentType,
    IntentResult,
    extract_entities
)


class TestBasicIntentDetection:
    """Tests for basic intent detection"""
    
    def test_greeting_intent(self):
        """Test greeting detection"""
        queries = [
            "Namaste",
            "Hello",
            "Hi",
            "Namaskar",
            "Hey"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.GREETING, f"Greeting not detected: {query}"
            
    def test_sip_intent(self):
        """Test SIP related intent"""
        queries = [
            "SIP kya hota hai",
            "SIP ke baare mein batao",
            "Systematic investment plan samjhao",
            "SIP kaise start karein"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.SIP_QUERY, f"SIP intent not detected: {query}"
            
    def test_rd_intent(self):
        """Test RD related intent"""
        queries = [
            "RD kya hai",
            "Recurring deposit samjhao",
            "RD mein interest kitna milta hai"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.RD_QUERY, f"RD intent not detected: {query}"
            
    def test_fd_intent(self):
        """Test FD related intent"""
        queries = [
            "FD ke baare mein batao",
            "Fixed deposit kya hota hai",
            "FD mein paisa lagana hai"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.FD_QUERY, f"FD intent not detected: {query}"
            
    def test_ppf_intent(self):
        """Test PPF related intent"""
        queries = [
            "PPF kya hai",
            "Public provident fund samjhao",
            "PPF mein invest karna hai"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.PPF_QUERY, f"PPF intent not detected: {query}"


class TestComparisonIntent:
    """Tests for comparison intent detection"""
    
    def test_sip_vs_rd_comparison(self):
        """Test SIP vs RD comparison"""
        queries = [
            "SIP aur RD mein kya difference hai",
            "SIP vs RD",
            "SIP better hai ya RD",
            "RD aur SIP compare karo"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.COMPARISON, f"Comparison not detected: {query}"
            
    def test_fd_vs_rd_comparison(self):
        """Test FD vs RD comparison"""
        queries = [
            "FD better hai ya RD",
            "FD aur RD mein difference",
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.COMPARISON


class TestGoalIntent:
    """Tests for goal-based intent detection"""
    
    def test_child_education_goal(self):
        """Test child education goal detection"""
        queries = [
            "Bachhe ki padhai ke liye planning karni hai",
            "Bete ki education ke liye save karna hai",
            "Child education fund banana hai",
            "Bachhe ke college ke liye paisa"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.GOAL_PLANNING, f"Goal not detected: {query}"
            
    def test_wedding_goal(self):
        """Test wedding goal detection"""
        queries = [
            "Beti ki shadi ke liye paisa bachana hai",
            "Wedding ke liye save karna hai",
            "Daughter marriage planning"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.GOAL_PLANNING
            
    def test_home_goal(self):
        """Test home purchase goal detection"""
        queries = [
            "Ghar lena hai down payment ke liye",
            "Home ke liye save karna hai",
            "Apna makan banana hai"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.GOAL_PLANNING
            
    def test_retirement_goal(self):
        """Test retirement goal detection"""
        queries = [
            "Retirement ke liye planning",
            "Budhape ke liye paisa",
            "Pension ke liye invest"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.GOAL_PLANNING


class TestCalculationIntent:
    """Tests for calculation intent detection"""
    
    def test_sip_calculation(self):
        """Test SIP calculation request"""
        queries = [
            "5000 ki SIP 10 saal mein kitna banega",
            "10000 monthly SIP ka return calculate karo",
            "SIP se 20 lakh kaise banaoon"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.CALCULATION
            
    def test_goal_calculation(self):
        """Test goal calculation request"""
        queries = [
            "25 lakh ke liye kitni SIP karni padegi",
            "10 saal mein 50 lakh kaise banayein",
            "20 lakh corpus ke liye monthly kitna invest"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.CALCULATION


class TestEntityExtraction:
    """Tests for entity extraction from queries"""
    
    def test_amount_extraction(self):
        """Test amount extraction"""
        queries_amounts = [
            ("5000 ki SIP karni hai", 5000),
            ("10000 monthly invest", 10000),
            ("₹15000 lagana hai", 15000),
            ("5 lakh ka FD", 500000),
            ("25 lakh chahiye", 2500000),
        ]
        
        for query, expected in queries_amounts:
            entities = extract_entities(query)
            assert entities.get("amount") == expected or \
                   entities.get("target_amount") == expected, \
                   f"Amount not extracted from: {query}"
                   
    def test_duration_extraction(self):
        """Test duration/years extraction"""
        queries_years = [
            ("10 saal ke liye", 10),
            ("5 years mein", 5),
            ("15 varsh", 15),
            ("20 years ke baad", 20),
        ]
        
        for query, expected in queries_years:
            entities = extract_entities(query)
            assert entities.get("years") == expected or \
                   entities.get("duration") == expected, \
                   f"Duration not extracted from: {query}"
                   
    def test_percentage_extraction(self):
        """Test percentage/rate extraction"""
        queries_rates = [
            ("12% return chahiye", 12),
            ("10 percent interest", 10),
            ("7.5% rate", 7.5),
        ]
        
        for query, expected in queries_rates:
            entities = extract_entities(query)
            assert entities.get("rate") == expected or \
                   entities.get("return_rate") == expected, \
                   f"Rate not extracted from: {query}"


class TestAmbiguousQueries:
    """Tests for ambiguous or complex queries"""
    
    def test_multiple_products_mentioned(self):
        """Test when multiple products are mentioned"""
        query = "SIP, RD, FD sab mein kya difference hai"
        result = detect_intent(query)
        
        # Should detect comparison intent
        assert result.intent == IntentType.COMPARISON
        
    def test_vague_investment_query(self):
        """Test vague investment queries"""
        queries = [
            "Paisa kahan lagaoon",
            "Investment kaise karein",
            "Savings kaise karein"
        ]
        
        for query in queries:
            result = detect_intent(query)
            # Should not crash, should give some intent
            assert result.intent is not None
            
    def test_scheme_info_query(self):
        """Test government scheme info queries"""
        queries = [
            "Sukanya samriddhi yojana kya hai",
            "NPS ke baare mein batao",
            "PMJJBY scheme samjhao"
        ]
        
        for query in queries:
            result = detect_intent(query)
            assert result.intent == IntentType.SCHEME_INFO


class TestIntentConfidence:
    """Tests for intent confidence scores"""
    
    def test_clear_intent_high_confidence(self):
        """Test that clear queries have high confidence"""
        result = detect_intent("SIP kya hota hai")
        assert result.confidence >= 0.7
        
    def test_vague_query_lower_confidence(self):
        """Test that vague queries have lower confidence"""
        result = detect_intent("kuch batao")
        assert result.confidence < 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
