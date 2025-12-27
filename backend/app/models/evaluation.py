"""Evaluation models for AI Prompt Studio."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class PlaceholderInfo(BaseModel):
    """Information about a placeholder in the expected output template."""
    name: str
    description: Optional[str] = None
    detected_type: str = "string"  # string, number, list, date, etc.


class TemplateAnalysis(BaseModel):
    """Analysis of the user's expected output template."""
    placeholders: List[PlaceholderInfo]
    structure_type: str  # text, json, table, list
    information_requirements: List[str]
    suggested_queries: List[str]


class QueryRefinement(BaseModel):
    """A refined query based on evaluation feedback."""
    original_query: str
    refined_query: str
    refinement_reason: str
    target_root_cause: str


class ContextQualityAssessment(BaseModel):
    """Assessment of retrieved context quality."""
    total_chunks: int
    relevant_chunks: int
    relevance_score: float
    missing_information: List[str]
    terminology_gaps: List[str]
