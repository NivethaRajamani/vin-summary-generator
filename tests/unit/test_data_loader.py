"""Unit tests for data loader utilities."""

import pytest
import tempfile
import csv
from pathlib import Path
from decimal import Decimal

from src.vin_analyzer.utils.data_loader import DataLoader
from src.vin_analyzer.models.vehicle import VehicleNotFoundError


class TestDataLoader:
    """Test DataLoader functionality."""

    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing."""
        return [
            {
                "VIN": "1HGCM82633A123456",
                "Year": "2018",
                "Make": "HONDA",
                "Model": "ACCORD",
                "Current price": "$25,000",
                "Current price to market %": "95%",
                "DOL": "25",
                "Mileage": "50,000",
                "Total VDPs (lifetime)": "150",
                "Total sales opportunities (lifetime)": "5",
            },
            {
                "VIN": "2HGCM82633A123457",
                "Year": "2019",
                "Make": "TOYOTA",
                "Model": "CAMRY",
                "Current price": "$30,500",
                "Current price to market %": "105%",
                "DOL": "45",
                "Mileage": "30,000",
                "Total VDPs (lifetime)": "75",
                "Total sales opportunities (lifetime)": "2",
            },
            {
                "VIN": "3HGCM82633A123458",
                "Year": "2020",
                "Make": "NISSAN",
                "Model": "ALTIMA",
                "Current price": "$0",
                "Current price to market %": "0%",
                "DOL": "100",
                "Mileage": "0",
                "Total VDPs (lifetime)": "0",
                "Total sales opportunities (lifetime)": "0",
            },
        ]

    @pytest.fixture
    def temp_csv_file(self, sample_csv_data):
        """Create temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            fieldnames = sample_csv_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_csv_data)
            f.flush()
            yield f.name

        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    def test_data_loader_initialization(self, temp_csv_file):
        """Test DataLoader initialization."""
        loader = DataLoader(temp_csv_file)
        assert loader.csv_file_path == Path(temp_csv_file)
        assert len(loader.vehicles) == 3

    def test_data_loader_file_not_found(self):
        """Test DataLoader with non-existent file."""
        with pytest.raises(FileNotFoundError):
            DataLoader("non_existent_file.csv")

    def test_clean_price(self, temp_csv_file):
        """Test price cleaning functionality."""
        loader = DataLoader(temp_csv_file)

        # Test regular price
        assert loader._clean_price("$25,000") == Decimal("25000")

        # Test price without currency symbol
        assert loader._clean_price("30500") == Decimal("30500")

        # Test zero price
        assert loader._clean_price("$0") == Decimal("0")

        # Test empty/invalid price
        assert loader._clean_price("") == Decimal("0")
        assert loader._clean_price("-") == Decimal("0")

    def test_clean_percentage(self, temp_csv_file):
        """Test percentage cleaning functionality."""
        loader = DataLoader(temp_csv_file)

        # Test regular percentage
        assert loader._clean_percentage("95%") == 95.0

        # Test percentage without symbol
        assert loader._clean_percentage("105") == 105.0

        # Test zero percentage
        assert loader._clean_percentage("0%") == 0.0

        # Test empty/invalid percentage
        assert loader._clean_percentage("") == 0.0
        assert loader._clean_percentage("-") == 0.0

    def test_clean_integer(self, temp_csv_file):
        """Test integer cleaning functionality."""
        loader = DataLoader(temp_csv_file)

        # Test regular integer with commas
        assert loader._clean_integer("50,000") == 50000

        # Test regular integer
        assert loader._clean_integer("150") == 150

        # Test zero
        assert loader._clean_integer("0") == 0

        # Test empty/invalid integer
        assert loader._clean_integer("") == 0
        assert loader._clean_integer("-") == 0

    def test_get_vehicle_by_vin(self, temp_csv_file):
        """Test getting vehicle by VIN."""
        loader = DataLoader(temp_csv_file)

        # Test existing VIN
        vehicle = loader.get_vehicle_by_vin("1HGCM82633A123456")
        assert vehicle.vin == "1HGCM82633A123456"
        assert vehicle.make == "HONDA"
        assert vehicle.model == "ACCORD"
        assert vehicle.year == 2018

        # Test case insensitive VIN lookup
        vehicle = loader.get_vehicle_by_vin("1hgcm82633a123456")
        assert vehicle.vin == "1HGCM82633A123456"

        # Test non-existent VIN
        with pytest.raises(VehicleNotFoundError):
            loader.get_vehicle_by_vin("NONEXISTENTVINNUMB")

    def test_get_all_vehicles(self, temp_csv_file):
        """Test getting all vehicles."""
        loader = DataLoader(temp_csv_file)
        vehicles = loader.get_all_vehicles()

        assert len(vehicles) == 3
        assert all(hasattr(v, "vin") for v in vehicles)

    def test_get_vehicles_by_make(self, temp_csv_file):
        """Test getting vehicles by make."""
        loader = DataLoader(temp_csv_file)

        honda_vehicles = loader.get_vehicles_by_make("HONDA")
        assert len(honda_vehicles) == 1
        assert honda_vehicles[0].make == "HONDA"

        # Test case insensitive
        honda_vehicles = loader.get_vehicles_by_make("honda")
        assert len(honda_vehicles) == 1

        # Test non-existent make
        nonexistent_vehicles = loader.get_vehicles_by_make("NONEXISTENT")
        assert len(nonexistent_vehicles) == 0

    def test_get_vehicles_by_year(self, temp_csv_file):
        """Test getting vehicles by year."""
        loader = DataLoader(temp_csv_file)

        vehicles_2018 = loader.get_vehicles_by_year(2018)
        assert len(vehicles_2018) == 1
        assert vehicles_2018[0].year == 2018

        # Test non-existent year
        vehicles_2000 = loader.get_vehicles_by_year(2000)
        assert len(vehicles_2000) == 0

    def test_calculate_average_mileage_for_age(self, temp_csv_file):
        """Test calculating average mileage for vehicle age."""
        loader = DataLoader(temp_csv_file)

        # Test with vehicles that have mileage data
        # Vehicle age calculation: 2025 - year
        avg_mileage = loader.calculate_average_mileage_for_age(7)  # 2018 vehicles
        assert avg_mileage == 50000  # Only one 2018 vehicle with 50,000 miles

        # Test with age that has no vehicles
        avg_mileage = loader.calculate_average_mileage_for_age(50)
        assert avg_mileage == 600000.0  # Default: 12000 * 50

    def test_get_vehicle_count(self, temp_csv_file):
        """Test getting vehicle count."""
        loader = DataLoader(temp_csv_file)
        assert loader.get_vehicle_count() == 3

    def test_parse_row_with_missing_data(self, temp_csv_file):
        """Test parsing row with missing or invalid data."""
        loader = DataLoader(temp_csv_file)

        # Test row with missing VIN
        invalid_row = {
            "VIN": "",
            "Year": "2018",
            "Make": "HONDA",
            "Model": "ACCORD",
            "Current price": "$25,000",
            "Current price to market %": "95%",
            "DOL": "25",
            "Mileage": "50,000",
            "Total VDPs (lifetime)": "150",
            "Total sales opportunities (lifetime)": "5",
        }

        result = loader._parse_row(invalid_row)
        assert result is None

        # Test row with missing year
        invalid_row["VIN"] = "1HGCM82633A123456"
        invalid_row["Year"] = ""

        result = loader._parse_row(invalid_row)
        assert result is None

    def test_data_loading_with_zero_values(self, temp_csv_file):
        """Test that vehicles with zero values are still loaded."""
        loader = DataLoader(temp_csv_file)

        # Get the vehicle with zero price
        vehicle = loader.get_vehicle_by_vin("3HGCM82633A123458")
        assert vehicle.current_price == Decimal("0")
        assert vehicle.price_to_market_percent == 0.0
        assert vehicle.mileage == 0
