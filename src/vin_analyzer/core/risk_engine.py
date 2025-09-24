"""Risk scoring engine with weighted calculations."""

from datetime import datetime
from typing import Optional

from ..models.vehicle import RiskAssessment, RiskFactors, VehicleData
from ..utils.llm_service import LLMService


class RiskEngine:
    """Engine for calculating vehicle risk scores based on multiple factors."""

    BASELINE_SCORE = 5
    MIN_SCORE = 1
    MAX_SCORE = 10

    # Mileage assumptions
    AVERAGE_MILES_PER_YEAR = 12000

    def __init__(self, use_llm: bool = True, anthropic_api_key: Optional[str] = None):
        """
        Initialize risk engine.

        Args:
            use_llm: Whether to use LLM for output generation
            anthropic_api_key: Anthropic API key (optional, can use env var)
        """
        self.use_llm = use_llm
        self.llm_service = None

        if use_llm:
            try:
                self.llm_service = LLMService(api_key=anthropic_api_key)
            except ValueError as e:
                print(f"Warning: LLM service initialization failed: {e}")
                print("Falling back to algorithmic output generation.")
                self.use_llm = False

    def _calculate_days_on_lot_impact(self, days_on_lot: int) -> int:
        """Calculate risk impact from days on lot."""
        if days_on_lot < 15:
            return -2  # Low risk
        elif days_on_lot <= 45:
            return 0  # Moderate risk
        else:
            return 2  # High risk

    def _calculate_price_to_market_impact(self, price_to_market_percent: float) -> int:
        """Calculate risk impact from price to market percentage."""
        if price_to_market_percent <= 95:
            return -2  # Below market, positive indicator
        elif 96 <= price_to_market_percent <= 105:
            return 0  # At/near market
        else:
            return 2  # Overpriced, negative indicator

    def _calculate_vdp_views_impact(self, vdp_views: int) -> int:
        """Calculate risk impact from VDP views."""
        if vdp_views > 200:
            return -1  # High views reduce risk
        elif 50 <= vdp_views <= 200:
            return 0  # Moderate views are neutral
        else:
            return 1  # Low views increase risk

    def _calculate_mileage_impact(self, vehicle: VehicleData) -> int:
        """Calculate risk impact from mileage relative to vehicle age."""
        current_year = datetime.now().year
        vehicle_age = current_year - vehicle.year

        # Handle new vehicles (0 mileage)
        if vehicle.mileage == 0:
            return -1  # New vehicles are lower risk

        # Calculate expected mileage
        expected_mileage = self.AVERAGE_MILES_PER_YEAR * vehicle_age

        if vehicle.mileage < expected_mileage * 0.8:  # Below average
            return -1
        elif vehicle.mileage <= expected_mileage * 1.2:  # Average range
            return 0
        else:  # Above average
            return 1

    def _calculate_sales_opportunities_impact(self, sales_opportunities: int) -> int:
        """Calculate risk impact from sales opportunities."""
        if sales_opportunities > 10:
            return -1  # Many opportunities reduce risk
        elif sales_opportunities <= 2:
            return 1  # Few opportunities increase risk
        else:
            return 0  # Moderate opportunities are neutral

    def _handle_missing_data_adjustments(self, vehicle: VehicleData) -> int:
        """Apply adjustments for missing or invalid data."""
        adjustment = 0

        # If price is 0 or missing, increase risk
        if vehicle.current_price == 0:
            adjustment += 1

        # If price_to_market is 0, use other factors more heavily
        if vehicle.price_to_market_percent == 0:
            # Weight days on lot more heavily
            if vehicle.days_on_lot > 100:
                adjustment += 1
            elif vehicle.days_on_lot < 10:
                adjustment -= 1

        return adjustment

    def calculate_risk_factors(self, vehicle: VehicleData) -> RiskFactors:
        """Calculate individual risk factors for transparency."""
        days_on_lot_impact = self._calculate_days_on_lot_impact(vehicle.days_on_lot)
        price_to_market_impact = self._calculate_price_to_market_impact(
            vehicle.price_to_market_percent
        )
        vdp_views_impact = self._calculate_vdp_views_impact(vehicle.total_vdps)
        mileage_impact = self._calculate_mileage_impact(vehicle)
        sales_opportunities_impact = self._calculate_sales_opportunities_impact(
            vehicle.sales_opportunities
        )

        # Handle missing data
        missing_data_adjustment = self._handle_missing_data_adjustments(vehicle)

        # Calculate total adjustments
        total_adjustments = (
            days_on_lot_impact
            + price_to_market_impact
            + vdp_views_impact
            + mileage_impact
            + sales_opportunities_impact
            + missing_data_adjustment
        )

        # Calculate final score with clamping
        raw_score = self.BASELINE_SCORE + total_adjustments
        final_score = max(self.MIN_SCORE, min(self.MAX_SCORE, raw_score))

        return RiskFactors(
            days_on_lot_impact=days_on_lot_impact,
            price_to_market_impact=price_to_market_impact,
            vdp_views_impact=vdp_views_impact,
            mileage_impact=mileage_impact,
            sales_opportunities_impact=sales_opportunities_impact,
            baseline_score=self.BASELINE_SCORE,
            total_adjustments=total_adjustments,
            final_score=final_score,
        )

    def _generate_summary(self, vehicle: VehicleData, risk_factors: RiskFactors) -> str:
        """Generate human-readable summary of vehicle's market position."""
        year = vehicle.year
        make = vehicle.make.title()
        model = vehicle.model.title()

        # Price analysis
        price_desc = ""
        if vehicle.current_price > 0:
            if vehicle.price_to_market_percent > 105:
                price_desc = "priced above market value"
            elif vehicle.price_to_market_percent < 95:
                price_desc = "priced below market value"
            else:
                price_desc = "competitively priced"
        else:
            price_desc = "with pricing to be determined"

        # Engagement analysis
        engagement_desc = ""
        if vehicle.total_vdps > 200:
            engagement_desc = "strong online engagement"
        elif vehicle.total_vdps >= 50:
            engagement_desc = "moderate online interest"
        else:
            engagement_desc = "limited online visibility"

        # Days on lot analysis
        lot_desc = ""
        if vehicle.days_on_lot < 15:
            lot_desc = "recently listed"
        elif vehicle.days_on_lot <= 45:
            lot_desc = "with normal inventory time"
        else:
            lot_desc = "with extended time on lot"

        # Risk level description
        risk_level = ""
        if risk_factors.final_score <= 3:
            risk_level = "low risk investment"
        elif risk_factors.final_score <= 6:
            risk_level = "moderate market position"
        else:
            risk_level = "requiring attention"

        return (
            f"This {year} {make} {model} is {price_desc} and shows {engagement_desc}, "
            f"{lot_desc}, indicating a {risk_level}."
        )

    def _generate_reasoning(
        self, vehicle: VehicleData, risk_factors: RiskFactors
    ) -> str:
        """Generate detailed reasoning for the risk score."""
        reasoning_parts = []

        # Days on lot reasoning
        if vehicle.days_on_lot < 15:
            reasoning_parts.append(
                f"Days on lot ({vehicle.days_on_lot}) is low "
                f"({risk_factors.days_on_lot_impact:+d})"
            )
        elif vehicle.days_on_lot <= 45:
            reasoning_parts.append(f"Days on lot ({vehicle.days_on_lot}) is normal (0)")
        else:
            reasoning_parts.append(
                f"Days on lot ({vehicle.days_on_lot}) is high "
                f"({risk_factors.days_on_lot_impact:+d})"
            )

        # Price to market reasoning
        if vehicle.price_to_market_percent > 0:
            if vehicle.price_to_market_percent <= 95:
                reasoning_parts.append(
                    f"Price is {vehicle.price_to_market_percent}% of market "
                    f"({risk_factors.price_to_market_impact:+d})"
                )
            elif vehicle.price_to_market_percent <= 105:
                reasoning_parts.append(
                    f"Price is {vehicle.price_to_market_percent}% of market (0)"
                )
            else:
                reasoning_parts.append(
                    f"Price is {vehicle.price_to_market_percent}% of market "
                    f"({risk_factors.price_to_market_impact:+d})"
                )
        else:
            reasoning_parts.append("Price to market data unavailable")

        # VDP views reasoning
        if vehicle.total_vdps > 200:
            reasoning_parts.append(
                f"VDP views ({vehicle.total_vdps:,}) are high "
                f"({risk_factors.vdp_views_impact:+d})"
            )
        elif vehicle.total_vdps >= 50:
            reasoning_parts.append(
                f"VDP views ({vehicle.total_vdps:,}) are moderate (0)"
            )
        else:
            reasoning_parts.append(
                f"VDP views ({vehicle.total_vdps:,}) are low "
                f"({risk_factors.vdp_views_impact:+d})"
            )

        # Mileage reasoning
        current_year = datetime.now().year
        vehicle_age = current_year - vehicle.year
        if vehicle.mileage == 0:
            reasoning_parts.append(
                f"New vehicle with 0 miles ({risk_factors.mileage_impact:+d})"
            )
        else:
            expected_mileage = self.AVERAGE_MILES_PER_YEAR * vehicle_age
            reasoning_parts.append(
                f"Mileage ({vehicle.mileage:,}) vs expected "
                f"({expected_mileage:,}) for age ({risk_factors.mileage_impact:+d})"
            )

        # Sales opportunities reasoning
        if vehicle.sales_opportunities > 10:
            reasoning_parts.append(
                f"Sales opportunities ({vehicle.sales_opportunities}) are high "
                f"({risk_factors.sales_opportunities_impact:+d})"
            )
        elif vehicle.sales_opportunities <= 2:
            reasoning_parts.append(
                f"Sales opportunities ({vehicle.sales_opportunities}) are low "
                f"({risk_factors.sales_opportunities_impact:+d})"
            )
        else:
            reasoning_parts.append(
                f"Sales opportunities ({vehicle.sales_opportunities}) are moderate (0)"
            )

        # Final calculation
        final_part = (
            f"Overall score = {risk_factors.baseline_score} baseline "
            f"{risk_factors.total_adjustments:+d} adjustments = "
            f"{risk_factors.final_score}"
        )

        return ". ".join(reasoning_parts) + f". {final_part}."

    def assess_risk(self, vehicle: VehicleData) -> RiskAssessment:
        """Assess risk for a vehicle and return complete assessment."""
        risk_factors = self.calculate_risk_factors(vehicle)

        # Use LLM for output generation if available
        if self.use_llm and self.llm_service:
            try:
                llm_output = self.llm_service.generate_risk_assessment(
                    vehicle, risk_factors
                )
                return RiskAssessment(
                    summary=llm_output["summary"],
                    risk_score=llm_output["risk_score"],
                    reasoning=llm_output["reasoning"],
                )
            except Exception as e:
                print(f"LLM generation failed: {e}. Using fallback.")

        # Fallback to algorithmic generation
        summary = self._generate_summary(vehicle, risk_factors)
        reasoning = self._generate_reasoning(vehicle, risk_factors)

        return RiskAssessment(
            summary=summary, risk_score=risk_factors.final_score, reasoning=reasoning
        )
