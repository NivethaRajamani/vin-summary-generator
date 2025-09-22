"""Vehicle data models and schemas."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VehicleData(BaseModel):
    """Vehicle data model with validation."""

    vin: str = Field(..., description="Vehicle Identification Number")
    year: int = Field(..., description="Model year")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    current_price: Decimal = Field(..., description="Current price in USD")
    price_to_market_percent: float = Field(
        ..., description="Price to market percentage"
    )
    days_on_lot: int = Field(..., description="Days on lot (DOL)")
    mileage: int = Field(..., description="Vehicle mileage")
    total_vdps: int = Field(..., description="Total VDP views (lifetime)")
    sales_opportunities: int = Field(
        ..., description="Total sales opportunities (lifetime)"
    )

    @field_validator('vin')
    def validate_vin(cls, v):
        """Validate VIN format."""
        if not v or len(v) != 17:
            raise ValueError('VIN must be exactly 17 characters')
        return v.upper()

    @field_validator('year')
    def validate_year(cls, v):
        """Validate year range."""
        if v < 1980 or v > 2030:
            raise ValueError('Year must be between 1980 and 2030')
        return v

    @field_validator('current_price')
    def validate_price(cls, v):
        """Validate price is positive."""
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v

    @field_validator('days_on_lot')
    def validate_days_on_lot(cls, v):
        """Validate days on lot is non-negative."""
        if v < 0:
            raise ValueError('Days on lot must be non-negative')
        return v

    @field_validator('mileage')
    def validate_mileage(cls, v):
        """Validate mileage is non-negative."""
        if v < 0:
            raise ValueError('Mileage must be non-negative')
        return v


class RiskAssessment(BaseModel):
    """Risk assessment result model."""

    summary: str = Field(
        ..., description="Human-readable summary of vehicle's market position"
    )
    risk_score: int = Field(
        ..., ge=1, le=10, description="Risk score from 1 (low) to 10 (high)"
    )
    reasoning: str = Field(..., description="Explanation of risk score calculation")

    class Config:
        schema_extra = {
            "example": {
                "summary": "This 2018 Honda Accord is priced slightly above market value but shows strong online engagement, indicating healthy buyer interest despite moderate days on lot.",
                "risk_score": 4,
                "reasoning": "Days on lot (25) is within normal range (neutral). Price is 5% above market (+2). VDP views are high (-1). Mileage is below average (-1). Overall score = 5 baseline +0 (days_on_lot) +2 (price_to_market) -1 (views) -1 (mileage) = 5, clamped to 4 for lower risk indication."
            }
        }


class VinRequest(BaseModel):
    """VIN analysis request model."""

    vin: str = Field(..., description="Vehicle Identification Number to analyze")

    @field_validator('vin')
    def validate_vin(cls, v):
        """Validate VIN format."""
        if not v or len(v.strip()) != 17:
            raise ValueError('VIN must be exactly 17 characters')
        return v.strip().upper()

    class Config:
        schema_extra = {
            "example": {
                "vin": "1HGCM82633A123456"
            }
        }

        
class VehicleNotFoundError(Exception):
    """Raised when vehicle is not found in database."""
    pass


class RiskFactors(BaseModel):
    """Individual risk factors for transparency."""

    days_on_lot_impact: int = Field(..., description="Impact from days on lot (-2 to +2)")
    price_to_market_impact: int = Field(..., description="Impact from price to market (-2 to +2)")
    vdp_views_impact: int = Field(..., description="Impact from VDP views (-1 to +1)")
    mileage_impact: int = Field(..., description="Impact from mileage (-1 to +1)")
    sales_opportunities_impact: int = Field(..., description="Impact from sales opportunities (-1 to +1)")
    baseline_score: int = Field(default=5, description="Baseline risk score")
    total_adjustments: int = Field(..., description="Sum of all adjustments")
    final_score: int = Field(..., ge=1, le=10, description="Final clamped risk score")