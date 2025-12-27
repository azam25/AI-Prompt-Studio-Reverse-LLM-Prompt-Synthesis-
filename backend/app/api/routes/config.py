"""Configuration API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.services.embedding_service import get_embedding_service

router = APIRouter()


class LLMConfigRequest(BaseModel):
    """Request to update LLM configuration."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    embedding_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class LLMConfigResponse(BaseModel):
    """Response with current LLM configuration."""
    base_url: str
    model: str
    embedding_model: str
    temperature: float
    max_tokens: int
    is_configured: bool


@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config():
    """Get current LLM configuration (without API key for security)."""
    return LLMConfigResponse(
        base_url=settings.openai_base_url,
        model=settings.llm_model,
        embedding_model=settings.embedding_model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        is_configured=bool(settings.openai_api_key)
    )


@router.post("/llm", response_model=LLMConfigResponse)
async def update_llm_config(request: LLMConfigRequest):
    """Update LLM configuration."""
    if request.api_key:
        settings.openai_api_key = request.api_key
    if request.base_url:
        settings.openai_base_url = request.base_url
    if request.model:
        settings.llm_model = request.model
    if request.embedding_model:
        settings.embedding_model = request.embedding_model
    if request.temperature is not None:
        settings.temperature = request.temperature
    if request.max_tokens is not None:
        settings.max_tokens = request.max_tokens
    
    # Reinitialize embedding service with new config
    embedding_service = get_embedding_service()
    embedding_service.update_config(
        api_key=request.api_key,
        base_url=request.base_url,
        model=request.embedding_model
    )
    
    return LLMConfigResponse(
        base_url=settings.openai_base_url,
        model=settings.llm_model,
        embedding_model=settings.embedding_model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        is_configured=bool(settings.openai_api_key)
    )


@router.post("/test-connection")
async def test_connection():
    """Test connection to the configured LLM."""
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="API key not configured")
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        
        # Simple test call
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
            max_tokens=10
        )
        
        return {
            "status": "connected",
            "model": settings.llm_model,
            "response": response.choices[0].message.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.get("/optimization")
async def get_optimization_config():
    """Get optimization settings."""
    return {
        "min_iterations": settings.min_optimization_iterations,
        "max_iterations": settings.max_optimization_iterations,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap
    }
