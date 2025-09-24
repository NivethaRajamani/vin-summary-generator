# VIN Risk Analyzer - Architecture Diagram

## System Architecture

```mermaid
graph TB
    subgraph "External Dependencies"
        CSV[CSV Data File<br/>sample_data.csv]
        ANTHROPIC[Anthropic Claude API<br/>Sonnet 4.0]
    end

    subgraph "FastAPI Application"
        subgraph "API Layer"
            MAIN[main.py<br/>FastAPI App<br/>Lifespan Management]
            ROUTES[routes.py<br/>API Endpoints<br/>- /analyze<br/>- /validate<br/>- /health<br/>- /stats]
        end

        subgraph "Core Business Logic"
            ANALYZER[vin_analyzer.py<br/>VinAnalyzer<br/>Main Orchestrator]
            RISK[risk_engine.py<br/>RiskEngine<br/>Risk Calculation Logic]
        end

        subgraph "Data Layer"
            LOADER[data_loader.py<br/>DataLoader<br/>CSV Parsing & Validation]
            MODELS[vehicle.py<br/>Pydantic Models<br/>- VehicleData<br/>- RiskAssessment<br/>- VinRequest]
        end

        subgraph "External Services"
            LLM[llm_service.py<br/>LLMService<br/>Anthropic Integration]
        end
    end

    subgraph "Containerization"
        DOCKER[Docker Container<br/>- Multi-stage build<br/>- Non-root user<br/>- Health checks]
        COMPOSE[Docker Compose<br/>Environment management]
    end

    subgraph "Testing"
        UNIT[Unit Tests<br/>- test_risk_engine.py<br/>- test_llm_service.py<br/>- test_data_loader.py<br/>- test_models.py]
        INTEGRATION[Integration Tests<br/>- test_api.py]
    end

    %% Data Flow
    CSV --> LOADER
    LOADER --> ANALYZER
    ANALYZER --> RISK
    RISK --> LLM
    LLM --> ANTHROPIC

    %% API Flow
    MAIN --> ROUTES
    ROUTES --> ANALYZER
    ANALYZER --> MODELS

    %% Dependencies
    RISK --> MODELS
    LOADER --> MODELS
    ROUTES --> MODELS

    %% Deployment
    MAIN --> DOCKER
    DOCKER --> COMPOSE

    %% Testing Dependencies
    UNIT --> RISK
    UNIT --> LLM
    UNIT --> LOADER
    UNIT --> MODELS
    INTEGRATION --> ROUTES

    %% Styling
    classDef apiLayer fill:#e1f5fe,stroke:#01579b
    classDef coreLogic fill:#f3e5f5,stroke:#4a148c
    classDef dataLayer fill:#e8f5e8,stroke:#1b5e20
    classDef external fill:#fff3e0,stroke:#e65100
    classDef container fill:#fce4ec,stroke:#880e4f
    classDef testing fill:#f1f8e9,stroke:#33691e

    class MAIN,ROUTES apiLayer
    class ANALYZER,RISK coreLogic
    class LOADER,MODELS dataLayer
    class CSV,ANTHROPIC,LLM external
    class DOCKER,COMPOSE container
    class UNIT,INTEGRATION testing
```

## Component Descriptions

### API Layer
- **main.py**: FastAPI application entry point with lifespan management, CORS, and startup/shutdown logic
- **routes.py**: REST API endpoints with comprehensive error handling and validation

### Core Business Logic
- **vin_analyzer.py**: Main orchestrator that coordinates between data loading, risk calculation, and LLM services
- **risk_engine.py**: Implements the weighted risk scoring algorithm with multiple factors and fallback mechanisms

### Data Layer
- **data_loader.py**: Handles CSV parsing, data cleaning, and vehicle lookup operations
- **vehicle.py**: Pydantic models for data validation and serialization

### External Services
- **llm_service.py**: Manages integration with Anthropic Claude API for natural language generation

### Key Features
- **Graceful Degradation**: LLM failures fall back to algorithmic output generation
- **Comprehensive Validation**: Input validation at multiple layers using Pydantic
- **Error Handling**: Structured error responses with appropriate HTTP status codes
- **Health Monitoring**: Health check endpoints with database statistics
- **Containerization**: Production-ready Docker setup with security best practices

## Risk Scoring Algorithm

```mermaid
graph LR
    START[Base Score: 5] --> DOL[Days on Lot<br/>-2 to +2]
    DOL --> PRICE[Price to Market<br/>-2 to +2]
    PRICE --> VIEWS[VDP Views<br/>-1 to +1]
    VIEWS --> MILEAGE[Mileage Impact<br/>-1 to +1]
    MILEAGE --> SALES[Sales Opportunities<br/>-1 to +1]
    SALES --> CLAMP[Clamp to 1-10]
    CLAMP --> FINAL[Final Risk Score]

    classDef score fill:#e3f2fd,stroke:#0277bd
    classDef factor fill:#f9fbe7,stroke:#827717
    classDef result fill:#ffebee,stroke:#c62828

    class START,FINAL result
    class DOL,PRICE,VIEWS,MILEAGE,SALES factor
    class CLAMP score
```

## Data Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Routes
    participant Analyzer as VinAnalyzer
    participant Loader as DataLoader
    participant Risk as RiskEngine
    participant LLM as LLMService
    participant Claude as Anthropic API

    Client->>API: POST /analyze {vin}
    API->>Analyzer: analyze_vin(vin)
    Analyzer->>Loader: get_vehicle_by_vin(vin)
    Loader-->>Analyzer: VehicleData
    Analyzer->>Risk: assess_risk(vehicle)
    Risk->>Risk: calculate_risk_factors()

    alt LLM Enabled
        Risk->>LLM: generate_risk_assessment()
        LLM->>Claude: API Request
        Claude-->>LLM: LLM Response
        LLM-->>Risk: Formatted Output
    else LLM Disabled/Failed
        Risk->>Risk: algorithmic_generation()
    end

    Risk-->>Analyzer: RiskAssessment
    Analyzer-->>API: RiskAssessment
    API-->>Client: JSON Response
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV[Local Development<br/>Python venv<br/>uvicorn --reload]
    end

    subgraph "Production"
        subgraph "Container"
            APP[FastAPI App<br/>Port 8000]
            HEALTH[Health Checks<br/>/api/v1/health]
        end

        subgraph "Environment"
            ENV[Environment Variables<br/>- ANTHROPIC_API_KEY<br/>- USE_LLM<br/>- CSV_DATA_PATH]
        end
    end

    subgraph "Data Sources"
        CSV_FILE[CSV Data File<br/>Vehicle Database]
        API_KEY[Anthropic API<br/>External Service]
    end

    ENV --> APP
    CSV_FILE --> APP
    API_KEY --> APP
    HEALTH --> APP

    classDef dev fill:#e8f5e8,stroke:#2e7d32
    classDef prod fill:#e3f2fd,stroke:#1565c0
    classDef data fill:#fff8e1,stroke:#f57f17

    class DEV dev
    class APP,HEALTH,ENV prod
    class CSV_FILE,API_KEY data
```