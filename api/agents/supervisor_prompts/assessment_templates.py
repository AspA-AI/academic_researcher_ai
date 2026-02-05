"""
Assessment Templates

Complete assessment templates that combine base prompts with agent-specific
criteria to create comprehensive supervisor assessment prompts.
"""

from typing import Dict, Any, List, Optional
from .base_prompts import BaseSupervisorPrompts
from .agent_specific_prompts import AgentSpecificPrompts

class AssessmentTemplates:
    """
    Complete assessment templates for supervisor evaluations.
    """
    
    @staticmethod
    def build_complete_assessment_prompt(
        agent_output: Dict[str, Any],
        agent_type: str,
        user_query: str,
        research_domain: str = "General",
        pipeline_step: str = "",
        previous_steps: List[str] = None,
        learning_context: Dict[str, Any] = None,
        original_agent_input: Dict[str, Any] = None
    ) -> str:
        """
        Build a complete assessment prompt combining all templates.
        """
        # Get base components
        role_definition = BaseSupervisorPrompts.get_supervisor_role_definition()
        response_format = BaseSupervisorPrompts.get_response_format_template()
        
        # Get agent-specific criteria
        agent_criteria = AgentSpecificPrompts.format_agent_prompt_for_assessment(agent_type)
        
        # Build context information
        context_info = AssessmentTemplates._build_context_information(
            user_query, research_domain, agent_type, pipeline_step, previous_steps, original_agent_input
        )
        
        # Format agent output for assessment
        output_summary = AssessmentTemplates._format_agent_output(agent_output, agent_type)
        
        # Add learning context if available
        learning_section = ""
        if learning_context:
            learning_section = AssessmentTemplates._build_learning_context(learning_context)
        
        # Combine all sections
        complete_prompt = f"""{role_definition}

{agent_criteria}

{context_info}

**Agent Output to Evaluate:**
{output_summary}

{learning_section}

{response_format}

**Your Assessment:**"""
        
        return complete_prompt
    
    @staticmethod
    def build_emergency_assessment_prompt(
        error_message: str,
        error_type: str,
        agent_type: str,
        user_query: str,
        research_domain: str = "General"
    ) -> str:
        """
        Build emergency assessment prompt for error scenarios.
        """
        emergency_template = BaseSupervisorPrompts.get_emergency_assessment_template()
        
        return emergency_template.format(
            error_message=error_message,
            error_type=error_type,
            agent_type=agent_type,
            user_query=user_query
        )
    
    @staticmethod
    def build_learning_assessment_prompt(
        agent_output: Dict[str, Any],
        agent_type: str,
        user_query: str,
        research_domain: str,
        previous_assessments: List[Dict[str, Any]],
        user_feedback: Dict[str, Any] = None
    ) -> str:
        """
        Build assessment prompt with learning context from previous assessments.
        """
        # Get base components
        role_definition = BaseSupervisorPrompts.get_supervisor_role_definition()
        response_format = BaseSupervisorPrompts.get_response_format_template()
        agent_criteria = AgentSpecificPrompts.format_agent_prompt_for_assessment(agent_type)
        
        # Build learning context
        learning_context = AssessmentTemplates._build_advanced_learning_context(
            previous_assessments, user_feedback
        )
        
        # Build context and output sections
        context_info = AssessmentTemplates._build_context_information(
            user_query, research_domain, agent_type, "", []
        )
        output_summary = AssessmentTemplates._format_agent_output(agent_output, agent_type)
        
        # Combine all sections
        complete_prompt = f"""{role_definition}

{agent_criteria}

{context_info}

**Agent Output to Evaluate:**
{output_summary}

{learning_context}

{response_format}

**Your Assessment:**"""
        
        return complete_prompt
    
    @staticmethod
    def _build_context_information(
        user_query: str,
        research_domain: str,
        agent_type: str,
        pipeline_step: str,
        previous_steps: List[str],
        original_agent_input: Dict[str, Any] = None
    ) -> str:
        """
        Build context information section.
        """
        agent_prompts = AgentSpecificPrompts.get_all_agent_prompts()
        agent_name = agent_prompts.get(agent_type, {}).get("agent_name", agent_type)
        
        previous_steps_str = ", ".join(previous_steps) if previous_steps else "None"
        
        # Build original input information
        original_input_info = ""
        if original_agent_input:
            original_input_info = f"""
**Original Agent Input Parameters:**
{chr(10).join([f"- {key}: {value}" for key, value in original_agent_input.items()])}"""
        
        return f"""**Current Context Information:**

User Query: "{user_query}"
Research Domain: {research_domain}
Agent Type: {agent_type}
Agent Name: {agent_name}
Pipeline Step: {pipeline_step}
Previous Steps Completed: {previous_steps_str}{original_input_info}"""
    
    @staticmethod
    def _format_agent_output(agent_output: Dict[str, Any], agent_type: str) -> str:
        """
        Format agent output for assessment.
        """
        if "error" in agent_output:
            return f"ERROR: {agent_output['error']}"
        
        # Agent-specific output formatting
        if agent_type == "data_extractor":
            return AssessmentTemplates._format_data_extractor_output(agent_output)
        elif agent_type == "literature_review":
            return AssessmentTemplates._format_literature_review_output(agent_output)
        elif agent_type == "initial_coding":
            return AssessmentTemplates._format_initial_coding_output(agent_output)
        elif agent_type == "thematic_grouping":
            return AssessmentTemplates._format_thematic_grouping_output(agent_output)
        elif agent_type == "theme_refiner":
            return AssessmentTemplates._format_theme_refiner_output(agent_output)
        elif agent_type == "report_generator":
            return AssessmentTemplates._format_report_generator_output(agent_output)
        else:
            return f"Agent output: {str(agent_output)[:500]}..."
    
    @staticmethod
    def _format_data_extractor_output(agent_output: Dict[str, Any]) -> str:
        """
        Format data extractor output for assessment.
        """
        # Handle both direct output and wrapped output structures
        data = agent_output.get("data", agent_output)
        documents = data.get("documents", [])
        return f"""
Documents Retrieved: {len(documents)}
Document Titles: {[doc.get('title', 'No title') for doc in documents[:5]]}
Relevance Scores: {[doc.get('relevance_score', 'N/A') for doc in documents[:5]]}
Sources: {[doc.get('source', 'Unknown') for doc in documents[:5]]}
Abstracts: {[doc.get('abstract', 'No abstract')[:100] + '...' for doc in documents[:3]]}
Search Query: {data.get("search_query", "Not specified")}
Sources Used: {data.get("sources_used", [])}
"""
    
    @staticmethod
    def _format_literature_review_output(agent_output: Dict[str, Any]) -> str:
        """
        Format literature review output for assessment.
        """
        # Handle both direct output and wrapped output structures
        data = agent_output.get("data", agent_output)
        
        summary = data.get('summary', 'No summary')
        key_findings = data.get('key_findings', [])
        research_gaps = data.get('research_gaps', [])
        full_review = data.get('full_literature_review', '')
        citations = data.get('citations', [])
        
        return f"""
Summary: {summary[:200]}...
Key Findings: {len(key_findings)} findings identified
Research Gaps: {len(research_gaps)} gaps identified
Literature Review Length: {len(full_review)} characters
Citations: {len(citations)} citations included
Documents Analyzed: {data.get('documents_analyzed', 0)}
Research Domain: {data.get('research_domain', 'Not specified')}
"""
    
    @staticmethod
    def _format_initial_coding_output(agent_output: Dict[str, Any]) -> str:
        """
        Format initial coding output for assessment.
        """
        # Handle both direct output and wrapped output structures
        data = agent_output.get("data", agent_output)
        coding_summary = data.get("coding_summary", {})
        return f"""
Total Units Coded: {coding_summary.get('total_units_coded', 0)}
Unique Codes Generated: {coding_summary.get('unique_codes_generated', 0)}
Average Confidence: {coding_summary.get('average_confidence', 0):.2f}
Primary Codes: {coding_summary.get('primary_codes', [])}
Sub Codes: {coding_summary.get('sub_codes', [])}
Coded Units: {len(data.get('coded_units', []))} units
"""
    
    @staticmethod
    def _format_thematic_grouping_output(agent_output: Dict[str, Any]) -> str:
        """
        Format thematic grouping output for assessment.
        """
        # Handle both direct output and wrapped output structures
        data = agent_output.get("data", agent_output)
        thematic_summary = data.get("thematic_summary", {})
        return f"""
Total Themes Generated: {thematic_summary.get('total_themes_generated', 0)}
Total Codes Analyzed: {thematic_summary.get('total_codes_analyzed', 0)}
Unique Codes Clustered: {thematic_summary.get('unique_codes_clustered', 0)}
Average Codes per Theme: {thematic_summary.get('average_codes_per_theme', 0):.1f}
Themes: {[theme.get('theme_name', 'Unknown') for theme in data.get('themes', [])]}
Cross-cutting Ideas: {len(thematic_summary.get('cross_cutting_ideas', []))} identified
"""
    
    @staticmethod
    def _format_theme_refiner_output(agent_output: Dict[str, Any]) -> str:
        """
        Format theme refiner output for assessment.
        """
        # Handle both direct output and wrapped output structures
        data = agent_output.get("data", agent_output)
        refinement_summary = data.get("refinement_summary", {})
        return f"""
Total Themes Refined: {refinement_summary.get('total_themes_refined', 0)}
Total Academic Quotes: {refinement_summary.get('total_academic_quotes', 0)}
Average Quotes per Theme: {refinement_summary.get('average_quotes_per_theme', 0):.1f}
Themes with Framework: {refinement_summary.get('themes_with_framework', 0)}
Themes with Implications: {refinement_summary.get('themes_with_implications', 0)}
Refined Themes: {[theme.get('refined_name', 'Unknown') for theme in data.get('refined_themes', [])]}
"""
    
    @staticmethod
    def _format_report_generator_output(agent_output: Dict[str, Any]) -> str:
        """
        Format report generator output for assessment.
        """
        # Handle both direct output and wrapped output structures
        data = agent_output.get("data", agent_output)
        report_summary = data.get("report_summary", {})
        return f"""
Word Count: {report_summary.get('word_count', 0)}
Sections Included: {list(report_summary.get('sections_included', {}).keys())}
Total References: {report_summary.get('total_references', 0)}
Report Length: {report_summary.get('report_length', 'Unknown')}
Generated At: {report_summary.get('generated_at', 'Unknown')}
Report File: {data.get('report_file', 'Not specified')}
"""
    
    @staticmethod
    def _build_learning_context(learning_context: Dict[str, Any]) -> str:
        """
        Build basic learning context section.
        """
        return f"""**Learning Context:**

Previous Quality Scores: {learning_context.get('previous_scores', [])}
Common Issues: {learning_context.get('common_issues', [])}
Successful Patterns: {learning_context.get('successful_patterns', [])}"""
    
    @staticmethod
    def _build_advanced_learning_context(
        previous_assessments: List[Dict[str, Any]],
        user_feedback: Dict[str, Any] = None
    ) -> str:
        """
        Build advanced learning context from previous assessments.
        """
        if not previous_assessments and not user_feedback:
            return ""
        
        context_parts = []
        
        if previous_assessments:
            avg_quality = sum(a.get('quality_score', 0) for a in previous_assessments) / len(previous_assessments)
            common_issues = []
            successful_patterns = []
            
            for assessment in previous_assessments:
                if assessment.get('status') == 'REVISE':
                    common_issues.extend(assessment.get('issues_found', []))
                elif assessment.get('status') == 'APPROVE':
                    successful_patterns.extend(assessment.get('strengths_identified', []))
            
            context_parts.append(f"""**Learning from Previous Assessments:**
Average Quality Score: {avg_quality:.2f}
Common Issues Identified: {list(set(common_issues))[:5]}
Successful Patterns: {list(set(successful_patterns))[:5]}""")
        
        if user_feedback:
            context_parts.append(f"""**User Feedback Integration:**
User Preferences: {user_feedback.get('preferences', [])}
User Corrections: {user_feedback.get('corrections', [])}
User Satisfaction: {user_feedback.get('satisfaction', 'Unknown')}""")
        
        return "\n\n".join(context_parts) 