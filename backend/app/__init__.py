"""FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, prompts, config as config_routes


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Prompt Studio",
        description="Intelligent prompt engineering platform with RLAIF optimization",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
    app.include_router(prompts.router, prefix="/api/prompts", tags=["Prompts"])
    app.include_router(config_routes.router, prefix="/api/config", tags=["Configuration"])
    
    @app.get("/")
    async def root():
        return {"message": "AI Prompt Studio API", "version": "1.0.0"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app
