"""VIN analysis service combining data loading and risk assessment."""

from pathlib import Path
from typing import Optional

from ..models.vehicle import RiskAssessment, VehicleData, VehicleNotFoundError
from ..utils.data_loader import DataLoader
from .risk_engine import RiskEngine


class VinAnalyzer:
    """Main service for VIN analysis combining data loading and risk assessment."""

    def __init__(
        self,
        csv_file_path: str,
        use_llm: bool = True,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize VIN analyzer with CSV data source.

        Args:
            csv_file_path: Path to CSV data file
            use_llm: Whether to use LLM for output generation
            anthropic_api_key: Anthropic API key (optional, can use env var)
        """
        self.data_loader = DataLoader(csv_file_path)
        self.risk_engine = RiskEngine(
            use_llm=use_llm, anthropic_api_key=anthropic_api_key
        )

    def analyze_vin(self, vin: str) -> RiskAssessment:
        """
        Analyze a VIN and return risk assessment.

        Args:
            vin: Vehicle Identification Number

        Returns:
            RiskAssessment with summary, risk score, and reasoning

        Raises:
            VehicleNotFoundError: If VIN is not found in database
        """
        # Get vehicle data
        vehicle_data = self.data_loader.get_vehicle_by_vin(vin)

        # Assess risk
        risk_assessment = self.risk_engine.assess_risk(vehicle_data)

        return risk_assessment

    def get_vehicle_data(self, vin: str) -> VehicleData:
        """
        Get raw vehicle data by VIN.

        Args:
            vin: Vehicle Identification Number

        Returns:
            VehicleData object

        Raises:
            VehicleNotFoundError: If VIN is not found in database
        """
        return self.data_loader.get_vehicle_by_vin(vin)

    def get_database_stats(self) -> dict:
        """Get statistics about the loaded database."""
        vehicles = self.data_loader.get_all_vehicles()

        if not vehicles:
            return {
                "total_vehicles": 0,
                "makes": [],
                "year_range": None,
                "price_range": None,
            }

        makes = list(set(v.make for v in vehicles))
        years = [v.year for v in vehicles]
        prices = [float(v.current_price) for v in vehicles if v.current_price > 0]

        return {
            "total_vehicles": len(vehicles),
            "makes": sorted(makes),
            "year_range": {
                "min": min(years) if years else None,
                "max": max(years) if years else None,
            },
            "price_range": {
                "min": min(prices) if prices else None,
                "max": max(prices) if prices else None,
                "avg": sum(prices) / len(prices) if prices else None,
            },
        }

    def validate_vin_exists(self, vin: str) -> bool:
        """
        Check if VIN exists in database without retrieving full data.

        Args:
            vin: Vehicle Identification Number

        Returns:
            True if VIN exists, False otherwise
        """
        try:
            self.data_loader.get_vehicle_by_vin(vin)
            return True
        except VehicleNotFoundError:
            return False

    @classmethod
    def create_from_sample_data(
        cls,
        project_root: Optional[str] = None,
        use_llm: bool = True,
        anthropic_api_key: Optional[str] = None,
    ) -> "VinAnalyzer":
        """
        Create VinAnalyzer using the sample data CSV file.

        Args:
            project_root: Optional project root path. If None, will try to find it.
            use_llm: Whether to use LLM for output generation
            anthropic_api_key: Anthropic API key (optional, can use env var)

        Returns:
            VinAnalyzer instance

        Raises:
            FileNotFoundError: If sample data file cannot be found
        """
        if project_root is None:
            # Try to find project root
            current_path = Path(__file__).parent
            while current_path.parent != current_path:
                sample_data_path = current_path / "sample_data.csv"
                if sample_data_path.exists():
                    return cls(
                        str(sample_data_path),
                        use_llm=use_llm,
                        anthropic_api_key=anthropic_api_key,
                    )
                current_path = current_path.parent

            raise FileNotFoundError("Could not find sample_data.csv file")
        else:
            sample_data_path = Path(project_root) / "sample_data.csv"
            if not sample_data_path.exists():
                raise FileNotFoundError(
                    f"Sample data file not found: {sample_data_path}"
                )
            return cls(
                str(sample_data_path),
                use_llm=use_llm,
                anthropic_api_key=anthropic_api_key,
            )
