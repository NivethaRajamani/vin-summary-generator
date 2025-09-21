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

    