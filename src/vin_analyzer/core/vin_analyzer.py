"""VIN analysis service combining data loading and risk assessment."""

from pathlib import Path
from typing import Optional

from ..utils.data_loader import DataLoader
from .risk_engine import RiskEngine


class VinAnalyzer:
    """Main service for VIN analysis combining data loading and risk assessment."""

    def __init__(self, csv_file_path: str, use_llm: bool = True, anthropic_api_key: Optional[str] = None):
        """
        Initialize VIN analyzer with CSV data source.

        Args:
            csv_file_path: Path to CSV data file
            use_llm: Whether to use LLM for output generation
            anthropic_api_key: Anthropic API key (optional, can use env var)
        """
        self.data_loader = DataLoader(csv_file_path)
        self.risk_engine = RiskEngine(use_llm=use_llm, anthropic_api_key=anthropic_api_key)

