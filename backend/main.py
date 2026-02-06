"""
ExportSathi Backend - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from routers import reports, certifications, documents, finance, logistics, action_plan, chat, users
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="ExportSathi API",
    description="AI-Powered Export Compliance & Certification Co-Pilot",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(certifications.router, prefix="/api/certifications", tags=["certifications"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(finance.router, prefix="/api/finance", tags=["finance"])
app.include_router(logistics.router, prefix="/api/logistics", tags=["logistics"])
app.include_router(action_plan.router, prefix="/api/action-plan", tags=["action-plan"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ExportSathi API"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "api": "operational",
            "database": "operational",
            "vector_store": "operational"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
