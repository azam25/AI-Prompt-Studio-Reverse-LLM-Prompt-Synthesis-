"""ChatML formatter for creating OpenAI-compatible prompts."""
from typing import List, Optional

from app.config import settings
from app.models.prompt import (
    ChatMLPrompt,
    ChatMLMessage,
    ChatMLRole,
    ExpectedOutput
)
from app.models.evaluation import TemplateAnalysis


class ChatMLFormatter:
    """Format prompts in OpenAI ChatML format."""
    
    def create_prompt(
        self,
        expected_output: ExpectedOutput,
        query: str,
        contexts: List[str],
        template_analysis: Optional[TemplateAnalysis] = None
    ) -> ChatMLPrompt:
        """
        Create a ChatML format prompt.
        
        Args:
            expected_output: User's expected output definition
            query: The designed query
            contexts: Retrieved context chunks
            template_analysis: Optional analysis of the template
            
        Returns:
            ChatMLPrompt ready for use
        """
        # Build system message
        system_content = self._build_system_message(expected_output, template_analysis)
        
        # Build user message with context
        user_content = self._build_user_message(query, contexts, expected_output)
        
        messages = [
            ChatMLMessage(role=ChatMLRole.SYSTEM, content=system_content),
            ChatMLMessage(role=ChatMLRole.USER, content=user_content)
        ]
        
        # Read current settings dynamically (not cached)
        return ChatMLPrompt(
            messages=messages,
            model=settings.llm_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )
    
    def _build_system_message(
        self,
        expected_output: ExpectedOutput,
        template_analysis: Optional[TemplateAnalysis]
    ) -> str:
        """Build the system message for the prompt."""
        # Detect format characteristics
        template = expected_output.template
        has_numbered_list = any(line.strip().startswith(f"{i}.") for i in range(1, 10) for line in template.split('\n'))
        has_bullets = any(line.strip().startswith(('-', '•', '*')) for line in template.split('\n'))
        has_sections = ':' in template or '\n\n' in template
        
        parts = [
            "You are a precise information extraction assistant.",
            "Your PRIMARY task is to extract information from documents and format it EXACTLY according to the user's specified output template.",
            "",
            "## CRITICAL: Output Format Requirements",
            "You MUST follow the EXACT structure, format, and organization specified in the template below.",
            "",
            "### Expected Output Template:",
            "```",
            expected_output.template,
            "```",
        ]
        
        # Add format-specific instructions
        format_instructions = []
        if has_numbered_list:
            format_instructions.append("- Maintain the EXACT numbered list format (1., 2., 3., etc.)")
            format_instructions.append("- Keep the same number of points as specified in the template")
        if has_bullets:
            format_instructions.append("- Use the same bullet style as the template")
        if has_sections:
            format_instructions.append("- Preserve all section headers and structure")
        
        if format_instructions:
            parts.append("")
            parts.append("### Format Specifications:")
            parts.extend(format_instructions)
        
        if expected_output.description:
            parts.append("")
            parts.append(f"### Additional Context: {expected_output.description}")
        
        # Add user's output instructions (response style preferences)
        if expected_output.output_instructions:
            parts.append("")
            parts.append("## Response Style Instructions")
            parts.append("Follow these instructions for how to format and style your response:")
            for instruction in expected_output.output_instructions.strip().split('\n'):
                instruction = instruction.strip()
                if instruction:
                    # Add bullet if not already present
                    if not instruction.startswith(('-', '•', '*', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                        parts.append(f"- {instruction}")
                    else:
                        parts.append(instruction)
        
        if template_analysis and template_analysis.placeholders:
            parts.append("")
            parts.append("### Information to Extract:")
            for placeholder in template_analysis.placeholders:
                parts.append(f"- {placeholder.name}: Extract the {placeholder.detected_type} value")
        
        parts.extend([
            "",
            "## Instructions",
            "1. Read the provided context carefully",
            "2. Extract ONLY information explicitly stated in the context",
            "3. Fill each point/section in the template with relevant information from the context",
            "4. If specific information is not found, write 'Not specified in the document'",
            "5. **CRITICAL**: Your output MUST match the template structure EXACTLY - same headings, same numbered points, same format",
            "6. Do NOT add extra sections or change the organization",
            "7. Follow ALL response style instructions provided above"
        ])
        
        if expected_output.examples:
            parts.append("")
            parts.append("## Examples of Expected Output:")
            for i, example in enumerate(expected_output.examples, 1):
                parts.append(f"Example {i}: {example}")
        
        return "\n".join(parts)
    
    def _build_user_message(
        self,
        query: str,
        contexts: List[str],
        expected_output: ExpectedOutput
    ) -> str:
        """Build the user message with context and query."""
        parts = [
            "## Context",
            "The following information has been retrieved from the documents:",
            ""
        ]
        
        for i, context in enumerate(contexts, 1):
            parts.append(f"### Source {i}")
            parts.append(context)
            parts.append("")
        
        parts.extend([
            "## Query",
            query,
            "",
            "## Task",
            f"Based on the context above, provide the output in this exact format:",
            expected_output.template
        ])
        
        return "\n".join(parts)
    
    def format_for_export(self, prompt: ChatMLPrompt) -> dict:
        """
        Format prompt for export in standard OpenAI API format.
        
        Args:
            prompt: ChatMLPrompt to export
            
        Returns:
            Dictionary in OpenAI API format
        """
        return {
            "model": prompt.model,
            "messages": [
                {"role": m.role.value, "content": m.content}
                for m in prompt.messages
            ],
            "temperature": prompt.temperature,
            "max_tokens": prompt.max_tokens
        }
    
    def to_string(self, prompt: ChatMLPrompt) -> str:
        """
        Convert prompt to a readable string format.
        
        Args:
            prompt: ChatMLPrompt to convert
            
        Returns:
            Human-readable string representation
        """
        parts = []
        for message in prompt.messages:
            parts.append(f"<|{message.role.value}|>")
            parts.append(message.content)
            parts.append("")
        return "\n".join(parts)


# Singleton instance
chatml_formatter = ChatMLFormatter()


def get_chatml_formatter() -> ChatMLFormatter:
    """Get the ChatML formatter instance."""
    return chatml_formatter
