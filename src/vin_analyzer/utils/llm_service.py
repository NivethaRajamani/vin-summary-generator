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