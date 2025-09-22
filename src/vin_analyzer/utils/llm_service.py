"""Anthropic Claude LLM service for generating vehicle risk assessments."""

import json
import os
from typing import Dict, Any

import anthropic

from ..models.vehicle import VehicleData, RiskFactors


class LLMService:
    """Service for generating LLM-powered risk assessments using Claude 4.0 Sonnet."""

    def __init__(self, api_key: str = None):
        """Initialize LLM service with Anthropic API key."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def generate_risk_assessment(
        self,
        vehicle: VehicleData,
        risk_factors: RiskFactors
    ) -> Dict[str, Any]:
        """
        Generate LLM-powered risk assessment output.

        Args:
            vehicle: Vehicle data
            risk_factors: Calculated risk factors

        Returns:
            Dictionary with summary, risk_score, and reasoning
        """
        prompt = self._build_prompt(vehicle, risk_factors)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.3,
                system=(
                    "You are an expert automotive risk analyst. Generate a "
                    "JSON response with vehicle risk assessment. Be concise "
                    "and professional. Always return valid JSON only."
                ),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text.strip()

            # Parse JSON response
            try:
                result = json.loads(content)

                # Validate required fields
                if not all(key in result for key in ['summary', 'risk_score', 'reasoning']):
                    raise ValueError("Missing required fields in LLM response")

                # Ensure risk_score is integer and within bounds
                result['risk_score'] = max(1, min(10, int(result['risk_score'])))

                return result

            except json.JSONDecodeError:
                # Fallback: extract JSON from response if wrapped in text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    result['risk_score'] = max(1, min(10, int(result['risk_score'])))
                    return result
                else:
                    raise ValueError("Could not parse JSON from LLM response")

        except Exception as e:
            # Fallback to algorithmic generation if LLM fails
            print(f"LLM generation failed: {e}. Using fallback.")
            return self._generate_fallback_assessment(vehicle, risk_factors)
        
    def _build_prompt(self, vehicle: VehicleData, risk_factors: RiskFactors) -> str:
        """Build the prompt for LLM generation."""
        current_year = 2025  # Could be made dynamic
        vehicle_age = current_year - vehicle.year

        prompt = f"""
Analyze this vehicle and provide a risk assessment in JSON format:

VEHICLE DETAILS:
- VIN: {vehicle.vin}
- Year: {vehicle.year} {vehicle.make.title()} {vehicle.model.title()}
- Vehicle Age: {vehicle_age} years
- Current Price: ${vehicle.current_price:,.0f}
- Price to Market: {vehicle.price_to_market_percent}%
- Days on Lot: {vehicle.days_on_lot}
- Mileage: {vehicle.mileage:,} miles
- VDP Views: {vehicle.total_vdps:,}
- Sales Opportunities: {vehicle.sales_opportunities}

RISK FACTOR ANALYSIS:
- Days on Lot Impact: {risk_factors.days_on_lot_impact:+d}
- Price to Market Impact: {risk_factors.price_to_market_impact:+d}
- VDP Views Impact: {risk_factors.vdp_views_impact:+d}
- Mileage Impact: {risk_factors.mileage_impact:+d}
- Sales Opportunities Impact: {risk_factors.sales_opportunities_impact:+d}
- Total Adjustments: {risk_factors.total_adjustments:+d}
- Calculated Risk Score: {risk_factors.final_score}

SCORING RULES:
- Days on Lot: <15 days (low risk), 15-45 days (normal), >45 days (high risk)
- Price to Market: ≤95% (below market, good), 96-105% (at market), >105% (overpriced)
- VDP Views: >200 (high interest), 50-200 (moderate), <50 (low interest)
- Mileage: Below average for age (good), average (normal), above average (concerning)
- Sales Opportunities: >10 (many), 3-10 (moderate), ≤2 (few)

Generate a JSON response with:
{{
  "summary": "A concise, professional summary of this vehicle's market position and appeal (2-3 sentences)",
  "risk_score": {risk_factors.final_score},
  "reasoning": "Clear explanation of why this risk score was assigned, mentioning specific factors like days on lot, pricing, buyer interest, mileage, and sales activity"
}}

Important: Return ONLY the JSON object, no additional text.
"""
        return prompt.strip()

    def _generate_fallback_assessment(
        self,
        vehicle: VehicleData,
        risk_factors: RiskFactors
    ) -> Dict[str, Any]:
        """Generate fallback assessment if LLM fails."""
        # Simple algorithmic fallback
        year = vehicle.year
        make = vehicle.make.title()
        model = vehicle.model.title()

        # Basic summary
        if risk_factors.final_score <= 3:
            risk_level = "low-risk investment"
        elif risk_factors.final_score <= 6:
            risk_level = "moderate market position"
        else:
            risk_level = "requiring attention"

        summary = (
            f"This {year} {make} {model} represents a {risk_level} "
            f"based on current market metrics and pricing."
        )

        # Basic reasoning
        reasoning_parts = []

        if risk_factors.days_on_lot_impact != 0:
            reasoning_parts.append(
                f"Days on lot ({vehicle.days_on_lot}) "
                f"{'reduces' if risk_factors.days_on_lot_impact < 0 else 'increases'} risk"
            )

        if risk_factors.price_to_market_impact != 0:
            reasoning_parts.append(
                f"Pricing at {vehicle.price_to_market_percent}% of market "
                f"{'helps' if risk_factors.price_to_market_impact < 0 else 'hurts'} appeal"
            )

        reasoning = (
            f"Risk assessment based on: {', '.join(reasoning_parts[:2])}. "
            f"Final score: {risk_factors.final_score}/10."
        )

        return {
            "summary": summary,
            "risk_score": risk_factors.final_score,
            "reasoning": reasoning
        }