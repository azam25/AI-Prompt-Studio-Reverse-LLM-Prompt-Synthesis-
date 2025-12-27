"""Prompt models for AI Prompt Studio."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ChatMLRole(str, Enum):
    """ChatML message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMLMessage(BaseModel):
    """A single ChatML message."""
    role: ChatMLRole
    content: str


class ChatMLPrompt(BaseModel):
    """Complete ChatML format prompt."""
    messages: List[ChatMLMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


class ExpectedOutput(BaseModel):
    """User's expected output definition with generic placeholders."""
    template: str = Field(
        ...,
        description="The expected output template with placeholders like {company_name}, {technology}"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of what the output should contain"
    )
    output_instructions: Optional[str] = Field(
        None,
        description="Instructions for response style: descriptive, precise, bullet points, etc."
    )
    examples: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional example outputs for reference"
    )
    output_format: Optional[str] = Field(
        "text",
        description="Expected format: text, json, table, list"
    )


class PromptOptimizationRequest(BaseModel):
    """Request to generate and optimize a prompt."""
    expected_output: ExpectedOutput
    document_ids: Optional[List[str]] = Field(
        default_factory=list,
        description="Specific document IDs to use, or empty for all"
    )


class RootCauseCategory(str, Enum):
    """Categories of root causes for prompt failures."""
    CONTEXT_MISSING = "context_missing"
    TERMINOLOGY_MISMATCH = "terminology_mismatch"
    STRUCTURE_MISMATCH = "structure_mismatch"
    AMBIGUITY = "ambiguity"
    RETRIEVAL_QUALITY = "retrieval_quality"


class EvaluationResult(BaseModel):
    """Result of evaluating a prompt iteration."""
    iteration: int
    generated_output: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    root_causes: List[RootCauseCategory] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    is_successful: bool = False


class OptimizationIteration(BaseModel):
    """A single iteration of the RLAIF optimization loop."""
    iteration: int
    query: str
    retrieved_contexts: List[str]
    generated_prompt: ChatMLPrompt
    evaluation: EvaluationResult


class PromptOptimizationResponse(BaseModel):
    """Response from prompt optimization."""
    final_prompt: ChatMLPrompt
    iterations: List[OptimizationIteration]
    total_iterations: int
    final_match_score: float
    status: str
    message: str
