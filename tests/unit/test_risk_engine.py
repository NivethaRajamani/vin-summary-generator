"""Unit tests for risk engine."""

import pytest
from decimal import Decimal
from datetime import datetime

from src.vin_analyzer.core.risk_engine import RiskEngine
from src.vin_analyzer.models.vehicle import VehicleData, RiskAssessment


class TestRiskEngine:
    """Test RiskEngine functionality."""

    @pytest.fixture
    def risk_engine(self):
        """Create RiskEngine instance for testing (without LLM)."""
        return RiskEngine(use_llm=False)

    @pytest.fixture
    def risk_engine_with_llm(self):
        """Create RiskEngine instance with LLM for testing."""
        return RiskEngine(use_llm=True, anthropic_api_key="test-key")

    @pytest.fixture
    def sample_vehicle_low_risk(self):
        """Create sample vehicle data with low risk characteristics."""
        return VehicleData(
            vin="1HGCM82633A123456",
            year=2023,  # Recent year
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("25000"),
            price_to_market_percent=90.0,  # Below market
            days_on_lot=10,  # Low days on lot
            mileage=15000,  # Low mileage for age
            total_vdps=250,  # High views
            sales_opportunities=15,  # Many opportunities
        )

    @pytest.fixture
    def sample_vehicle_high_risk(self):
        """Create sample vehicle data with high risk characteristics."""
        return VehicleData(
            vin="2HGCM82633A123457",
            year=2018,  # Older year
            make="NISSAN",
            model="ALTIMA",
            current_price=Decimal("35000"),
            price_to_market_percent=110.0,  # Above market
            days_on_lot=60,  # High days on lot
            mileage=120000,  # High mileage for age
            total_vdps=30,  # Low views
            sales_opportunities=1,  # Few opportunities
        )

    @pytest.fixture
    def sample_vehicle_new_car(self):
        """Create sample vehicle data for new car."""
        return VehicleData(
            vin="3HGCM82633A123458",
            year=2025,  # New car
            make="TOYOTA",
            model="CAMRY",
            current_price=Decimal("30000"),
            price_to_market_percent=100.0,  # At market
            days_on_lot=5,  # Very new
            mileage=0,  # New car mileage
            total_vdps=100,  # Moderate views
            sales_opportunities=3,  # Moderate opportunities
        )

    def test_calculate_days_on_lot_impact(self, risk_engine):
        """Test days on lot impact calculation."""
        # Low days on lot
        assert risk_engine._calculate_days_on_lot_impact(10) == -2

        # Moderate days on lot
        assert risk_engine._calculate_days_on_lot_impact(25) == 0
        assert risk_engine._calculate_days_on_lot_impact(45) == 0

        # High days on lot
        assert risk_engine._calculate_days_on_lot_impact(60) == 2

    def test_calculate_price_to_market_impact(self, risk_engine):
        """Test price to market impact calculation."""
        # Below market
        assert risk_engine._calculate_price_to_market_impact(90.0) == -2

        # At/near market
        assert risk_engine._calculate_price_to_market_impact(96.0) == 0
        assert risk_engine._calculate_price_to_market_impact(100.0) == 0
        assert risk_engine._calculate_price_to_market_impact(105.0) == 0

        # Above market
        assert risk_engine._calculate_price_to_market_impact(110.0) == 2

    def test_calculate_vdp_views_impact(self, risk_engine):
        """Test VDP views impact calculation."""
        # High views
        assert risk_engine._calculate_vdp_views_impact(250) == -1

        # Moderate views
        assert risk_engine._calculate_vdp_views_impact(100) == 0
        assert risk_engine._calculate_vdp_views_impact(150) == 0

        # Low views
        assert risk_engine._calculate_vdp_views_impact(30) == 1

    def test_calculate_mileage_impact_new_vehicle(
        self, risk_engine, sample_vehicle_new_car
    ):
        """Test mileage impact for new vehicle."""
        # New vehicles (0 mileage) should have low risk
        assert risk_engine._calculate_mileage_impact(sample_vehicle_new_car) == -1

    def test_calculate_mileage_impact_used_vehicle(self, risk_engine):
        """Test mileage impact for used vehicles."""
        # Create test vehicle with specific mileage scenarios
        current_year = datetime.now().year

        # Below average mileage (5 year old car with 30k miles vs expected 60k)
        vehicle_low_mileage = VehicleData(
            vin="1HGCM82633A123456",
            year=current_year - 5,
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("25000"),
            price_to_market_percent=100.0,
            days_on_lot=25,
            mileage=30000,  # Below 12k/year average
            total_vdps=100,
            sales_opportunities=5,
        )
        assert risk_engine._calculate_mileage_impact(vehicle_low_mileage) == -1

        # Above average mileage (5 year old car with 100k miles vs expected 60k)
        vehicle_high_mileage = VehicleData(
            vin="1HGCM82633A123456",
            year=current_year - 5,
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("25000"),
            price_to_market_percent=100.0,
            days_on_lot=25,
            mileage=100000,  # Above 12k/year average
            total_vdps=100,
            sales_opportunities=5,
        )
        assert risk_engine._calculate_mileage_impact(vehicle_high_mileage) == 1

    def test_calculate_sales_opportunities_impact(self, risk_engine):
        """Test sales opportunities impact calculation."""
        # Many opportunities
        assert risk_engine._calculate_sales_opportunities_impact(15) == -1

        # Few opportunities
        assert risk_engine._calculate_sales_opportunities_impact(1) == 1
        assert risk_engine._calculate_sales_opportunities_impact(2) == 1

        # Moderate opportunities
        assert risk_engine._calculate_sales_opportunities_impact(5) == 0

    def test_handle_missing_data_adjustments(self, risk_engine):
        """Test missing data adjustments."""
        # Vehicle with zero price
        vehicle_zero_price = VehicleData(
            vin="1HGCM82633A123456",
            year=2020,
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("0"),  # Missing price
            price_to_market_percent=0.0,  # Missing price to market
            days_on_lot=150,  # High days on lot
            mileage=50000,
            total_vdps=100,
            sales_opportunities=5,
        )

        adjustment = risk_engine._handle_missing_data_adjustments(vehicle_zero_price)
        assert adjustment >= 1  # Should increase risk

    def test_calculate_risk_factors_low_risk(
        self, risk_engine, sample_vehicle_low_risk
    ):
        """Test risk factor calculation for low risk vehicle."""
        factors = risk_engine.calculate_risk_factors(sample_vehicle_low_risk)

        assert factors.baseline_score == 5
        assert factors.days_on_lot_impact == -2  # Low days on lot
        assert factors.price_to_market_impact == -2  # Below market
        assert factors.vdp_views_impact == -1  # High views
        assert factors.mileage_impact == -1  # New vehicle
        assert factors.sales_opportunities_impact == -1  # Many opportunities
        assert factors.final_score >= 1  # Should be low risk

    def test_calculate_risk_factors_high_risk(
        self, risk_engine, sample_vehicle_high_risk
    ):
        """Test risk factor calculation for high risk vehicle."""
        factors = risk_engine.calculate_risk_factors(sample_vehicle_high_risk)

        assert factors.baseline_score == 5
        assert factors.days_on_lot_impact == 2  # High days on lot
        assert factors.price_to_market_impact == 2  # Above market
        assert factors.vdp_views_impact == 1  # Low views
        assert factors.sales_opportunities_impact == 1  # Few opportunities
        assert factors.final_score >= 6  # Should be high risk

    def test_assess_risk_returns_valid_assessment(
        self, risk_engine, sample_vehicle_low_risk
    ):
        """Test that assess_risk returns valid RiskAssessment."""
        assessment = risk_engine.assess_risk(sample_vehicle_low_risk)

        assert isinstance(assessment, RiskAssessment)
        assert 1 <= assessment.risk_score <= 10
        assert len(assessment.summary) > 0
        assert len(assessment.reasoning) > 0

    def test_generate_summary_content(self, risk_engine, sample_vehicle_low_risk):
        """Test that generated summary contains expected content."""
        factors = risk_engine.calculate_risk_factors(sample_vehicle_low_risk)
        summary = risk_engine._generate_summary(sample_vehicle_low_risk, factors)

        # Should contain vehicle information
        assert "2023" in summary
        assert "Honda" in summary
        assert "Accord" in summary

        # Should contain market analysis
        assert any(
            term in summary.lower()
            for term in ["priced", "engagement", "risk", "investment", "position"]
        )

    def test_generate_reasoning_content(self, risk_engine, sample_vehicle_low_risk):
        """Test that generated reasoning contains expected content."""
        factors = risk_engine.calculate_risk_factors(sample_vehicle_low_risk)
        reasoning = risk_engine._generate_reasoning(sample_vehicle_low_risk, factors)

        # Should contain analysis of all factors
        assert "Days on lot" in reasoning
        assert "Price is" in reasoning or "Price to market" in reasoning
        assert "VDP views" in reasoning
        assert "miles" in reasoning or "Mileage" in reasoning
        assert "opportunities" in reasoning
        assert "Overall score" in reasoning

    def test_score_clamping(self, risk_engine):
        """Test that risk scores are properly clamped between 1 and 10."""
        # Create extreme low risk vehicle
        extreme_low_risk = VehicleData(
            vin="1HGCM82633A123456",
            year=2025,  # New
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("20000"),
            price_to_market_percent=80.0,  # Well below market
            days_on_lot=5,  # Very low
            mileage=0,  # New
            total_vdps=500,  # Very high views
            sales_opportunities=20,  # Many opportunities
        )

        factors = risk_engine.calculate_risk_factors(extreme_low_risk)
        assert factors.final_score >= 1

        # Create extreme high risk vehicle
        extreme_high_risk = VehicleData(
            vin="2HGCM82633A123457",
            year=2015,  # Old
            make="NISSAN",
            model="ALTIMA",
            current_price=Decimal("40000"),
            price_to_market_percent=150.0,  # Well above market
            days_on_lot=200,  # Very high
            mileage=200000,  # Very high mileage
            total_vdps=5,  # Very low views
            sales_opportunities=0,  # No opportunities
        )

        factors = risk_engine.calculate_risk_factors(extreme_high_risk)
        assert factors.final_score <= 10

    def test_baseline_score_constant(self, risk_engine):
        """Test that baseline score is consistent."""
        assert risk_engine.BASELINE_SCORE == 5
        assert risk_engine.MIN_SCORE == 1
        assert risk_engine.MAX_SCORE == 10

    def test_llm_fallback_functionality(self, sample_vehicle_low_risk):
        """Test that LLM fallback works when LLM fails."""
        # Create engine with invalid API key to force fallback
        engine = RiskEngine(use_llm=True, anthropic_api_key="invalid-key")

        # Should fall back to algorithmic generation
        assessment = engine.assess_risk(sample_vehicle_low_risk)

        assert isinstance(assessment, RiskAssessment)
        assert 1 <= assessment.risk_score <= 10
        assert len(assessment.summary) > 0
        assert len(assessment.reasoning) > 0

    def test_llm_disabled_functionality(self, sample_vehicle_low_risk):
        """Test that engine works when LLM is disabled."""
        engine = RiskEngine(use_llm=False)

        assessment = engine.assess_risk(sample_vehicle_low_risk)

        assert isinstance(assessment, RiskAssessment)
        assert 1 <= assessment.risk_score <= 10
        assert len(assessment.summary) > 0
        assert len(assessment.reasoning) > 0
