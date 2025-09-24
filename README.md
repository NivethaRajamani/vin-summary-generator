# vin-summary-generator

A RESTful API service for analyzing Vehicle Identification Numbers (VINs) and assessing market risk using intelligent algorithms and AI-powered natural language generation.

## Overview

The VIN Summary Generator processes vehicle data from CSV files and provides comprehensive risk assessments based on multiple market factors. The system uses a weighted scoring algorithm combined with Anthropic Claude 4.0 Sonnet for generating human-readable summaries and detailed reasoning.

## Key Features

### Core Functionality
- **VIN Analysis**: Analyze 17-character VINs to get comprehensive market risk assessments
- **Intelligent Risk Scoring**: Multi-factor algorithm considering:
  - Days on lot (DOL)
  - Price to market ratio
  - VDP views (online engagement metrics)
  - Mileage relative to vehicle age
  - Sales opportunities
- **AI-Powered Summaries**: Natural language generation using Anthropic Claude 4.0 Sonnet
- **Fallback Mechanism**: Automatic algorithmic generation when AI services are unavailable

### Technical Features
- **FastAPI Framework**: Modern, high-performance API with automatic documentation
- **Data Validation**: Robust input validation using Pydantic models
- **Error Handling**: Comprehensive error responses with appropriate HTTP status codes
- **Health Monitoring**: Real-time health checks and database statistics
- **Docker Support**: Production-ready containerization
- **Testing Suite**: Comprehensive unit and integration tests

## Requirements

- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn
- Anthropic API key (for LLM features)
- Docker (for containerized deployment)

## Architecture

The system follows a layered architecture pattern:

```
├── API Layer (FastAPI routes and middleware)
├── Core Business Logic (VIN analysis and risk engine)
├── Data Layer (CSV processing and models)
└── External Services (Anthropic Claude integration)
```
For detailed architecture diagrams, see [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md).

## Installation

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NivethaRajamani/vin-summary-generator.git
   cd vin-summary-generator
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env file and add your Anthropic API key
   # ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

5. **Run the application**:
   ```bash
   python -m uvicorn src.vin_analyzer.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc


### Docker Deployment

1. **Build the Docker image**:
   ```bash
   docker build -t vin-analyzer .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_api_key_here vin-analyzer
   ```

### Docker Compose

1. **Configure environment**:
   ```bash
   # Set your Anthropic API key in environment or .env file
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **Stop the service**:
   ```bash
   docker-compose down
   ```
## Data Format

The API expects vehicle data in CSV format with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| VIN | Vehicle Identification Number | `1HGCM82633A123456` |
| Year | Model year | `2018` |
| Make | Vehicle manufacturer | `HONDA` |
| Model | Vehicle model | `ACCORD` |
| Current price | Current price in USD | `$25,000` |
| Current price to market % | Price to market percentage | `95%` |
| DOL | Days on lot | `25` |
| Mileage | Vehicle mileage | `50,000` |
| Total VDPs (lifetime) | Total VDP views | `150` |
| Total sales opportunities (lifetime) | Sales opportunities | `5` |

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Analyze VIN
**POST** `/api/v1/analyze`

Analyze a VIN and get risk assessment.

<img width="783" height="484" alt="image" src="https://github.com/user-attachments/assets/4e7a1422-fd50-4dae-b16a-28b52f6f3fcb" />

<img width="1753" height="386" alt="image" src="https://github.com/user-attachments/assets/5d1b4169-bc7d-4979-b50a-076f0a505c8f" />


#### 2. Validate VIN
**POST** `/api/v1/validate`

Check if a VIN exists in the database.

**Request Body**:
```json
{
  "vin": "1HGCM82633A123456"
}
```

**Response**:
```json
{
  "vin": "1HGCM82633A123456",
  "exists": true,
  "message": "VIN found in database"
}
```

#### 3. Health Check
**GET** `/api/v1/health`

Check service health and get database statistics.

**Response**:
```json
{
  "status": "healthy",
  "message": "Service is operational",
  "database_stats": {
    "total_vehicles": 501,
    "makes": ["HONDA", "TOYOTA", "NISSAN", ...],
    "year_range": {"min": 2014, "max": 2026},
    "price_range": {"min": 6877, "max": 120399, "avg": 43287.5}
  }
}
```

