"""FastAPI application main module."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.vin_analyzer import VinAnalyzer
from .routes import router, set_analyzer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    try:
        # Get configuration from environment
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        use_llm = os.getenv("USE_LLM", "true").lower() == "true"

        # Try to find sample_data.csv file
        csv_path = os.getenv("CSV_DATA_PATH")
        if csv_path and Path(csv_path).exists():
            analyzer = VinAnalyzer(
                csv_path, use_llm=use_llm, anthropic_api_key=anthropic_api_key
            )
        else:
            # Try to find sample_data.csv in project root
            current_path = Path(__file__).parent
            while current_path.parent != current_path:
                sample_data_path = current_path / "sample_data.csv"
                if sample_data_path.exists():
                    analyzer = VinAnalyzer(
                        str(sample_data_path),
                        use_llm=use_llm,
                        anthropic_api_key=anthropic_api_key,
                    )
                    break
                current_path = current_path.parent
            else:
                # Fallback to relative path
                sample_data_path = Path("sample_data.csv")
                if sample_data_path.exists():
                    analyzer = VinAnalyzer(
                        str(sample_data_path),
                        use_llm=use_llm,
                        anthropic_api_key=anthropic_api_key,
                    )
                else:
                    raise FileNotFoundError("Could not find sample_data.csv file")

        set_analyzer(analyzer)
        print(
            f"Loaded {analyzer.get_database_stats()['total_vehicles']} vehicles from CSV"
        )

    except Exception as e:
        print(f"Error initializing analyzer: {e}")
        raise

    yield

    # Shutdown
    print("Shutting down VIN analyzer service")


# Create FastAPI application
app = FastAPI(
    title="VIN Risk Analyzer API",
    description="""
    A RESTful API for analyzing Vehicle Identification Numbers (VINs) and assessing market risk.

    ## Features

    * **VIN Analysis**: Analyze a 17-character VIN to get market risk assessment
    * **Risk Scoring**: Intelligent scoring based on multiple factors:
        - Days on lot
        - Price to market ratio
        - VDP views (online engagement)
        - Mileage relative to vehicle age
        - Sales opportunities
    * **Market Summary**: Human-readable summary of vehicle's market position
    * **Health Monitoring**: Health check and database statistics endpoints

    ## Usage

    Send a POST request to `/analyze` with a VIN to get a comprehensive risk assessment.
    The API returns a JSON object with a market summary, risk score (1-10), and detailed reasoning.

    ## Data Sources

    The API uses vehicle data from CSV files containing make, model, year, pricing, and market metrics.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["VIN Analysis"])


@app.get("/", summary="API Root", description="Root endpoint with API information.")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "VIN Risk Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "validate": "POST /api/v1/validate",
            "stats": "GET /api/v1/stats",
            "health": "GET /api/v1/health",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    print(f"Starting VIN Analyzer API on {host}:{port}")
    uvicorn.run(
        "src.vin_analyzer.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
