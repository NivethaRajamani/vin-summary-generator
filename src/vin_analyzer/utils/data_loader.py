"""CSV data loading and parsing utilities."""

import csv
import re
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from ..models.vehicle import VehicleData, VehicleNotFoundError


class DataLoader:
    """Handles loading and parsing vehicle data from CSV files."""

    def __init__(self, csv_file_path: str):
        """Initialize with CSV file path."""
        self.csv_file_path = Path(csv_file_path)
        self.vehicles: Dict[str, VehicleData] = {}
        self._load_data()

    def _clean_price(self, price_str: str) -> Decimal:
        """Clean and convert price string to Decimal."""
        if not price_str or price_str.strip() in ["$0", "0", "-", ""]:
            return Decimal("0")

        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r"[$,\s]", "", price_str.strip())

        # Handle empty or invalid values
        if not cleaned or cleaned == "0":
            return Decimal("0")

        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal("0")

    def _clean_percentage(self, percent_str: str) -> float:
        """Clean and convert percentage string to float."""
        if not percent_str or percent_str.strip() in ["-", "", "0%"]:
            return 0.0

        # Remove % symbol and whitespace
        cleaned = percent_str.strip().replace("%", "")

        # Handle empty or invalid values
        if not cleaned or cleaned == "0":
            return 0.0

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _clean_integer(self, int_str: str) -> int:
        """Clean and convert string to integer."""
        if not int_str or int_str.strip() in ["-", "", "0"]:
            return 0

        # Remove commas and whitespace
        cleaned = re.sub(r"[,\s]", "", int_str.strip())

        # Handle empty or invalid values
        if not cleaned:
            return 0

        try:
            return int(cleaned)
        except ValueError:
            return 0

    def _parse_row(self, row: Dict[str, str]) -> Optional[VehicleData]:
        """Parse a single CSV row into VehicleData."""
        try:
            # Handle different possible column names
            vin = row.get("VIN", "").strip()
            if not vin:
                return None

            year = self._clean_integer(row.get("Year", "0"))
            if year == 0:
                return None

            make = row.get("Make", "").strip().upper()
            model = row.get("Model", "").strip().upper()

            if not make or not model:
                return None

            current_price = self._clean_price(row.get("Current price", ""))
            price_to_market_percent = self._clean_percentage(
                row.get("Current price to market %", "0%")
            )
            days_on_lot = self._clean_integer(row.get("DOL", "0"))
            mileage = self._clean_integer(row.get("Mileage", "0"))
            total_vdps = self._clean_integer(row.get("Total VDPs (lifetime)", "0"))
            sales_opportunities = self._clean_integer(
                row.get("Total sales opportunities (lifetime)", "0")
            )

            return VehicleData(
                vin=vin,
                year=year,
                make=make,
                model=model,
                current_price=current_price,
                price_to_market_percent=price_to_market_percent,
                days_on_lot=days_on_lot,
                mileage=mileage,
                total_vdps=total_vdps,
                sales_opportunities=sales_opportunities,
            )

        except Exception as e:
            print(f"Error parsing row: {e}")
            return None

    def _load_data(self) -> None:
        """Load vehicle data from CSV file."""
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")

        with open(self.csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                vehicle = self._parse_row(row)
                if vehicle:
                    self.vehicles[vehicle.vin] = vehicle
                else:
                    print(f"Warning: Could not parse row {row_num}: {row}")

        print(f"Loaded {len(self.vehicles)} vehicles from CSV")

    def get_vehicle_by_vin(self, vin: str) -> VehicleData:
        """Get vehicle data by VIN."""
        vin = vin.strip().upper()

        if vin not in self.vehicles:
            raise VehicleNotFoundError(f"Vehicle with VIN {vin} not found")

        return self.vehicles[vin]

    def get_all_vehicles(self) -> List[VehicleData]:
        """Get all loaded vehicles."""
        return list(self.vehicles.values())

    def get_vehicles_by_make(self, make: str) -> List[VehicleData]:
        """Get vehicles by manufacturer."""
        make = make.strip().upper()
        return [v for v in self.vehicles.values() if v.make == make]

    def get_vehicles_by_year(self, year: int) -> List[VehicleData]:
        """Get vehicles by model year."""
        return [v for v in self.vehicles.values() if v.year == year]

    def calculate_average_mileage_for_age(self, vehicle_age: int) -> float:
        """Calculate average mileage for vehicles of a given age."""
        vehicles_of_age = [
            v
            for v in self.vehicles.values()
            if (2025 - v.year) == vehicle_age and v.mileage > 0
        ]

        if not vehicles_of_age:
            return 12000.0 * vehicle_age  # Default assumption

        total_mileage = sum(v.mileage for v in vehicles_of_age)
        return total_mileage / len(vehicles_of_age)

    def get_vehicle_count(self) -> int:
        """Get total number of loaded vehicles."""
        return len(self.vehicles)