#### 4. Database Statistics
**GET** `/api/v1/stats`

Get detailed database statistics.

**Response**:
```json
{
  "database_statistics": {
    "total_vehicles": 501,
    "makes": ["HONDA", "TOYOTA", "NISSAN", ...],
    "year_range": {"min": 2014, "max": 2026},
    "price_range": {"min": 6877, "max": 120399, "avg": 43287.5}
  },
  "message": "Database statistics retrieved successfully"
}
```

## Usage Examples

### cURL Examples

1. **Analyze a VIN**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analyze" \
        -H "Content-Type: application/json" \
        -d '{"vin": "1HGCM82633A123456"}'
   ```

2. **Validate a VIN**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/validate" \
        -H "Content-Type: application/json" \
        -d '{"vin": "1HGCM82633A123456"}'
   ```

3. **Health Check**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/health"
   ```

### Python Client Example

```python
import requests

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def analyze_vin(vin: str):
    """Analyze a VIN and get risk assessment."""
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={"vin": vin}
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Example usage
result = analyze_vin("1HGCM82633A123456")
if result:
    print(f"Risk Score: {result['risk_score']}")
    print(f"Summary: {result['summary']}")
    print(f"Reasoning: {result['reasoning']}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api/v1';

async function analyzeVin(vin) {
    try {
        const response = await axios.post(`${BASE_URL}/analyze`, {
            vin: vin
        });

        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        return null;
    }
}

// Example usage
analyzeVin('1HGCM82633A123456')
    .then(result => {
        if (result) {
            console.log(`Risk Score: ${result.risk_score}`);
            console.log(`Summary: ${result.summary}`);
            console.log(`Reasoning: ${result.reasoning}`);
        }
    });
```

## Testing

### Run Unit Tests
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov-report=html
```

### Run Linting
```bash
# Check code style
flake8 src/ tests/

# Format code (if using black)
black src/ tests/
```

### Test Coverage
- Unit tests for all core components
- Integration tests for API endpoints
- Mock testing for external services
- Error condition testing


## Risk Scoring Algorithm

The system uses a weighted scoring algorithm with the following factors:

### Base Score: 5 (Neutral Risk)

### Risk Factors:

1. **Days on Lot (DOL)**:
   - < 15 days: -2 (reduces risk)
   - 15-45 days: 0 (neutral)
   - > 45 days: +2 (increases risk)

2. **Price to Market (%)**:
   - ≤ 95%: -2 (below market, positive)
   - 96%-105%: 0 (at market, neutral)
   - > 105%: +2 (overpriced, negative)

3. **VDP Views**:
   - > 200: -1 (high engagement, reduces risk)
   - 50-200: 0 (moderate engagement, neutral)
   - < 50: +1 (low engagement, increases risk)

4. **Mileage**:
   - Below average for age: -1 (reduces risk)
   - Average for age: 0 (neutral)
   - Above average for age: +1 (increases risk)
   - New vehicle (0 miles): -1 (reduces risk)

5. **Sales Opportunities**:
   - > 10: -1 (many opportunities, reduces risk)
   - 3-10: 0 (moderate opportunities, neutral)
   - ≤ 2: +1 (few opportunities, increases risk)

| Factor | Low Risk | Neutral | High Risk |
|--------|----------|---------|-----------|
| **Days on Lot** | < 15 days (-2) | 15-45 days (0) | > 45 days (+2) |
| **Price to Market** | ≤ 95% (-2) | 96%-105% (0) | > 105% (+2) |
| **VDP Views** | > 200 (-1) | 50-200 (0) | < 50 (+1) |
| **Mileage** | Below average (-1) | Average (0) | Above average (+1) |
| **Sales Opportunities** | > 10 (-1) | 3-10 (0) | ≤ 2 (+1) |

### Final Score Calculation:
```
Final Score = Base Score (5) + Sum of Risk Factor Adjustments
Clamped between 1 (lowest risk) and 10 (highest risk)
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HOST` | Server host | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `CSV_DATA_PATH` | Path to CSV data file | Auto-detect | No |
| `ANTHROPIC_API_KEY` | Anthropic API key | None | Yes (for AI features) |
| `USE_LLM` | Enable/disable AI features | `true` | No |
| `RELOAD` | Enable auto-reload in development | `false` | No |

### LLM Configuration

The application uses Anthropic Claude 4.0 Sonnet for generating natural language summaries and reasoning:

- **Model**: Claude 3.5 Sonnet (configurable)
- **Fallback**: Automatic fallback to algorithmic generation if LLM fails
- **API Key**: Required for LLM features (set via `ANTHROPIC_API_KEY` environment variable)
- **Disable LLM**: Set `USE_LLM=false` to use only algorithmic generation

### Docker Environment

The Docker container uses the following configuration:
- Runs on port 8000
- Uses non-root user for security
- Includes health checks
- Optimized for production deployment
- Supports Anthropic API key via environment variables

## Project Structure

```
vin-summary-generator/
├── src/
│   └── vin_analyzer/
│       ├── api/              # FastAPI routes and main app
│       │   ├── main.py       # Application entry point
│       │   └── routes.py     # API endpoint definitions
│       ├── core/             # Business logic
│       │   ├── risk_engine.py    # Risk calculation engine
│       │   └── vin_analyzer.py   # Main orchestrator
│       ├── models/           # Data models
│       │   └── vehicle.py    # Pydantic models
│       └── utils/            # Utilities
│           ├── data_loader.py     # CSV processing
│           └── llm_service.py     # AI integration
├── tests/
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── config/                   # Configuration files
├── Dockerfile               # Container definition
├── docker-compose.yml       # Container orchestration
├── requirements.txt         # Python dependencies
├── sample_data.csv          # Sample vehicle data
└── README.md               # This file
```

## Error Handling

The API provides comprehensive error handling with appropriate HTTP status codes:

- **400 Bad Request**: Invalid request format
- **404 Not Found**: VIN not found in database
- **422 Unprocessable Entity**: Invalid VIN format or validation errors
- **500 Internal Server Error**: Server-side errors
- **503 Service Unavailable**: Service not properly initialized

Example error response:
```json
{
  "detail": "Vehicle with VIN 1HGCM82633A123456 not found"
}
```
## Performance Considerations

- **Memory Usage**: Entire CSV dataset loaded into memory for fast lookups
- **Response Time**: Typical response times < 100ms for cached data
- **Scalability**: Stateless design enables horizontal scaling
- **Caching**: Vehicle data cached in memory, AI responses can be cached

## Security Features

- **Input Validation**: All inputs validated using Pydantic schemas
- **Docker Security**: Non-root user, minimal container surface
- **API Security**: CORS middleware, rate limiting ready
- **Environment Variables**: Sensitive data managed via environment variables

## Monitoring and Observability

- **Health Endpoints**: Real-time service health monitoring
- **Database Statistics**: Insights into loaded data
- **Logging**: Structured logging for debugging and monitoring
- **Metrics**: Ready for Prometheus/Grafana integration

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Run tests and linting: `pytest && flake8 src/ tests/`
5. Commit your changes: `git commit -m "Add new feature"`
6. Push to the branch: `git push origin feature/new-feature`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support and Troubleshooting

### Common Issues

1. **CSV File Not Found**
   - Ensure `sample_data.csv` exists in the project root
   - Check `CSV_DATA_PATH` environment variable

2. **AI Features Not Working**
   - Verify `ANTHROPIC_API_KEY` is set correctly
   - Check API key permissions and quotas
   - Set `USE_LLM=false` to disable AI features

3. **Docker Issues**
   - Ensure Docker is running
   - Check port 8000 is not in use
   - Verify environment variables are passed correctly

### Getting Help

- Check the [API documentation](http://localhost:8000/docs) when running
- Review error messages in the logs
- Open an issue in the GitHub repository
- Consult the architecture diagram for system understanding

## Changelog

### v1.0.0
- Initial release with full VIN analysis functionality
- Anthropic Claude 4.0 Sonnet integration
- Comprehensive risk scoring algorithm
- Docker containerization
- Full test suite

---

**Built with**: FastAPI, Python 3.11+, Anthropic Claude 4.0 Sonnet, Docker
