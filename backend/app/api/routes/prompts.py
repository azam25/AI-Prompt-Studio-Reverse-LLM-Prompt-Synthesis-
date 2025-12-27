"""Prompt optimization API routes."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.prompt import (
    ExpectedOutput,
    PromptOptimizationRequest,
    PromptOptimizationResponse,
    ChatMLPrompt
)
from app.services.rlaif_optimizer import get_rlaif_optimizer
from app.services.chatml_formatter import get_chatml_formatter
from app.services.query_designer import get_query_designer

router = APIRouter()


class AnalyzeTemplateRequest(BaseModel):
    """Request to analyze an expected output template."""
    template: str
    description: Optional[str] = None
    output_format: Optional[str] = "text"


@router.post("/optimize", response_model=PromptOptimizationResponse)
async def optimize_prompt(request: PromptOptimizationRequest):
    """
    Run RLAIF optimization to generate an optimized prompt.
    
    This endpoint:
    1. Analyzes the expected output template
    2. Designs an initial query
    3. Runs iterative optimization (min 3 iterations)
    4. Returns the optimized prompt in ChatML format
    """
    try:
        optimizer = get_rlaif_optimizer()
        result = optimizer.optimize(
            expected_output=request.expected_output,
            document_ids=request.document_ids if request.document_ids else None
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/analyze")
async def analyze_template(request: AnalyzeTemplateRequest):
    """
    Analyze an expected output template without running optimization.
    
    Returns:
    - Detected placeholders and their types
    - Structure analysis
    - Initial query suggestions
    """
    try:
        query_designer = get_query_designer()
        expected_output = ExpectedOutput(
            template=request.template,
            description=request.description,
            output_format=request.output_format
        )
        analysis = query_designer.analyze_template(expected_output)
        return {
            "placeholders": [
                {"name": p.name, "type": p.detected_type}
                for p in analysis.placeholders
            ],
            "structure_type": analysis.structure_type,
            "information_requirements": analysis.information_requirements,
            "suggested_queries": analysis.suggested_queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/export")
async def export_prompt(prompt: ChatMLPrompt):
    """
    Export a prompt in various formats.
    
    Returns the prompt in OpenAI API compatible JSON format.
    """
    formatter = get_chatml_formatter()
    return {
        "openai_format": formatter.format_for_export(prompt),
        "readable": formatter.to_string(prompt)
    }


@router.post("/test")
async def test_prompt(prompt: ChatMLPrompt):
    """
    Test a prompt by generating output.
    
    Useful for validating the generated prompt before export.
    """
    try:
        from app.services.evaluation_llm import get_evaluation_llm
        evaluation_llm = get_evaluation_llm()
        output = evaluation_llm.generate_output(prompt)
        return {
            "output": output,
            "prompt": prompt.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
