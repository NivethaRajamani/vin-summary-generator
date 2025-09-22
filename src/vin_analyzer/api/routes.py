"""FastAPI route definitions for VIN analysis API."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..core.vin_analyzer import VinAnalyzer
from ..models.vehicle import RiskAssessment, VehicleNotFoundError, VinRequest

# Create router
router = APIRouter()

# Global analyzer instance (will be initialized in main.py)
analyzer: VinAnalyzer = None


def set_analyzer(vin_analyzer: VinAnalyzer) -> None:
    """Set the global analyzer instance."""
    global analyzer
    analyzer = vin_analyzer


@router.post(
    "/analyze",
    response_model=RiskAssessment,
    summary="Analyze VIN for risk assessment",
    description="Analyze a Vehicle Identification Number (VIN) and return risk assessment with market summary.",
    responses={
        200: {
            "description": "Successful analysis",
            "content": {
                "application/json": {
                    "example": {
                        "summary": "This 2018 Honda Accord is priced slightly above market value but shows strong online engagement, indicating healthy buyer interest despite moderate days on lot.",
                        "risk_score": 4,
                        "reasoning": "Days on lot (25) is within normal range (neutral). Price is 5% above market (+2). VDP views are high (-1). Mileage is below average (-1). Overall score = 5 baseline +0 (days_on_lot) +2 (price_to_market) -1 (views) -1 (mileage) = 4."
                    }
                }
            }
        },
        404: {"description": "VIN not found in database"},
        422: {"description": "Invalid VIN format"}
    }
)
async def analyze_vin(request: VinRequest) -> RiskAssessment:
    """
    Analyze a VIN and return risk assessment.

    - **vin**: 17-character Vehicle Identification Number

    Returns a JSON object with:
    - **summary**: Human-readable market position summary
    - **risk_score**: Integer from 1 (low risk) to 10 (high risk)
    - **reasoning**: Detailed explanation of score calculation
    """
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not properly initialized"
        )

    try:
        assessment = analyzer.analyze_vin(request.vin)
        return assessment
    except VehicleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check if the service is running and operational.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service unavailable"}
    }
)
async def health_check():
    """Health check endpoint to verify service status."""
    if analyzer is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "message": "Service not initialized"}
        )

    try:
        stats = analyzer.get_database_stats()
        return {
            "status": "healthy",
            "message": "Service is operational",
            "database_stats": stats
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "message": f"Database error: {str(e)}"
            }
        )


@router.get(
    "/stats",
    summary="Get database statistics",
    description="Get statistics about the loaded vehicle database.",
    responses={
        200: {"description": "Database statistics"},
        503: {"description": "Service unavailable"}
    }
)
async def get_database_stats():
    """Get statistics about the loaded vehicle database."""
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not properly initialized"
        )

    try:
        stats = analyzer.get_database_stats()
        return {
            "database_statistics": stats,
            "message": "Database statistics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@router.post(
    "/validate",
    summary="Validate VIN exists",
    description="Check if a VIN exists in the database without performing full analysis.",
    responses={
        200: {"description": "VIN validation result"},
        422: {"description": "Invalid VIN format"}
    }
)
async def validate_vin(request: VinRequest):
    """
    Validate if a VIN exists in the database.

    - **vin**: 17-character Vehicle Identification Number

    Returns a JSON object with:
    - **vin**: The validated VIN
    - **exists**: Boolean indicating if VIN exists in database
    """
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not properly initialized"
        )

    try:
        exists = analyzer.validate_vin_exists(request.vin)
        return {
            "vin": request.vin,
            "exists": exists,
            "message": "VIN found in database" if exists else "VIN not found in database"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating VIN: {str(e)}"
        )