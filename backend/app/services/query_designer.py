"""Query designer service for generating queries from expected output templates."""
import re
from typing import List, Dict
from openai import OpenAI

from app.config import settings
from app.models.prompt import ExpectedOutput
from app.models.evaluation import TemplateAnalysis, PlaceholderInfo


class QueryDesigner:
    """Design queries based on expected output templates."""
    
    def __init__(self):
        self.client = None
        self._current_api_key = None
        self._current_base_url = None
    
    def _ensure_client(self):
        """Ensure OpenAI client is initialized and up-to-date."""
        # Reinitialize if settings have changed
        if (settings.openai_api_key and 
            (self._current_api_key != settings.openai_api_key or 
             self._current_base_url != settings.openai_base_url)):
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            self._current_api_key = settings.openai_api_key
            self._current_base_url = settings.openai_base_url
        
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please configure API key.")
    
    def analyze_template(self, expected_output: ExpectedOutput) -> TemplateAnalysis:
        """
        Analyze the expected output template to understand user intent.
        
        Args:
            expected_output: The user's expected output definition
            
        Returns:
            TemplateAnalysis with placeholders and requirements
        """
        template = expected_output.template
        
        # Extract placeholders using regex
        placeholder_pattern = r'\{([^}]+)\}'
        placeholder_names = re.findall(placeholder_pattern, template)
        
        placeholders = []
        for name in placeholder_names:
            # Infer type from naming conventions
            detected_type = self._infer_type(name)
            placeholders.append(PlaceholderInfo(
                name=name,
                detected_type=detected_type
            ))
        
        # Determine structure type
        structure_type = self._detect_structure(template, expected_output.output_format)
        
        # Generate information requirements
        info_requirements = self._generate_requirements(placeholders)
        
        # Generate initial query suggestions
        suggested_queries = self._generate_query_suggestions(
            placeholders, 
            expected_output.description
        )
        
        return TemplateAnalysis(
            placeholders=placeholders,
            structure_type=structure_type,
            information_requirements=info_requirements,
            suggested_queries=suggested_queries
        )
    
    def design_initial_query(
        self, 
        expected_output: ExpectedOutput,
        context_samples: List[str] = None
    ) -> str:
        """
        Design the initial query based on expected output analysis.
        
        Args:
            expected_output: User's expected output definition
            context_samples: Optional sample context for better query design
            
        Returns:
            Designed query string
        """
        self._ensure_client()
        
        # Build prompt for query design
        system_prompt = """You are an expert query designer for RAG (Retrieval-Augmented Generation) systems.
Your task is to analyze an expected output template and design a GENERIC, REUSABLE query that will retrieve 
the necessary information to fill in the template placeholders.

The expected output template uses placeholders like {company_name}, {technology}, etc.
These represent TYPES of information the user needs, not actual values.

CRITICAL RULES:
1. DO NOT reference specific document sections, chapter numbers, page numbers, or document structure
2. DO NOT mention "Chapter 1", "Section 3.2", "Appendix A", or any document-specific identifiers
3. Create queries that work across ANY document containing the relevant information
4. Use generic terminology that would match content in various documents
5. Focus on the TYPE of information needed, not WHERE it might be located

Your query should:
1. Target the specific types of information indicated by placeholders
2. Use common industry terminology likely to appear in various documents
3. Be generic enough to work on different documents about the same topic
4. Cover all the information needs in the template"""

        user_prompt = f"""Expected Output Template:
{expected_output.template}

Description: {expected_output.description or 'Not provided'}
Output Format: {expected_output.output_format}

Design a GENERIC query that will retrieve information to fill this template.
The query must NOT reference any specific document sections, chapters, or locations.
The query should work on ANY document containing this type of information.

Return ONLY the query text, nothing else."""

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    def refine_query(
        self,
        original_query: str,
        root_causes: List[str],
        improvement_suggestions: List[str],
        context_analysis: Dict
    ) -> str:
        """
        Refine a query based on evaluation feedback.
        
        Args:
            original_query: The query that was evaluated
            root_causes: Identified root causes of issues
            improvement_suggestions: Suggestions for improvement
            context_analysis: Analysis of retrieved context quality
            
        Returns:
            Refined query string
        """
        self._ensure_client()
        
        system_prompt = """You are an expert at refining RAG queries based on feedback.
Given an original query and evaluation feedback, create an improved query that addresses the issues.

CRITICAL: The refined query must be GENERIC and work on ANY document:
- DO NOT reference specific chapters, sections, pages, or document structure
- DO NOT mention document-specific identifiers like "Chapter 4", "Section 2.1", "Appendix B"
- Focus on improving the terminology and scope, not document navigation
- Create queries that would work on different documents about the same topic"""

        user_prompt = f"""Original Query:
{original_query}

Root Causes Identified:
{', '.join(root_causes)}

Improvement Suggestions:
{chr(10).join(f'- {s}' for s in improvement_suggestions)}

Context Analysis:
- Missing information: {context_analysis.get('missing_information', [])}
- Terminology gaps: {context_analysis.get('terminology_gaps', [])}

Create a GENERIC refined query that works on any document. 
DO NOT reference specific document sections or chapters.
Return ONLY the refined query text."""

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    def _infer_type(self, placeholder_name: str) -> str:
        """Infer the type of a placeholder from its name."""
        name_lower = placeholder_name.lower()
        
        if any(x in name_lower for x in ['date', 'time', 'year', 'month', 'day']):
            return 'date'
        elif any(x in name_lower for x in ['list', 'items', 'features', 'options']):
            return 'list'
        elif any(x in name_lower for x in ['count', 'number', 'amount', 'quantity', 'price', 'cost']):
            return 'number'
        elif any(x in name_lower for x in ['description', 'summary', 'details', 'text']):
            return 'text'
        else:
            return 'string'
    
    def _detect_structure(self, template: str, output_format: str) -> str:
        """Detect the structure type of the template."""
        if output_format and output_format != 'text':
            return output_format
        
        if template.strip().startswith('{') and template.strip().endswith('}'):
            return 'json'
        elif '|' in template and '-' in template:
            return 'table'
        elif template.count('\n-') > 2 or template.count('\n•') > 2:
            return 'list'
        else:
            return 'text'
    
    def _generate_requirements(self, placeholders: List[PlaceholderInfo]) -> List[str]:
        """Generate information requirements from placeholders."""
        requirements = []
        for p in placeholders:
            req = f"Need to find: {p.name.replace('_', ' ')} ({p.detected_type})"
            requirements.append(req)
        return requirements
    
    def _generate_query_suggestions(
        self, 
        placeholders: List[PlaceholderInfo],
        description: str = None
    ) -> List[str]:
        """Generate initial query suggestions."""
        suggestions = []
        
        # Generate query based on placeholders
        placeholder_names = [p.name.replace('_', ' ') for p in placeholders]
        main_query = f"What are the {', '.join(placeholder_names[:3])}?"
        suggestions.append(main_query)
        
        if description:
            suggestions.append(description)
        
        return suggestions


# Singleton instance
query_designer = QueryDesigner()


def get_query_designer() -> QueryDesigner:
    """Get the query designer instance."""
    return query_designer
