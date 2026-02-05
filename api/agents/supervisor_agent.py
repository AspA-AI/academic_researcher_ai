import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
import sys
import os
# Add the api directory to the path
from api.utils.llm_backends import get_llm_backend
from api.agents.supervisor_prompts.assessment_templates import AssessmentTemplates

@dataclass
class QualityAssessment:
    """Represents a quality assessment result"""
    status: str  # APPROVE, REVISE, HALT
    feedback: List[str]
    action: str
    confidence: float
    issues_found: List[str]
    quality_score: float
    
    # Enhanced assessment fields
    purpose_alignment_score: float = 0.0
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    strategic_value_score: float = 0.0
    
    # Detailed feedback
    gaps_identified: List[str] = None
    improvement_suggestions: List[str] = None
    enhanced_context_prompt: str = ""
    user_input_improvements: List[str] = None
    assessment_reasoning: str = ""
    strengths_identified: List[str] = None
    next_steps_recommendation: str = ""
    
    def __post_init__(self):
        """Initialize default values for lists"""
        if self.gaps_identified is None:
            self.gaps_identified = []
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []
        if self.user_input_improvements is None:
            self.user_input_improvements = []
        if self.strengths_identified is None:
            self.strengths_identified = []

class SupervisorAgent:
    """
    Quality Control Supervisor Agent that reviews each agent's output and decides whether to proceed.
    """
    def __init__(self, llm_backend=None):
        # Initialize with OpenAI backend by default
        self.llm_backend = llm_backend or get_llm_backend("openai")

    def _get_quality_criteria(self, agent_type: str) -> Dict[str, Any]:
        """
        Get quality criteria for a specific agent type.
        """
        criteria = {
            "literature_review": {
                "summary_length_min": 200,
                "key_findings_min": 3,
                "research_gaps_min": 2,
                "required_elements": ["summary", "key_findings", "research_gaps", "full_literature_review"],
                "tone_check": "academic but accessible",
                "citation_format": "Harvard-style"
            },
            "initial_coding": {
                "unique_codes_min": 5,
                "average_confidence_min": 0.7,
                "required_elements": ["coding_summary", "coded_units"],
                "code_relevance": "aligned with research domain",
                "code_definitions": "clear and specific"
            },
            "thematic_grouping": {
                "theme_count_min": 2,
                "theme_count_max": 5,
                "required_elements": ["thematic_summary", "themes"],
                "code_distribution": "relatively even across themes",
                "theme_distinctness": "no redundant themes",
                "cross_cutting_ideas": "identified"
            },
            "theme_refinement": {
                "academic_quotes_min_per_theme": 2,
                "required_elements": ["refinement_summary", "refined_themes"],
                "definitions": "precise and clear",
                "scope_boundaries": "well-defined",
                "theoretical_frameworks": "identified"
            },
            "report_generation": {
                "word_count_min": 800,
                "required_sections": ["Abstract", "Introduction", "Literature Review", "Methodology", "Findings", "Discussion", "Conclusion"],
                "citation_format": "Harvard-style throughout",
                "logical_flow": "coherent narrative"
            }
        }
        
        return criteria.get(agent_type, {})

    def _build_supervisor_prompt(self, agent_output: Dict[str, Any], agent_type: str, research_domain: str, user_query: str = "") -> str:
        """
        Build the supervisor prompt using the new template system.
        """
        # Use the new assessment templates
        return AssessmentTemplates.build_complete_assessment_prompt(
            agent_output=agent_output,
            agent_type=agent_type,
            user_query=user_query,
            research_domain=research_domain,
            pipeline_step="",
            previous_steps=[],
            learning_context=None
        )

    def _format_output_for_review(self, agent_output: Dict[str, Any], agent_type: str) -> str:
        """
        Format agent output for supervisor review.
        """
        if "error" in agent_output:
            return f"ERROR: {agent_output['error']}"
        
        # Extract key metrics based on agent type
        if agent_type == "literature_review":
            summary = agent_output.get("summary", "")
            key_findings = agent_output.get("key_findings", [])
            research_gaps = agent_output.get("research_gaps", [])
            full_review = agent_output.get("full_literature_review", "")
            
            return f"""
Summary Length: {len(summary)} characters
Key Findings Count: {len(key_findings)}
Research Gaps Count: {len(research_gaps)}
Full Review Length: {len(full_review)} characters
Summary Preview: {summary[:200]}...
Key Findings: {key_findings}
Research Gaps: {research_gaps}
"""
        
        elif agent_type == "initial_coding":
            coding_summary = agent_output.get("coding_summary", {})
            coded_units = agent_output.get("coded_units", [])
            
            return f"""
Total Units Coded: {coding_summary.get('total_units_coded', 0)}
Unique Codes: {coding_summary.get('unique_codes_generated', 0)}
Average Confidence: {coding_summary.get('average_confidence', 0):.2f}
Primary Codes: {coding_summary.get('primary_codes', [])}
Sub Codes: {coding_summary.get('sub_codes', [])}
Coded Units Count: {len(coded_units)}
"""
        
        elif agent_type == "thematic_grouping":
            thematic_summary = agent_output.get("thematic_summary", {})
            themes = agent_output.get("themes", [])
            
            return f"""
Total Themes: {thematic_summary.get('total_themes_generated', 0)}
Codes Analyzed: {thematic_summary.get('total_codes_analyzed', 0)}
Cross-cutting Ideas: {thematic_summary.get('cross_cutting_ideas', [])}
Theme Names: {[theme.get('theme_name', '') for theme in themes]}
"""
        
        elif agent_type == "theme_refinement":
            refinement_summary = agent_output.get("refinement_summary", {})
            refined_themes = agent_output.get("refined_themes", [])
            
            return f"""
Total Themes Refined: {refinement_summary.get('total_themes_refined', 0)}
Academic Quotes: {refinement_summary.get('total_academic_quotes', 0)}
Key Concepts: {refinement_summary.get('total_key_concepts', 0)}
Refined Theme Names: {[theme.get('refined_name', '') for theme in refined_themes]}
"""
        
        elif agent_type == "report_generation":
            report_summary = agent_output.get("report_summary", {})
            report_content = agent_output.get("report_content", "")
            
            return f"""
Word Count: {report_summary.get('word_count', 0)}
Sections Included: {report_summary.get('sections_included', {})}
Total References: {report_summary.get('total_references', 0)}
Report Length: {len(report_content)} characters
"""
        
        else:
            return f"Agent output: {str(agent_output)[:500]}..."

    def _format_criteria_for_prompt(self, criteria: Dict[str, Any]) -> str:
        """
        Format quality criteria for the prompt.
        """
        criteria_text = []
        for key, value in criteria.items():
            if isinstance(value, list):
                criteria_text.append(f"- {key}: {', '.join(value)}")
            else:
                criteria_text.append(f"- {key}: {value}")
        
        return "\n".join(criteria_text)

    def _parse_supervisor_response(self, response: str) -> QualityAssessment:
        """
        Parse the enhanced supervisor response to extract all assessment details.
        """
        # Default values
        status = "HALT"
        feedback = []
        action = "Stop pipeline due to parsing error"
        confidence = 0.0
        quality_score = 0.0
        issues_found = []
        
        # Enhanced assessment fields
        purpose_alignment_score = 0.0
        relevance_score = 0.0
        completeness_score = 0.0
        strategic_value_score = 0.0
        
        # Detailed feedback
        gaps_identified = []
        improvement_suggestions = []
        enhanced_context_prompt = ""
        user_input_improvements = []
        assessment_reasoning = ""
        strengths_identified = []
        next_steps_recommendation = ""
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse status
            if line.startswith('Status:'):
                status_part = line.split(':', 1)[1].strip()
                if status_part in ['APPROVE', 'REVISE', 'HALT']:
                    status = status_part
            
            # Parse scores
            elif line.startswith('Quality Score:'):
                try:
                    score = line.split(':', 1)[1].strip()
                    quality_score = float(score)
                except:
                    quality_score = 0.0
            
            elif line.startswith('Purpose Alignment Score:'):
                try:
                    score = line.split(':', 1)[1].strip()
                    purpose_alignment_score = float(score)
                except:
                    purpose_alignment_score = 0.0
            
            elif line.startswith('Relevance Score:'):
                try:
                    score = line.split(':', 1)[1].strip()
                    relevance_score = float(score)
                except:
                    relevance_score = 0.0
            
            elif line.startswith('Completeness Score:'):
                try:
                    score = line.split(':', 1)[1].strip()
                    completeness_score = float(score)
                except:
                    completeness_score = 0.0
            
            elif line.startswith('Strategic Value Score:'):
                try:
                    score = line.split(':', 1)[1].strip()
                    strategic_value_score = float(score)
                except:
                    strategic_value_score = 0.0
            
            elif line.startswith('Confidence:'):
                try:
                    conf = line.split(':', 1)[1].strip()
                    confidence = float(conf)
                except:
                    confidence = 0.0
            
            # Parse sections
            elif line == 'Gaps Identified:':
                current_section = 'gaps'
            elif line == 'Improvement Suggestions:':
                current_section = 'improvements'
            elif line == 'Enhanced Context Prompt:':
                current_section = 'context'
            elif line == 'User Input Improvements:':
                current_section = 'user_input'
            elif line == 'Assessment Reasoning:':
                current_section = 'reasoning'
            elif line == 'Issues Found:':
                current_section = 'issues'
            elif line == 'Strengths Identified:':
                current_section = 'strengths'
            elif line == 'Next Steps Recommendation:':
                current_section = 'next_steps'
            
            # Parse content based on current section
            elif line.startswith('- ') and current_section:
                content = line[2:].strip()
                if current_section == 'gaps':
                    gaps_identified.append(content)
                elif current_section == 'improvements':
                    improvement_suggestions.append(content)
                elif current_section == 'user_input':
                    user_input_improvements.append(content)
                elif current_section == 'issues':
                    issues_found.append(content)
                elif current_section == 'strengths':
                    strengths_identified.append(content)
            
            elif current_section == 'context' and line:
                enhanced_context_prompt += line + "\n"
            
            elif current_section == 'reasoning' and line:
                assessment_reasoning += line + "\n"
            
            elif current_section == 'next_steps' and line:
                next_steps_recommendation += line + "\n"
        
        # Set action based on status
        if status == "APPROVE":
            action = "Proceed to next step"
        elif status == "REVISE":
            action = "Retry with improvements"
        else:
            action = "Stop pipeline due to critical issues"
        
        # Set feedback based on issues found
        feedback = issues_found.copy()
        
        return QualityAssessment(
            status=status,
            feedback=feedback,
            action=action,
            confidence=confidence,
            issues_found=issues_found,
            quality_score=quality_score,
            purpose_alignment_score=purpose_alignment_score,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            strategic_value_score=strategic_value_score,
            gaps_identified=gaps_identified,
            improvement_suggestions=improvement_suggestions,
            enhanced_context_prompt=enhanced_context_prompt.strip(),
            user_input_improvements=user_input_improvements,
            assessment_reasoning=assessment_reasoning.strip(),
            strengths_identified=strengths_identified,
            next_steps_recommendation=next_steps_recommendation.strip()
        )

    async def check_quality(self, agent_output: Dict[str, Any], agent_type: str, research_domain: str = "General", user_query: str = "") -> QualityAssessment:
        """
        Check the quality of an agent's output.
        Args:
            agent_output: The output from the agent to check
            agent_type: Type of agent (literature_review, initial_coding, etc.)
            research_domain: The research domain being studied
            user_query: The original user query for context
        Returns:
            QualityAssessment: The quality assessment result
        """
        print(f"[DEBUG] SupervisorAgent.check_quality called for {agent_type}")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        try:
            # Check for errors first
            if "error" in agent_output:
                print(f"[DEBUG] Agent output contains error: {agent_output['error']}")
                return QualityAssessment(
                    status="HALT",
                    feedback=[f"Agent failed with error: {agent_output['error']}"],
                    action="Stop pipeline due to agent error",
                    confidence=1.0,
                    issues_found=[f"Agent error: {agent_output['error']}"],
                    quality_score=0.0
                )
            
            # Build supervisor prompt
            prompt = self._build_supervisor_prompt(agent_output, agent_type, research_domain, user_query)
            print(f"[DEBUG] Generated supervisor prompt length: {len(prompt)} characters")
            
            if not self.llm_backend:
                return QualityAssessment(
                    status="HALT",
                    feedback=["No LLM backend provided for supervisor"],
                    action="Stop pipeline due to missing LLM backend",
                    confidence=1.0,
                    issues_found=["Missing LLM backend"],
                    quality_score=0.0
                )
            
            print(f"[DEBUG] Using LLM backend: {self.llm_backend.get_model_info()}")
            
            # Get supervisor assessment
            llm_response = await self.llm_backend.generate(prompt)
            print(f"[DEBUG] Supervisor LLM response received, length: {len(llm_response)} characters")
            
            if not llm_response:
                return QualityAssessment(
                    status="HALT",
                    feedback=["Supervisor LLM generation failed"],
                    action="Stop pipeline due to supervisor failure",
                    confidence=1.0,
                    issues_found=["Supervisor LLM failure"],
                    quality_score=0.0
                )
            
            # Parse supervisor response
            assessment = self._parse_supervisor_response(llm_response)
            
            print(f"[DEBUG] Supervisor assessment: {assessment.status} (confidence: {assessment.confidence:.2f})")
            if assessment.feedback:
                print(f"[DEBUG] Feedback: {assessment.feedback}")
            
            return assessment
            
        except Exception as e:
            print(f"[ERROR] Supervisor quality check failed: {e}")
            return QualityAssessment(
                status="HALT",
                feedback=[f"Supervisor check failed: {str(e)}"],
                action="Stop pipeline due to supervisor error",
                confidence=1.0,
                issues_found=[f"Supervisor error: {str(e)}"],
                quality_score=0.0
            )

    async def run(self, pipeline_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for supervisor agent.
        Args:
            pipeline_state: Current state of the pipeline with all agent outputs
        Returns:
            Dict: Overall pipeline assessment and recommendations
        """
        print(f"[DEBUG] SupervisorAgent.run called with pipeline state")
        
        # This method can be used for overall pipeline assessment
        # For now, we'll use check_quality for individual agent checks
        
        return {
            "status": "supervisor_ready",
            "message": "Supervisor agent ready for quality checks",
            "timestamp": datetime.now(timezone.utc).isoformat()
        } 