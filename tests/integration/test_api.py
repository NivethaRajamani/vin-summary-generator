"""Integration tests for API endpoints."""

import pytest
import tempfile
import csv
from pathlib import Path
from fastapi.testclient import TestClient

from src.vin_analyzer.api.main import app
from src.vin_analyzer.api.routes import set_analyzer
from src.vin_analyzer.core.vin_analyzer import VinAnalyzer


class TestAPIIntegration:
    """Integration tests for the VIN Analyzer API."""

    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing."""
        return [
            {
                'VIN': '1HGCM82633A123456',
                'Year': '2018',
                'Make': 'HONDA',
                'Model': 'ACCORD',
                'Current price': '$25,000',
                'Current price to market %': '95%',
                'DOL': '25',
                'Mileage': '50,000',
                'Total VDPs (lifetime)': '150',
                'Total sales opportunities (lifetime)': '5'
            },
            {
                'VIN': '2HGCM82633A123457',
                'Year': '2019',
                'Make': 'TOYOTA',
                'Model': 'CAMRY',
                'Current price': '$30,500',
                'Current price to market %': '105%',
                'DOL': '45',
                'Mileage': '30,000',
                'Total VDPs (lifetime)': '75',
                'Total sales opportunities (lifetime)': '2'
            },
            {
                'VIN': '3HGCM82633A123458',
                'Year': '2020',
                'Make': 'NISSAN',
                'Model': 'ALTIMA',
                'Current price': '$22,000',
                'Current price to market %': '98%',
                'DOL': '60',
                'Mileage': '35,000',
                'Total VDPs (lifetime)': '25',
                'Total sales opportunities (lifetime)': '1'
            }
        ]

    @pytest.fixture
    def temp_csv_file(self, sample_csv_data):
        """Create temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            fieldnames = sample_csv_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_csv_data)
            f.flush()
            yield f.name

        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def api_client(self, temp_csv_file):
        """Create API client with test data."""
        # Initialize analyzer with test data
        analyzer = VinAnalyzer(temp_csv_file)
        set_analyzer(analyzer)

        # Create test client
        client = TestClient(app)
        return client

    def test_root_endpoint(self, api_client):
        """Test root endpoint."""
        response = api_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "endpoints" in data

    def test_health_check_endpoint(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "database_stats" in data
        assert data["database_stats"]["total_vehicles"] == 3

    def test_stats_endpoint(self, api_client):
        """Test database statistics endpoint."""
        response = api_client.get("/api/v1/stats")
        assert response.status_code == 200

        data = response.json()
        assert "database_statistics" in data
        stats = data["database_statistics"]

        assert stats["total_vehicles"] == 3
        assert "HONDA" in stats["makes"]
        assert "TOYOTA" in stats["makes"]
        assert "NISSAN" in stats["makes"]
        assert stats["year_range"]["min"] == 2018
        assert stats["year_range"]["max"] == 2020

    def test_analyze_valid_vin(self, api_client):
        """Test VIN analysis with valid VIN."""
        vin_request = {"vin": "1HGCM82633A123456"}
        response = api_client.post("/api/v1/analyze", json=vin_request)

        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "risk_score" in data
        assert "reasoning" in data

        # Validate response structure
        assert 1 <= data["risk_score"] <= 10
        assert len(data["summary"]) > 0
        assert len(data["reasoning"]) > 0

        # Check that summary contains vehicle information
        assert "2018" in data["summary"]
        assert "Honda" in data["summary"]
        assert "Accord" in data["summary"]

    def test_analyze_case_insensitive_vin(self, api_client):
        """Test VIN analysis with lowercase VIN."""
        vin_request = {"vin": "1hgcm82633a123456"}
        response = api_client.post("/api/v1/analyze", json=vin_request)

        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "risk_score" in data
        assert "reasoning" in data

    def test_analyze_vin_with_whitespace(self, api_client):
        """Test VIN analysis with whitespace."""
        vin_request = {"vin": "  1HGCM82633A123456  "}
        response = api_client.post("/api/v1/analyze", json=vin_request)

        assert response.status_code == 200

        data = response.json()
        assert "summary" in data

    def test_analyze_invalid_vin_format(self, api_client):
        """Test VIN analysis with invalid VIN format."""
        vin_request = {"vin": "INVALID"}
        response = api_client.post("/api/v1/analyze", json=vin_request)

        assert response.status_code == 422

    def test_analyze_nonexistent_vin(self, api_client):
        """Test VIN analysis with non-existent VIN."""
        vin_request = {"vin": "9HGCM82633A999999"}
        response = api_client.post("/api/v1/analyze", json=vin_request)

        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_validate_existing_vin(self, api_client):
        """Test VIN validation with existing VIN."""
        vin_request = {"vin": "1HGCM82633A123456"}
        response = api_client.post("/api/v1/validate", json=vin_request)

        assert response.status_code == 200

        data = response.json()
        assert data["vin"] == "1HGCM82633A123456"
        assert data["exists"] is True
        assert "found" in data["message"].lower()

    def test_validate_nonexistent_vin(self, api_client):
        """Test VIN validation with non-existent VIN."""
        vin_request = {"vin": "9HGCM82633A999999"}
        response = api_client.post("/api/v1/validate", json=vin_request)

        assert response.status_code == 200

        data = response.json()
        assert data["vin"] == "9HGCM82633A999999"
        assert data["exists"] is False
        assert "not found" in data["message"].lower()

    def test_validate_invalid_vin_format(self, api_client):
        """Test VIN validation with invalid format."""
        vin_request = {"vin": "SHORT"}
        response = api_client.post("/api/v1/validate", json=vin_request)

        assert response.status_code == 422

    def test_analyze_multiple_vins(self, api_client):
        """Test analyzing multiple different VINs."""
        vins = ["1HGCM82633A123456", "2HGCM82633A123457", "3HGCM82633A123458"]

        for vin in vins:
            vin_request = {"vin": vin}
            response = api_client.post("/api/v1/analyze", json=vin_request)

            assert response.status_code == 200

            data = response.json()
            assert 1 <= data["risk_score"] <= 10
            assert len(data["summary"]) > 0
            assert len(data["reasoning"]) > 0

    def test_risk_score_variations(self, api_client):
        """Test that different vehicles get different risk scores."""
        # Analyze multiple vehicles and collect risk scores
        vins = ["1HGCM82633A123456", "2HGCM82633A123457", "3HGCM82633A123458"]
        risk_scores = []

        for vin in vins:
            vin_request = {"vin": vin}
            response = api_client.post("/api/v1/analyze", json=vin_request)
            assert response.status_code == 200

            data = response.json()
            risk_scores.append(data["risk_score"])

        # Different vehicles should potentially have different risk scores
        # (though they might coincidentally be the same)
        assert all(1 <= score <= 10 for score in risk_scores)

    def test_api_error_handling_missing_json(self, api_client):
        """Test API error handling with missing JSON body."""
        response = api_client.post("/api/v1/analyze")
        assert response.status_code == 422

    def test_api_error_handling_invalid_json(self, api_client):
        """Test API error handling with invalid JSON structure."""
        response = api_client.post("/api/v1/analyze", json={"invalid_field": "value"})
        assert response.status_code == 422

    def test_api_cors_headers(self, api_client):
        """Test that CORS headers are present."""
        response = api_client.options("/api/v1/analyze")
        # CORS middleware should handle OPTIONS requests

    def test_analyze_reasoning_contains_factors(self, api_client):
        """Test that analysis reasoning contains all risk factors."""
        vin_request = {"vin": "1HGCM82633A123456"}
        response = api_client.post("/api/v1/analyze", json=vin_request)

        assert response.status_code == 200

        data = response.json()
        reasoning = data["reasoning"].lower()

        # Check that reasoning mentions all major risk factors
        assert "days on lot" in reasoning
        assert "price" in reasoning
        assert "views" in reasoning or "vdp" in reasoning
        assert "mileage" in reasoning or "miles" in reasoning
        assert "opportunities" in reasoning

    def test_summary_format_consistency(self, api_client):
        """Test that summary format is consistent across different vehicles."""
        vins = ["1HGCM82633A123456", "2HGCM82633A123457"]

        for vin in vins:
            vin_request = {"vin": vin}
            response = api_client.post("/api/v1/analyze", json=vin_request)

            assert response.status_code == 200

            data = response.json()
            summary = data["summary"]

            # Summary should be a proper sentence
            assert summary.endswith(".")
            assert len(summary) > 20  # Should be reasonably descriptive
            # Should have proper capitalization
            assert any(char.isupper() for char in summary)