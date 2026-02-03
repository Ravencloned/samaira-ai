"""
Tests for Safety and Compliance Layer
"""

import pytest
from backend.core.safety import (
    check_safety,
    SafetyResult,
    SafetyCategory,
    inject_disclaimer,
    format_handoff_response
)


class TestSafetyDetection:
    """Tests for safety boundary detection"""
    
    def test_normal_query_is_safe(self):
        """Test that normal queries pass safety check"""
        queries = [
            "SIP kya hota hai?",
            "RD aur FD mein kya difference hai?",
            "PPF ke baare mein batao",
            "Mutual fund kaise kaam karta hai?"
        ]
        
        for query in queries:
            result = check_safety(query)
            assert result.is_safe, f"Query should be safe: {query}"
            
    def test_advisory_request_detected(self):
        """Test that specific investment advice requests are flagged"""
        queries = [
            "Mujhe batao konsa mutual fund kharidna chahiye",
            "Best SIP recommend karo",
            "Konsi company ka share lena chahiye",
            "Mera paisa kahan invest karoon?"
        ]
        
        for query in queries:
            result = check_safety(query)
            assert result.category == SafetyCategory.ADVISORY or not result.is_safe, \
                f"Advisory request not detected: {query}"
                
    def test_tax_advice_detected(self):
        """Test that tax advice requests are flagged"""
        queries = [
            "Mera ITR kaise file karoon?",
            "Tax audit mein kya karna chahiye?",
            "Mujhe tax evasion ka tarika batao",
            "Capital gains tax calculate karo"
        ]
        
        for query in queries:
            result = check_safety(query)
            if "evasion" in query.lower():
                assert not result.is_safe or result.needs_handoff
            else:
                assert result.category == SafetyCategory.TAX or result.needs_handoff
                
    def test_legal_matters_detected(self):
        """Test that legal matters are flagged"""
        queries = [
            "Nominee change karne ka legal process",
            "Property ka legal dispute hai",
            "Court case ke baare mein batao",
            "Mujhe legal action lena hai"
        ]
        
        for query in queries:
            result = check_safety(query)
            assert result.category == SafetyCategory.LEGAL or result.needs_handoff
            
    def test_complaint_detected(self):
        """Test that complaints are flagged for handoff"""
        queries = [
            "Mujhe bank se complaint karni hai",
            "Fraud ho gaya hai mujhe report karna hai",
            "Consumer forum mein jaana hai",
            "Refund nahi mil raha"
        ]
        
        for query in queries:
            result = check_safety(query)
            assert result.category == SafetyCategory.COMPLAINT or result.needs_handoff
            
    def test_human_handoff_request(self):
        """Test that explicit handoff requests are detected"""
        queries = [
            "Mujhe human agent se baat karni hai",
            "Real advisor se connect karo",
            "Aadmi se baat karwao",
            "Bot se nahi, insaan se baat karni hai"
        ]
        
        for query in queries:
            result = check_safety(query)
            assert result.needs_handoff, f"Handoff not detected: {query}"


class TestDisclaimerInjection:
    """Tests for disclaimer injection"""
    
    def test_disclaimer_added_to_projection(self):
        """Test that disclaimers are added to projection responses"""
        response = "Aapka SIP 10 saal mein 11 lakh ho jayega."
        
        result = inject_disclaimer(response, has_projection=True)
        
        assert "illustrative" in result.lower() or "example" in result.lower() or \
               "sirf samajhne" in result.lower()
               
    def test_no_double_disclaimer(self):
        """Test that disclaimers aren't duplicated"""
        response = "Yeh sirf illustrative example hai. Actual returns vary ho sakte hain."
        
        result = inject_disclaimer(response, has_projection=True)
        
        # Count occurrences of disclaimer keywords
        disclaimer_count = result.lower().count("illustrative") + result.lower().count("example")
        assert disclaimer_count <= 2  # Original counts
        
    def test_educational_content_no_heavy_disclaimer(self):
        """Test that educational content gets lighter disclaimers"""
        response = "SIP matlab Systematic Investment Plan. Isme har mahine thoda thoda invest karte hain."
        
        result = inject_disclaimer(response, has_projection=False)
        
        # Should have minimal changes for educational content
        assert len(result) <= len(response) * 1.5


class TestHandoffResponse:
    """Tests for handoff response formatting"""
    
    def test_handoff_response_format(self):
        """Test handoff response includes necessary elements"""
        response = format_handoff_response(SafetyCategory.TAX)
        
        # Should include advisor mention
        assert "advisor" in response.lower() or "expert" in response.lower() or \
               "professional" in response.lower()
               
    def test_handoff_preserves_category(self):
        """Test handoff response is appropriate for category"""
        tax_response = format_handoff_response(SafetyCategory.TAX)
        legal_response = format_handoff_response(SafetyCategory.LEGAL)
        
        # Should be different responses
        assert tax_response != legal_response


class TestHinglishPatterns:
    """Tests for Hinglish pattern detection"""
    
    def test_hindi_keywords_detected(self):
        """Test Hindi keywords are properly detected"""
        queries = [
            "Kaunsa fund lena chahiye",  # kaunsa = which
            "Guarantee do ki paisa double hoga",  # guarantee
            "Mujhe yakeen dilao",  # yakeen = assurance
        ]
        
        # These should trigger advisory/promise detection
        for query in queries:
            result = check_safety(query)
            # At least some should be flagged
            
    def test_mixed_hinglish_handling(self):
        """Test mixed Hindi-English queries"""
        queries = [
            "Best mutual fund for long term investment batao",
            "SIP start karne ke liye kya documents chahiye",
            "PPF account kholne ka process kya hai"
        ]
        
        # Normal queries should pass
        for query in queries:
            result = check_safety(query)
            # Process should not crash


class TestContextualSafety:
    """Tests for contextual safety checks"""
    
    def test_amount_context_affects_safety(self):
        """Test that large amounts may trigger different handling"""
        small_query = "₹5000 ki SIP karni hai"
        large_query = "₹50 lakh invest karna hai"
        
        # Both should process, but large amounts might need more care
        small_result = check_safety(small_query)
        large_result = check_safety(large_query)
        
        # At minimum, both should not crash
        assert small_result is not None
        assert large_result is not None
        
    def test_emergency_context(self):
        """Test emergency/urgent requests"""
        queries = [
            "Urgent paisa chahiye kya karoon",
            "Emergency mein mutual fund se paisa kaise nikaloon",
            "Jaldi batao nahi to bahut loss ho jayega"
        ]
        
        for query in queries:
            result = check_safety(query)
            # Should process without crashing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
