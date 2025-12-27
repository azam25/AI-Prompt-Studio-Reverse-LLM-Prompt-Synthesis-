"""RLAIF Optimizer - Core optimization loop for prompt refinement."""
from typing import List, Optional
import logging

from app.config import settings
from app.models.prompt import (
    ExpectedOutput,
    ChatMLPrompt,
    ChatMLMessage,
    ChatMLRole,
    OptimizationIteration,
    PromptOptimizationResponse,
    EvaluationResult
)
from app.models.document import RetrievedContext
from app.services.vector_store import get_vector_store
from app.services.query_designer import get_query_designer
from app.services.evaluation_llm import get_evaluation_llm
from app.services.chatml_formatter import get_chatml_formatter

logger = logging.getLogger(__name__)


class RLAIFOptimizer:
    """
    RLAIF (Reinforcement Learning from AI Feedback) Optimizer.
    
    Implements an iterative optimization loop that:
    1. Designs a query from expected output
    2. Retrieves relevant context
    3. Generates a prompt and tests it
    4. Evaluates the output
    5. Refines the query based on feedback
    6. Repeats until success or max iterations
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.query_designer = get_query_designer()
        self.evaluation_llm = get_evaluation_llm()
        self.chatml_formatter = get_chatml_formatter()
        
        self.min_iterations = settings.min_optimization_iterations
        self.max_iterations = settings.max_optimization_iterations
        self.success_threshold = 0.85  # Match score threshold for success
    
    def optimize(
        self,
        expected_output: ExpectedOutput,
        document_ids: Optional[List[str]] = None
    ) -> PromptOptimizationResponse:
        """
        Run the RLAIF optimization loop.
        
        Args:
            expected_output: User's expected output definition
            document_ids: Optional filter for specific documents
            
        Returns:
            PromptOptimizationResponse with final prompt and iteration history
        """
        iterations: List[OptimizationIteration] = []
        current_query = ""
        best_prompt: Optional[ChatMLPrompt] = None
        best_score = 0.0
        best_iteration_num = 0
        
        # Analyze the template first
        template_analysis = self.query_designer.analyze_template(expected_output)
        logger.info(f"Template analysis: {len(template_analysis.placeholders)} placeholders found")
        
        # Get initial context samples for query design
        initial_contexts = self._get_sample_contexts(document_ids)
        
        # Design initial query
        current_query = self.query_designer.design_initial_query(
            expected_output,
            context_samples=[c.content for c in initial_contexts]
        )
        logger.info(f"Initial query designed: {current_query[:100]}...")
        
        for iteration_num in range(1, self.max_iterations + 1):
            logger.info(f"Starting iteration {iteration_num}")
            
            # Step 1: Retrieve context using current query
            retrieved_contexts = self.vector_store.search(
                query=current_query,
                top_k=5,
                document_ids=document_ids
            )
            
            context_texts = [ctx.content for ctx in retrieved_contexts]
            logger.info(f"Retrieved {len(context_texts)} context chunks")
            
            # Step 2: Generate prompt with retrieved context
            prompt = self.chatml_formatter.create_prompt(
                expected_output=expected_output,
                query=current_query,
                contexts=context_texts,
                template_analysis=template_analysis
            )
            
            # Step 3: Generate output using the prompt
            generated_output = self.evaluation_llm.generate_output(prompt)
            logger.info(f"Generated output: {generated_output[:100]}...")
            
            # Step 4: Evaluate the output
            evaluation = self.evaluation_llm.evaluate(
                generated_output=generated_output,
                expected_output=expected_output,
                retrieved_contexts=context_texts,
                iteration=iteration_num
            )
            logger.info(f"Evaluation score: {evaluation.match_score}")
            
            # Record iteration
            iteration_record = OptimizationIteration(
                iteration=iteration_num,
                query=current_query,
                retrieved_contexts=context_texts,
                generated_prompt=prompt,
                evaluation=evaluation
            )
            iterations.append(iteration_record)
            
            # Track best result
            if evaluation.match_score > best_score:
                best_score = evaluation.match_score
                best_prompt = prompt
                best_iteration_num = iteration_num
                logger.info(f"New best score: {best_score} at iteration {best_iteration_num}")
            
            # Check if we've achieved success
            if evaluation.is_successful and evaluation.match_score >= self.success_threshold:
                if iteration_num >= self.min_iterations:
                    logger.info(f"Optimization successful at iteration {iteration_num}")
                    # Use best prompt even if success happens on a lower-scoring iteration
                    return self._create_response(
                        final_prompt=best_prompt or prompt,
                        iterations=iterations,
                        best_score=best_score,
                        best_iteration=best_iteration_num,
                        status="success",
                        message=f"Optimization successful! Best score: {best_score:.2f} (iteration {best_iteration_num})"
                    )
            
            # Step 5: Refine query for next iteration (if not at max)
            if iteration_num < self.max_iterations:
                # Analyze context quality
                context_analysis = self.evaluation_llm.analyze_context_quality(
                    expected_output=expected_output,
                    retrieved_contexts=context_texts
                )
                
                # Refine the query
                current_query = self.query_designer.refine_query(
                    original_query=current_query,
                    root_causes=[rc.value for rc in evaluation.root_causes],
                    improvement_suggestions=evaluation.improvement_suggestions,
                    context_analysis={
                        'missing_information': context_analysis.missing_information,
                        'terminology_gaps': context_analysis.terminology_gaps
                    }
                )
                logger.info(f"Refined query: {current_query[:100]}...")
        
        # Return best result after all iterations
        logger.info(f"Optimization completed. Best score: {best_score} from iteration {best_iteration_num}")
        return self._create_response(
            final_prompt=best_prompt or iterations[-1].generated_prompt,
            iterations=iterations,
            best_score=best_score,
            best_iteration=best_iteration_num,
            status="completed" if best_score >= 0.7 else "needs_improvement",
            message=f"Completed {len(iterations)} iterations. Best score: {best_score:.2f} (from iteration {best_iteration_num})"
        )
    
    def _get_sample_contexts(
        self, 
        document_ids: Optional[List[str]] = None,
        sample_size: int = 3
    ) -> List[RetrievedContext]:
        """Get sample contexts for initial query design."""
        # Use a generic query to get some sample content
        return self.vector_store.search(
            query="main content summary overview",
            top_k=sample_size,
            document_ids=document_ids
        )
    
    def _create_response(
        self,
        final_prompt: ChatMLPrompt,
        iterations: List[OptimizationIteration],
        best_score: float,
        best_iteration: int,
        status: str,
        message: str
    ) -> PromptOptimizationResponse:
        """Create the optimization response."""
        return PromptOptimizationResponse(
            final_prompt=final_prompt,
            iterations=iterations,
            total_iterations=len(iterations),
            final_match_score=best_score,  # Use best score, not last iteration
            status=status,
            message=message
        )


# Singleton instance
rlaif_optimizer = RLAIFOptimizer()


def get_rlaif_optimizer() -> RLAIFOptimizer:
    """Get the RLAIF optimizer instance."""
    return rlaif_optimizer
