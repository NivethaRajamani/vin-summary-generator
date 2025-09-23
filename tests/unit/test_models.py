"""Unit tests for data models."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from src.vin_analyzer.models.vehicle import (
    VehicleData,
    RiskAssessment,
    VinRequest,
    RiskFactors,
    VehicleNotFoundError
)


class TestVehicleData:
    """Test VehicleData model validation."""

    def test_valid_vehicle_data(self):
        """Test creation of valid vehicle data."""
        vehicle = VehicleData(
            vin="1HGCM82633A123456",
            year=2018,
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("25000.00"),
            price_to_market_percent=95.5,
            days_on_lot=25,
            mileage=50000,
            total_vdps=150,
            sales_opportunities=5
        )

        assert vehicle.vin == "1HGCM82633A123456"
        assert vehicle.year == 2018
        assert vehicle.make == "HONDA"
        assert vehicle.model == "ACCORD"
        assert vehicle.current_price == Decimal("25000.00")
        assert vehicle.price_to_market_percent == 95.5
        assert vehicle.days_on_lot == 25
        assert vehicle.mileage == 50000
        assert vehicle.total_vdps == 150
        assert vehicle.sales_opportunities == 5

    def test_vin_validation_uppercase(self):
        """Test VIN is converted to uppercase."""
        vehicle = VehicleData(
            vin="1hgcm82633a123456",
            year=2018,
            make="HONDA",
            model="ACCORD",
            current_price=Decimal("25000.00"),
            price_to_market_percent=95.5,
            days_on_lot=25,
            mileage=50000,
            total_vdps=150,
            sales_opportunities=5
        )

        assert vehicle.vin == "1HGCM82633A123456"

    def test_vin_validation_length(self):
        """Test VIN length validation."""
        with pytest.raises(ValidationError) as exc_info:
            VehicleData(
                vin="SHORT",
                year=2018,
                make="HONDA",
                model="ACCORD",
                current_price=Decimal("25000.00"),
                price_to_market_percent=95.5,
                days_on_lot=25,
                mileage=50000,
                total_vdps=150,
                sales_opportunities=5
            )

        assert "VIN must be exactly 17 characters" in str(exc_info.value)

    def test_year_validation_range(self):
        """Test year validation range."""
        # Test lower bound
        with pytest.raises(ValidationError) as exc_info:
            VehicleData(
                vin="1HGCM82633A123456",
                year=1979,
                make="HONDA",
                model="ACCORD",
                current_price=Decimal("25000.00"),
                price_to_market_percent=95.5,
                days_on_lot=25,
                mileage=50000,
                total_vdps=150,
                sales_opportunities=5
            )

        assert "Year must be between 1980 and 2030" in str(exc_info.value)

        # Test upper bound
        with pytest.raises(ValidationError) as exc_info:
            VehicleData(
                vin="1HGCM82633A123456",
                year=2031,
                make="HONDA",
                model="ACCORD",
                current_price=Decimal("25000.00"),
                price_to_market_percent=95.5,
                days_on_lot=25,
                mileage=50000,
                total_vdps=150,
                sales_opportunities=5
            )

        assert "Year must be between 1980 and 2030" in str(exc_info.value)

    def test_price_validation_negative(self):
        """Test price validation for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            VehicleData(
                vin="1HGCM82633A123456",
                year=2018,
                make="HONDA",
                model="ACCORD",
                current_price=Decimal("-1000.00"),
                price_to_market_percent=95.5,
                days_on_lot=25,
                mileage=50000,
                total_vdps=150,
                sales_opportunities=5
            )

        assert "Price must be non-negative" in str(exc_info.value)

    def test_days_on_lot_validation_negative(self):
        """Test days on lot validation for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            VehicleData(
                vin="1HGCM82633A123456",
                year=2018,
                make="HONDA",
                model="ACCORD",
                current_price=Decimal("25000.00"),
                price_to_market_percent=95.5,
                days_on_lot=-5,
                mileage=50000,
                total_vdps=150,
                sales_opportunities=5
            )

        assert "Days on lot must be non-negative" in str(exc_info.value)

    def test_mileage_validation_negative(self):
        """Test mileage validation for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            VehicleData(
                vin="1HGCM82633A123456",
                year=2018,
                make="HONDA",
                model="ACCORD",
                current_price=Decimal("25000.00"),
                price_to_market_percent=95.5,
                days_on_lot=25,
                mileage=-1000,
                total_vdps=150,
                sales_opportunities=5
            )

        assert "Mileage must be non-negative" in str(exc_info.value)


