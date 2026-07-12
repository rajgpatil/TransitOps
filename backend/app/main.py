import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.vehicles import router as vehicles_router
from app.api.drivers import router as drivers_router
from app.api.trips import router as trips_router
from app.api.maintenance import router as maintenance_router
from app.api.fuel_logs import router as fuel_logs_router
from app.api.expenses import router as expenses_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(vehicles_router, prefix=f"{settings.API_V1_STR}/vehicles", tags=["vehicles"])
app.include_router(drivers_router, prefix=f"{settings.API_V1_STR}/drivers", tags=["drivers"])
app.include_router(trips_router, prefix=f"{settings.API_V1_STR}/trips", tags=["trips"])
app.include_router(maintenance_router, prefix=f"{settings.API_V1_STR}/maintenance", tags=["maintenance"])
app.include_router(fuel_logs_router, prefix=f"{settings.API_V1_STR}/fuel-logs", tags=["fuel-logs"])
app.include_router(expenses_router, prefix=f"{settings.API_V1_STR}/expenses", tags=["expenses"])

# CORS middleware configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Exception handler for Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error for path {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "detail": exc.errors(),
            "message": "Input validation failed. Please check your request fields."
        }),
    )


# Global exception handler for unhandled server errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing request {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "An unexpected error occurred on the server. Please try again later."
        },
    )


# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}
