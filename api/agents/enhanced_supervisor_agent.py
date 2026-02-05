"""
Enhanced Supervisor Agent

A standalone supervisor that evaluates agent outputs and automatically retries agents
with improved context when quality standards are not met.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import sys
import os

# Add the api directory to the path
from api.utils.llm_backends import get_llm_backend
from api.agents.supervisor_prompts.assessment_templates import AssessmentTemplates

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retry_attempts: int = 2
    quality_threshold: float = 0.7
    purpose_alignment_threshold: float = 0.6
    relevance_threshold: float = 0.65
    completeness_threshold: float = 0.6
    strategic_value_threshold: float = 0.5

@dataclass
class RetryHistory:
    """Track retry history for an agent."""
    agent_type: str
    attempt_number: int
    assessment: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    improvement_applied: bool = False

@dataclass
class EnhancedQualityAssessment:
    """Simplified quality assessment with essential fields."""
    status: str  # APPROVE, REVISE, HALT
    quality_score: float
    confidence: float
    issues_found: List[str]
    improvement_suggestions: List[str]
    enhanced_context_prompt: str
    assessment_reasoning: str = ""

    def __post_init__(self):
        if self.issues_found is None:
            self.issues_found = []
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []

@dataclass
class SupervisorResult:
    """Complete supervisor result including evaluation and retry output."""
    initial_assessment: EnhancedQualityAssessment
    final_assessment: Optional[EnhancedQualityAssessment] = None
    retry_output: Optional[Dict[str, Any]] = None
    retry_attempts: int = 0
    final_status: str = "APPROVED"  # APPROVED, IMPROVED, HALTED
    final_message: str = ""

class EnhancedSupervisorAgent:
    """
    Enhanced supervisor agent with standalone retry capabilities.
    """
    
    def __init__(self, llm_backend=None, retry_config: RetryConfig = None):
        self.llm_backend = llm_backend or get_llm_backend("openai")
        self.retry_config = retry_config or RetryConfig()
        self.retry_history: Dict[str, List[RetryHistory]] = {}
        self.learning_context: Dict[str, Any] = {}
        
        # Initialize agent instances for retry
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agent instances for retry functionality."""
        try:
            from api.agents.data_extractor_agent import DataExtractorAgent
            from api.agents.literature_review_agent import LiteratureReviewAgent
            from api.agents.initial_coding_agent import InitialCodingAgent
            from api.agents.thematic_grouping_agent import ThematicGroupingAgent
            from api.agents.theme_refiner_agent import ThemeRefinerAgent
            from api.agents.report_generator_agent import ReportGeneratorAgent
            
            self.agents = {
                "data_extractor": DataExtractorAgent(),
                "literature_review": LiteratureReviewAgent(),
                "initial_coding": InitialCodingAgent(),
                "thematic_grouping": ThematicGroupingAgent(),
                "theme_refinement": ThemeRefinerAgent(),
                "report_generator": ReportGeneratorAgent()
            }
        except ImportError as e:
            print(f"[WARNING] Could not initialize agents for retry: {e}")
            self.agents = {}
    
    def _get_retry_config_for_agent(self, agent_type: str) -> RetryConfig:
        """Get retry configuration for specific agent type."""
        # Agent-specific configurations
        agent_configs = {
            "data_extractor": RetryConfig(
                max_retry_attempts=3,
                quality_threshold=0.6,
                purpose_alignment_threshold=0.7,
                relevance_threshold=0.7,
                completeness_threshold=0.5,
                strategic_value_threshold=0.5
            ),
            "literature_review": RetryConfig(
                max_retry_attempts=2,
                quality_threshold=0.75,
                purpose_alignment_threshold=0.7,
                relevance_threshold=0.7,
                completeness_threshold=0.7,
                strategic_value_threshold=0.6
            ),
            "initial_coding": RetryConfig(
                max_retry_attempts=2,
                quality_threshold=0.7,
                purpose_alignment_threshold=0.65,
                relevance_threshold=0.7,
                completeness_threshold=0.6,
                strategic_value_threshold=0.5
            ),
            "thematic_grouping": RetryConfig(
                max_retry_attempts=2,
                quality_threshold=0.7,
                purpose_alignment_threshold=0.7,
                relevance_threshold=0.7,
                completeness_threshold=0.6,
                strategic_value_threshold=0.6
            ),
            "theme_refinement": RetryConfig(
                max_retry_attempts=2,
                quality_threshold=0.75,
                purpose_alignment_threshold=0.7,
                relevance_threshold=0.7,
                completeness_threshold=0.7,
                strategic_value_threshold=0.6
            ),
            "report_generator": RetryConfig(
                max_retry_attempts=2,
                quality_threshold=0.8,
                purpose_alignment_threshold=0.75,
                relevance_threshold=0.75,
                completeness_threshold=0.8,
                strategic_value_threshold=0.7
            )
        }
        
        return agent_configs.get(agent_type, self.retry_config)
    
    def _store_retry_history(self, agent_type: str, attempt_number: int, assessment: EnhancedQualityAssessment):
        """Store retry history for learning."""
        if agent_type not in self.retry_history:
            self.retry_history[agent_type] = []
        
        retry_record = RetryHistory(
            agent_type=agent_type,
            attempt_number=attempt_number,
            assessment=assessment.__dict__,
            improvement_applied=assessment.status == "REVISE"  # If status is REVISE, improvement was needed
        )
        
        self.retry_history[agent_type].append(retry_record)
    
    def _get_retry_history_for_agent(self, agent_type: str) -> List[RetryHistory]:
        """Get retry history for an agent."""
        return self.retry_history.get(agent_type, [])
    
    def _build_learning_context(self, agent_type: str) -> Dict[str, Any]:
        """Build learning context from previous attempts."""
        history = self._get_retry_history_for_agent(agent_type)
        
        if not history:
            return {}
        
        # Analyze patterns in previous attempts
        common_issues = []
        successful_improvements = []
        
        for record in history:
            assessment = record.assessment
            if assessment.get('issues_found'):
                common_issues.extend(assessment['issues_found'])
            if record.improvement_applied and assessment.get('improvement_suggestions'):
                successful_improvements.extend(assessment['improvement_suggestions'])
        
        return {
            "total_attempts": len(history),
            "common_issues": list(set(common_issues)),
            "successful_improvements": list(set(successful_improvements)),
            "last_assessment": history[-1].assessment if history else None
        }
    
    async def evaluate_quality(self, agent_output: Dict[str, Any], agent_type: str,
                              agent_input: Dict[str, Any] = None, original_agent_input: Dict[str, Any] = None) -> SupervisorResult:
        """
        Evaluate agent output quality only.
        
        Args:
            agent_output: Output from the agent to evaluate
            agent_type: Type of agent that produced the output
            agent_input: Optional modified input (not used in evaluation-only mode)
            original_agent_input: Original input sent to the agent
            
        Returns:
            SupervisorResult with evaluation information
        """
        print(f"[ENHANCED SUPERVISOR] Evaluating {agent_type} quality")
        
        # Extract research domain and user query from agent output or original input
        research_domain = agent_output.get("research_domain", "General")
        
        # Try to get user_query from different possible locations
        user_query = ""
        if original_agent_input:
            user_query = original_agent_input.get("user_query", "")
            if not user_query:
                # Try to extract from research_domain if it looks like a query
                research_domain_from_input = original_agent_input.get("research_domain", "")
                if research_domain_from_input and "?" in research_domain_from_input:
                    user_query = research_domain_from_input
        
        # Build learning context
        learning_context = self._build_learning_context(agent_type)
        
        # Perform quality assessment
        assessment = await self._perform_quality_assessment(
            agent_output=agent_output,
            agent_type=agent_type,
            research_domain=research_domain,
            user_query=user_query,
            learning_context=learning_context,
            original_agent_input=original_agent_input
        )
        
        # Store assessment
        self._store_retry_history(agent_type, 1, assessment)
        
        # Determine final status
        if assessment.status == "APPROVE":
            final_status = "APPROVED"
            final_message = f"{agent_type} output approved"
        elif assessment.status == "HALT":
            final_status = "HALTED"
            final_message = f"Supervisor halted {agent_type}: {', '.join(assessment.issues_found)}"
        else:  # REVISE
            final_status = "NEEDS_RETRY"
            final_message = f"{agent_type} needs retry with enhanced context. Use the /retry-agent endpoint with the provided suggestions."
        
        return SupervisorResult(
            initial_assessment=assessment,
            final_status=final_status,
            final_message=final_message
        )
    
    async def _attempt_retry(self, agent_type: str, research_domain: str, user_query: str,
                           agent_input: Dict[str, Any], original_agent_input: Dict[str, Any],
                           initial_assessment: EnhancedQualityAssessment,
                           agent_config: RetryConfig) -> Dict[str, Any]:
        """
        Attempt to retry the agent with enhanced context.
        """
        if agent_type not in self.agents:
            return {
                "success": False,
                "error": f"Agent {agent_type} not available for retry",
                "retry_attempts": 0
            }
        
        agent_instance = self.agents[agent_type]
        current_attempt = 1
        max_attempts = agent_config.max_retry_attempts
        
        print(f"[ENHANCED SUPERVISOR] Attempting retry for {agent_type} (max {max_attempts} attempts)")
        
        while current_attempt <= max_attempts:
            try:
                print(f"[ENHANCED SUPERVISOR] {agent_type} retry attempt {current_attempt}/{max_attempts}")
                
                # Build enhanced context for retry
                enhanced_context = {
                    "supervisor_feedback": initial_assessment,
                    "previous_attempts": self._get_retry_history_for_agent(agent_type),
                    "attempt_number": current_attempt + 1,
                    "max_attempts": max_attempts,
                    "improvement_requirements": initial_assessment.improvement_suggestions,
                    "enhanced_context_prompt": initial_assessment.enhanced_context_prompt
                }
                
                # Call agent with enhanced context based on agent type
                if hasattr(agent_instance, 'run'):
                    # Prepare base parameters for all agents
                    base_params = {
                        "supervisor_feedback": initial_assessment,
                        "previous_attempts": enhanced_context,
                        "attempt_number": current_attempt + 1,
                        "max_attempts": max_attempts
                    }
                    
                    # Dynamically extract parameters based on agent type
                    retry_params = self._extract_agent_parameters(
                        agent_type=agent_type,
                        original_input=original_agent_input,
                        modified_input=agent_input,
                        user_query=user_query,
                        research_domain=research_domain
                    )
                    
                    # Add supervisor feedback parameters
                    retry_params.update(base_params)
                    
                    # Call the agent with extracted parameters
                    retry_output = await agent_instance.run(**retry_params)
                    
                    print(f"[DEBUG] Retry output type: {type(retry_output)}")
                    print(f"[DEBUG] Retry output keys: {list(retry_output.keys()) if isinstance(retry_output, dict) else 'Not a dict'}")
                    print(f"[DEBUG] Retry output data key exists: {'data' in retry_output if isinstance(retry_output, dict) else 'N/A'}")
                    
                    # Get the actual output for assessment
                    assessment_output = retry_output.get("data", retry_output)
                    print(f"[DEBUG] Assessment output type: {type(assessment_output)}")
                    print(f"[DEBUG] Assessment output keys: {list(assessment_output.keys()) if isinstance(assessment_output, dict) else 'Not a dict'}")
                    
                    # Evaluate retry output
                    final_assessment = await self._perform_quality_assessment(
                        agent_output=assessment_output,
                        agent_type=agent_type,
                        research_domain=research_domain,
                        user_query=user_query,
                        learning_context={}
                    )
                    
                    # Store retry assessment
                    self._store_retry_history(agent_type, current_attempt + 1, final_assessment)
                    
                    # Check if retry was successful
                    if final_assessment.status == "APPROVE":
                        print(f"[ENHANCED SUPERVISOR] {agent_type} retry successful on attempt {current_attempt}")
                        print(f"[DEBUG] Returning successful retry with output: {type(retry_output)}")
                        return {
                            "success": True,
                            "retry_output": retry_output,
                            "retry_attempts": current_attempt,
                            "final_assessment": final_assessment
                        }
                    
                    elif final_assessment.status == "HALT":
                        print(f"[ENHANCED SUPERVISOR] {agent_type} retry halted")
                        print(f"[DEBUG] Returning halted retry with output: {type(retry_output)}")
                        return {
                            "success": False,
                            "error": f"Supervisor halted retry: {', '.join(final_assessment.issues_found)}",
                            "retry_attempts": current_attempt,
                            "final_assessment": final_assessment,
                            "retry_output": retry_output  # Include retry output even on halt
                        }
                    
                    else:
                        # Continue retrying
                        print(f"[DEBUG] Retry status: {final_assessment.status}, continuing to attempt {current_attempt + 1}")
                        current_attempt += 1
                        initial_assessment = final_assessment
                        continue
                
                else:
                    return {
                        "success": False,
                        "error": f"Agent {agent_type} does not have a run method",
                        "retry_attempts": 0
                    }
                
            except Exception as e:
                print(f"[ERROR] {agent_type} retry attempt {current_attempt} failed: {e}")
                if current_attempt < max_attempts:
                    current_attempt += 1
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Retry failed after {max_attempts} attempts: {str(e)}",
                        "retry_attempts": current_attempt
                    }
        
        # Max attempts reached
        return {
            "success": False,
            "error": f"Max retry attempts ({max_attempts}) reached",
            "retry_attempts": max_attempts,
            "final_assessment": initial_assessment
        }
    
    async def _perform_quality_assessment(self, agent_output: Dict[str, Any], agent_type: str,
                                        research_domain: str, user_query: str,
                                        learning_context: Dict[str, Any],
                                        original_agent_input: Dict[str, Any] = None) -> EnhancedQualityAssessment:
        """
        Perform comprehensive quality assessment using the existing supervisor prompts.
        """
        # Use the existing assessment templates
        prompt = AssessmentTemplates.build_complete_assessment_prompt(
            agent_output=agent_output,
            agent_type=agent_type,
            user_query=user_query,
            research_domain=research_domain,
            pipeline_step="",
            previous_steps=[],
            learning_context=learning_context,
            original_agent_input=original_agent_input
        )
        
        print(f"[ENHANCED SUPERVISOR] Generating assessment for {agent_type}")
        response = await self.llm_backend.generate(prompt)
        
        # Parse the response using existing logic
        assessment = self._parse_enhanced_assessment_response(response, agent_type)
        
        return assessment
    
    def _parse_enhanced_assessment_response(self, response: str, agent_type: str) -> EnhancedQualityAssessment:
        """
        Parse the LLM response into enhanced quality assessment.
        """
        # Initialize default values
        assessment = EnhancedQualityAssessment(
            status="APPROVE",
            quality_score=0.8,
            confidence=0.8,
            issues_found=[],
            improvement_suggestions=[],
            enhanced_context_prompt="",
            assessment_reasoning=""
        )
        
        try:
            print(f"[DEBUG] Parsing assessment response: {response[:200]}...")
            
            # Extract status and scores from response
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse status - look for various formats
                if any(keyword in line.lower() for keyword in ["status:", "decision:", "assessment:"]):
                    if ":" in line:
                        status_part = line.split(':', 1)[1].strip().upper()
                        if "APPROVE" in status_part:
                            assessment.status = "APPROVE"
                        elif "REVISE" in status_part:
                            assessment.status = "REVISE"
                        elif "HALT" in status_part:
                            assessment.status = "HALT"
                
                # Parse quality score (0-10 scale)
                if "quality" in line.lower() and any(char.isdigit() for char in line):
                    try:
                        import re
                        numbers = re.findall(r'\d+\.?\d*', line)
                        if numbers:
                            score = float(numbers[0])
                            # Quality score is on 0-10 scale, keep as is
                            assessment.quality_score = score
                    except (ValueError, IndexError):
                        pass
                
                # Parse confidence (0-1 scale)
                if "confidence" in line.lower() and any(char.isdigit() for char in line):
                    try:
                        import re
                        numbers = re.findall(r'\d+\.?\d*', line)
                        if numbers:
                            confidence = float(numbers[0])
                            # If confidence is > 1, assume it's percentage (0-100) and convert to 0-1
                            if confidence > 1.0:
                                assessment.confidence = confidence / 100.0
                            else:
                                assessment.confidence = confidence
                    except (ValueError, IndexError):
                        pass
                
                # Parse issues and suggestions
                if any(keyword in line.lower() for keyword in ["issues:", "problems:", "concerns:", "issues found:"]):
                    current_section = "issues"
                elif any(keyword in line.lower() for keyword in ["suggestions:", "improvements:", "recommendations:"]):
                    current_section = "improvements"
                elif any(keyword in line.lower() for keyword in ["enhanced context prompt:", "context prompt:", "enhanced context:"]):
                    current_section = "context"
                    # Extract content from the same line if it exists
                    if ':' in line:
                        content = line.split(':', 1)[1].strip()
                        if content:
                            assessment.enhanced_context_prompt = content
                elif line.startswith('-') or line.startswith('*') or line.startswith('•'):
                    content = line[1:].strip()
                    if current_section == "issues" and content:
                        assessment.issues_found.append(content)
                    elif current_section == "improvements" and content:
                        assessment.improvement_suggestions.append(content)
                elif current_section == "context" and line and not line.startswith('**') and not line.startswith('Status:') and not line.startswith('Quality Score:'):
                    # Add to enhanced context prompt, but avoid adding other response fields
                    if not any(field in line for field in ['Status:', 'Quality Score:', 'Purpose Alignment Score:', 'Relevance Score:', 'Completeness Score:', 'Strategic Value Score:', 'Assessment Reasoning:', 'Confidence:', 'Gaps Identified:', 'Improvement Suggestions:', 'User Input Improvements:', 'Issues Found:', 'Strengths Identified:', 'Next Steps Recommendation:']):
                        assessment.enhanced_context_prompt += line + "\n"
            
            # No action field needed - status determines action
            
            # If no issues found but status is REVISE, add a default issue
            if assessment.status == "REVISE" and not assessment.issues_found:
                assessment.issues_found = ["Quality below acceptable threshold"]
                assessment.improvement_suggestions = ["Improve overall quality and completeness"]
            
            print(f"[DEBUG] Parsed assessment: status={assessment.status}, quality_score={assessment.quality_score}, issues={len(assessment.issues_found)}")
            print(f"[DEBUG] Enhanced context prompt length: {len(assessment.enhanced_context_prompt)}")
            print(f"[DEBUG] Enhanced context prompt: {assessment.enhanced_context_prompt[:100]}...")
            
        except Exception as e:
            print(f"[WARNING] Error parsing assessment response: {e}")
            # Fallback to default assessment
            assessment.status = "REVISE"
            assessment.issues_found = ["Unable to parse assessment response"]
            assessment.improvement_suggestions = ["Assessment parsing failed"]
        
        return assessment
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get statistics about retry behavior."""
        stats = {
            "total_agents_with_retries": 0,
            "total_retry_attempts": 0,
            "agent_retry_counts": {},
            "common_issues": {},
            "successful_improvements": {}
        }
        
        for agent_type, history in self.retry_history.items():
            if history:
                stats["total_agents_with_retries"] += 1
                stats["total_retry_attempts"] += len(history)
                stats["agent_retry_counts"][agent_type] = len(history)
                
                # Analyze common issues and improvements
                for record in history:
                    assessment = record.assessment
                    for issue in assessment.get('issues_found', []):
                        stats["common_issues"][issue] = stats["common_issues"].get(issue, 0) + 1
                    
                    if record.improvement_applied:
                        for improvement in assessment.get('improvement_suggestions', []):
                            stats["successful_improvements"][improvement] = stats["successful_improvements"].get(improvement, 0) + 1
        
        return stats
    
    def _extract_agent_parameters(self, agent_type: str, original_input: Dict[str, Any], 
                                 modified_input: Dict[str, Any], user_query: str, 
                                 research_domain: str) -> Dict[str, Any]:
        """
        Dynamically extract the correct parameters for each agent type.
        
        Args:
            agent_type: Type of agent to extract parameters for
            original_input: Original input sent to the agent
            modified_input: Modified input for retry (optional)
            user_query: User query
            research_domain: Research domain
            
        Returns:
            Dictionary of parameters for the agent
        """
        # Use modified input if provided, otherwise use original input
        input_data = modified_input if modified_input else original_input
        
        if not input_data:
            # Fallback with minimal parameters
            return {"research_domain": research_domain}
        
        # Extract parameters based on agent type
        if agent_type == "data_extractor":
            return {
                "query": input_data.get("query", user_query),
                "max_results": input_data.get("max_results", 20),
                "year_from": input_data.get("year_from", 2020),
                "year_to": input_data.get("year_to", 2024),
                "research_domain": research_domain
            }
        
        elif agent_type == "literature_review":
            return {
                "documents": input_data.get("documents", []),
                "research_domain": research_domain
            }
        
        elif agent_type == "initial_coding":
            return {
                "documents": input_data.get("documents", []),
                "research_domain": research_domain
            }
        
        elif agent_type == "thematic_grouping":
            return {
                "coded_units": input_data.get("coded_units", []),
                "research_domain": research_domain
            }
        
        elif agent_type == "theme_refinement":
            return {
                "themes": input_data.get("themes", []),
                "research_domain": research_domain
            }
        
        elif agent_type == "report_generator":
            return {
                "sections": input_data.get("sections", {}),
                "research_domain": research_domain
            }
        
        else:
            # For unknown agents, pass through all input data
            params = {"research_domain": research_domain}
            params.update(input_data)
            return params 