class TestRiskAssessment:
    """Test RiskAssessment model."""

    def test_valid_risk_assessment(self):
        """Test creation of valid risk assessment."""
        assessment = RiskAssessment(
            summary="Test vehicle summary",
            risk_score=5,
            reasoning="Test reasoning"
        )

        assert assessment.summary == "Test vehicle summary"
        assert assessment.risk_score == 5
        assert assessment.reasoning == "Test reasoning"

    def test_risk_score_bounds(self):
        """Test risk score bounds validation."""
        # Test lower bound
        with pytest.raises(ValidationError):
            RiskAssessment(
                summary="Test summary",
                risk_score=0,
                reasoning="Test reasoning"
            )

        # Test upper bound
        with pytest.raises(ValidationError):
            RiskAssessment(
                summary="Test summary",
                risk_score=11,
                reasoning="Test reasoning"
            )

        # Test valid bounds
        assessment_low = RiskAssessment(
            summary="Test summary",
            risk_score=1,
            reasoning="Test reasoning"
        )
        assert assessment_low.risk_score == 1

        assessment_high = RiskAssessment(
            summary="Test summary",
            risk_score=10,
            reasoning="Test reasoning"
        )
        assert assessment_high.risk_score == 10


class TestVinRequest:
    """Test VinRequest model."""

    def test_valid_vin_request(self):
        """Test creation of valid VIN request."""
        request = VinRequest(vin="1HGCM82633A123456")
        assert request.vin == "1HGCM82633A123456"

    def test_vin_request_whitespace_trimming(self):
        """Test VIN request trims whitespace."""
        request = VinRequest(vin="  1HGCM82633A123456  ")
        assert request.vin == "1HGCM82633A123456"

    def test_vin_request_uppercase_conversion(self):
        """Test VIN request converts to uppercase."""
        request = VinRequest(vin="1hgcm82633a123456")
        assert request.vin == "1HGCM82633A123456"

    def test_vin_request_length_validation(self):
        """Test VIN request length validation."""
        with pytest.raises(ValidationError) as exc_info:
            VinRequest(vin="SHORT")

        assert "VIN must be exactly 17 characters" in str(exc_info.value)


class TestRiskFactors:
    """Test RiskFactors model."""

    def test_valid_risk_factors(self):
        """Test creation of valid risk factors."""
        factors = RiskFactors(
            days_on_lot_impact=-1,
            price_to_market_impact=2,
            vdp_views_impact=0,
            mileage_impact=-1,
            sales_opportunities_impact=1,
            total_adjustments=1,
            final_score=6
        )

        assert factors.days_on_lot_impact == -1
        assert factors.price_to_market_impact == 2
        assert factors.vdp_views_impact == 0
        assert factors.mileage_impact == -1
        assert factors.sales_opportunities_impact == 1
        assert factors.baseline_score == 5  # Default value
        assert factors.total_adjustments == 1
        assert factors.final_score == 6

    def test_final_score_bounds(self):
        """Test final score bounds validation."""
        # Test lower bound
        with pytest.raises(ValidationError):
            RiskFactors(
                days_on_lot_impact=0,
                price_to_market_impact=0,
                vdp_views_impact=0,
                mileage_impact=0,
                sales_opportunities_impact=0,
                total_adjustments=0,
                final_score=0
            )

        # Test upper bound
        with pytest.raises(ValidationError):
            RiskFactors(
                days_on_lot_impact=0,
                price_to_market_impact=0,
                vdp_views_impact=0,
                mileage_impact=0,
                sales_opportunities_impact=0,
                total_adjustments=0,
                final_score=11
            )


class TestVehicleNotFoundError:
    """Test VehicleNotFoundError exception."""

    def test_exception_creation(self):
        """Test creation of VehicleNotFoundError."""
        error = VehicleNotFoundError("Test message")
        assert str(error) == "Test message"

    def test_exception_inheritance(self):
        """Test VehicleNotFoundError inheritance."""
        error = VehicleNotFoundError("Test message")
        assert isinstance(error, Exception)