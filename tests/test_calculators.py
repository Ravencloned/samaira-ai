"""
Tests for Financial Calculators
"""

import pytest
from backend.financial.calculators import (
    calculate_sip,
    calculate_rd,
    calculate_fd,
    calculate_ppf,
    calculate_ssy,
    compare_sip_vs_rd,
    calculate_goal_corpus
)


class TestSIPCalculator:
    """Tests for SIP calculator"""
    
    def test_basic_sip(self):
        """Test basic SIP calculation"""
        result = calculate_sip(
            monthly_amount=5000,
            years=10,
            expected_return=12
        )
        
        assert result["monthly_investment"] == 5000
        assert result["total_invested"] == 600000  # 5000 * 12 * 10
        assert result["maturity_value"] > result["total_invested"]
        assert result["rate_of_return"] == 12
        
    def test_sip_short_term(self):
        """Test SIP for short term"""
        result = calculate_sip(
            monthly_amount=10000,
            years=1,
            expected_return=12
        )
        
        assert result["total_invested"] == 120000
        assert result["maturity_value"] > 120000
        
    def test_sip_long_term(self):
        """Test SIP for long term shows power of compounding"""
        result_5yr = calculate_sip(5000, 5, 12)
        result_20yr = calculate_sip(5000, 20, 12)
        
        # 20yr returns should be much more than 4x of 5yr returns
        ratio = result_20yr["total_returns"] / result_5yr["total_returns"]
        assert ratio > 4


class TestRDCalculator:
    """Tests for RD calculator"""
    
    def test_basic_rd(self):
        """Test basic RD calculation"""
        result = calculate_rd(
            monthly_amount=5000,
            years=5,
            interest_rate=6.5
        )
        
        assert result["monthly_deposit"] == 5000
        assert result["total_invested"] == 300000
        assert result["maturity_value"] > 300000
        
    def test_rd_vs_sip_returns(self):
        """RD should have lower returns than SIP for same amount"""
        sip = calculate_sip(5000, 10, 12)
        rd = calculate_rd(5000, 10, 6.5)
        
        assert sip["maturity_value"] > rd["maturity_value"]


class TestFDCalculator:
    """Tests for FD calculator"""
    
    def test_basic_fd(self):
        """Test basic FD calculation"""
        result = calculate_fd(
            principal=100000,
            years=5,
            interest_rate=7
        )
        
        assert result["principal"] == 100000
        assert result["maturity_value"] > 100000
        
    def test_fd_interest_accumulation(self):
        """Test FD interest is compounded annually"""
        result = calculate_fd(100000, 1, 7)
        # After 1 year at 7%, should be ~107000
        assert 106000 < result["maturity_value"] < 108000


class TestPPFCalculator:
    """Tests for PPF calculator"""
    
    def test_basic_ppf(self):
        """Test basic PPF calculation"""
        result = calculate_ppf(
            yearly_amount=150000,  # Max PPF limit
            years=15
        )
        
        assert result["yearly_investment"] == 150000
        assert result["total_invested"] == 2250000
        assert result["maturity_value"] > 2250000
        
    def test_ppf_with_custom_rate(self):
        """Test PPF with custom rate"""
        result = calculate_ppf(100000, 15, interest_rate=8.0)
        assert result["rate_of_return"] == 8.0


class TestSSYCalculator:
    """Tests for Sukanya Samriddhi Yojana calculator"""
    
    def test_basic_ssy(self):
        """Test basic SSY calculation"""
        result = calculate_ssy(
            yearly_amount=150000,
            current_age=5
        )
        
        assert result["yearly_investment"] == 150000
        assert "maturity_value" in result


class TestComparisons:
    """Tests for comparison functions"""
    
    def test_sip_vs_rd_comparison(self):
        """Test SIP vs RD comparison"""
        result = compare_sip_vs_rd(
            monthly_amount=5000,
            years=10
        )
        
        assert "sip" in result
        assert "rd" in result
        assert "difference" in result
        assert result["sip"]["maturity_value"] > result["rd"]["maturity_value"]
        
    def test_comparison_hinglish_summary(self):
        """Test that comparison includes Hinglish summary"""
        result = compare_sip_vs_rd(5000, 10)
        assert "summary_hinglish" in result
        assert "lakh" in result["summary_hinglish"].lower() or "₹" in result["summary_hinglish"]


class TestGoalCalculator:
    """Tests for goal corpus calculator"""
    
    def test_goal_corpus_calculation(self):
        """Test goal corpus calculation"""
        result = calculate_goal_corpus(
            target_amount=2500000,  # 25 lakh
            years=10,
            expected_return=12
        )
        
        assert "monthly_sip_required" in result
        assert result["monthly_sip_required"] > 0
        assert result["target_amount"] == 2500000
        
    def test_goal_with_existing_corpus(self):
        """Test goal with existing investments"""
        result = calculate_goal_corpus(
            target_amount=2500000,
            years=10,
            expected_return=12,
            existing_corpus=500000
        )
        
        # With existing corpus, monthly SIP should be lower
        result_no_corpus = calculate_goal_corpus(2500000, 10, 12)
        
        assert result["monthly_sip_required"] < result_no_corpus["monthly_sip_required"]


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_zero_amount(self):
        """Test with zero amount"""
        result = calculate_sip(0, 10, 12)
        assert result["maturity_value"] == 0
        
    def test_zero_years(self):
        """Test with zero years"""
        result = calculate_sip(5000, 0, 12)
        assert result["maturity_value"] == 0
        
    def test_high_return_rate(self):
        """Test with high return rate"""
        result = calculate_sip(5000, 10, 25)
        assert result["maturity_value"] > 0
        
    def test_decimal_values(self):
        """Test with decimal values"""
        result = calculate_sip(5000.50, 10, 12.5)
        assert result["maturity_value"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
