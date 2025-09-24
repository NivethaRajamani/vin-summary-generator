"""Unit tests for Anthropic Claude LLM service."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from src.vin_analyzer.utils.llm_service import LLMService
from src.vin_analyzer.models.vehicle import VehicleData, RiskFactors


class TestLLMService:
    """Test LLMService functionality."""

    @pytest.fixture
    def sample_vehicle(self):
        """Create sample vehicle data for testing."""
        return VehicleData(
            vin="1HGCM82633A123456",
            year=2018,
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("25000"),
            price_to_market_percent=95.0,
            days_on_lot=25,
            mileage=50000,
            total_vdps=150,
            sales_opportunities=5,
        )

    @pytest.fixture
    def sample_risk_factors(self):
        """Create sample risk factors for testing."""
        return RiskFactors(
            days_on_lot_impact=0,
            price_to_market_impact=-2,
            vdp_views_impact=0,
            mileage_impact=-1,
            sales_opportunities_impact=0,
            baseline_score=5,
            total_adjustments=-3,
            final_score=4,
        )

    def test_llm_service_init_with_api_key(self):
        """Test LLM service initialization with API key."""
        service = LLMService(api_key="test-key")
        assert service.api_key == "test-key"
        assert service.model == "claude-3-5-sonnet-20241022"

    def test_llm_service_init_without_api_key(self):
        """Test LLM service initialization without API key."""
        with pytest.raises(ValueError) as exc_info:
            LLMService()
        assert "Anthropic API key is required" in str(exc_info.value)

    def test_build_prompt(self, sample_vehicle, sample_risk_factors):
        """Test prompt building functionality."""
        service = LLMService(api_key="test-key")
        prompt = service._build_prompt(sample_vehicle, sample_risk_factors)

        # Check that prompt contains vehicle information
        assert "1HGCM82633A123456" in prompt
        assert "2018" in prompt
        assert "Honda" in prompt
        assert "Accord" in prompt
        assert "25,000" in prompt
        assert "95%" in prompt

        # Check that prompt contains risk factors
        assert "Days on Lot Impact: +0" in prompt
        assert "Price to Market Impact: -2" in prompt
        assert "Final Calculation: 4" in prompt or "Calculated Risk Score: 4" in prompt

        # Check that prompt contains instructions
        assert "JSON" in prompt
        assert "summary" in prompt
        assert "risk_score" in prompt
        assert "reasoning" in prompt

    def test_generate_fallback_assessment(self, sample_vehicle, sample_risk_factors):
        """Test fallback assessment generation."""
        service = LLMService(api_key="test-key")
        result = service._generate_fallback_assessment(
            sample_vehicle, sample_risk_factors
        )

        # Check required fields
        assert "summary" in result
        assert "risk_score" in result
        assert "reasoning" in result

        # Check data types and ranges
        assert isinstance(result["summary"], str)
        assert isinstance(result["risk_score"], int)
        assert isinstance(result["reasoning"], str)
        assert 1 <= result["risk_score"] <= 10

        # Check content quality
        assert len(result["summary"]) > 20
        assert len(result["reasoning"]) > 20
        assert "2018" in result["summary"]
        assert "Honda" in result["summary"]
        assert "Accord" in result["summary"]

    @patch("anthropic.Anthropic")
    def test_generate_risk_assessment_success(
        self, mock_anthropic, sample_vehicle, sample_risk_factors
    ):
        """Test successful LLM risk assessment generation."""
        # Mock Anthropic response
        mock_content = Mock()
        mock_content.text = """{
            "summary": "This 2018 Honda Accord represents a moderate market position.",
            "risk_score": 4,
            "reasoning": "Vehicle shows balanced risk factors with good pricing."
        }"""

        mock_response = Mock()
        mock_response.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        service = LLMService(api_key="test-key")
        result = service.generate_risk_assessment(sample_vehicle, sample_risk_factors)

        # Check that Anthropic was called
        mock_client.messages.create.assert_called_once()

        # Check result
        assert (
            result["summary"]
            == "This 2018 Honda Accord represents a moderate market position."
        )
        assert result["risk_score"] == 4
        assert (
            result["reasoning"]
            == "Vehicle shows balanced risk factors with good pricing."
        )

    @patch("anthropic.Anthropic")
    def test_generate_risk_assessment_api_failure(
        self, mock_anthropic, sample_vehicle, sample_risk_factors
    ):
        """Test LLM assessment generation with API failure."""
        # Mock Anthropic to raise an exception
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        service = LLMService(api_key="test-key")
        result = service.generate_risk_assessment(sample_vehicle, sample_risk_factors)

        # Should fall back to algorithmic generation
        assert "summary" in result
        assert "risk_score" in result
        assert "reasoning" in result
        assert 1 <= result["risk_score"] <= 10

    @patch("anthropic.Anthropic")
    def test_generate_risk_assessment_invalid_json(
        self, mock_anthropic, sample_vehicle, sample_risk_factors
    ):
        """Test handling of invalid JSON response from LLM."""
        # Mock Anthropic response with invalid JSON
        mock_content = Mock()
        mock_content.text = "Invalid JSON response"

        mock_response = Mock()
        mock_response.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        service = LLMService(api_key="test-key")
        result = service.generate_risk_assessment(sample_vehicle, sample_risk_factors)

        # Should fall back to algorithmic generation
        assert "summary" in result
        assert "risk_score" in result
        assert "reasoning" in result

    @patch("anthropic.Anthropic")
    def test_generate_risk_assessment_risk_score_bounds(
        self, mock_anthropic, sample_vehicle, sample_risk_factors
    ):
        """Test that risk scores are properly bounded."""
        # Mock Anthropic response with out-of-bounds risk score
        mock_content = Mock()
        mock_content.text = """{
            "summary": "Test summary",
            "risk_score": 15,
            "reasoning": "Test reasoning"
        }"""

        mock_response = Mock()
        mock_response.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        service = LLMService(api_key="test-key")
        result = service.generate_risk_assessment(sample_vehicle, sample_risk_factors)

        # Risk score should be clamped to 10
        assert result["risk_score"] == 10

    @patch("anthropic.Anthropic")
    def test_test_connection_success(self, mock_anthropic):
        """Test successful connection test."""
        mock_response = Mock()
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        service = LLMService(api_key="test-key")
        assert service.test_connection() is True

    @patch("anthropic.Anthropic")
    def test_test_connection_failure(self, mock_anthropic):
        """Test failed connection test."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("Connection failed")
        mock_anthropic.return_value = mock_client

        service = LLMService(api_key="test-key")
        assert service.test_connection() is False
