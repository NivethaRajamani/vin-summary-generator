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



class VehicleNotFoundError(Exception):
    """Raised when vehicle is not found in database."""
    pass

