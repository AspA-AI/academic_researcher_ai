"""
Agent-Specific Supervisor Prompt Templates

Prompt templates tailored for each agent type in the research pipeline,
defining their specific assessment criteria and success metrics.
"""

from typing import Dict, Any, List

class AgentSpecificPrompts:
    """
    Agent-specific prompt templates for supervisor assessments.
    """
    
    @staticmethod
    def get_data_extractor_prompt() -> Dict[str, Any]:
        """
        Assessment criteria and prompts for the Data Extractor agent.
        """
        return {
            "agent_name": "Data Extractor",
            "agent_purpose": "Extract and retrieve relevant academic documents from external sources based on user query",
            "expected_outputs": [
                "List of relevant academic papers (5-20 documents)",
                "Document metadata (title, authors, year, abstract)",
                "Relevance scores for each document (0.0-1.0)",
                "Source information (database, URL, etc.)",
                "Search query used and sources accessed"
            ],
            "success_criteria": [
                "Documents are highly relevant to user query (relevance score >= 0.7)",
                "Sufficient number of documents retrieved (5-20 documents)",
                "Documents are from reputable academic sources (PubMed, IEEE, etc.)",
                "Documents cover different aspects of the query",
                "Recent and authoritative sources included (within last 5 years preferred)",
                "Diverse source types (journals, conferences, etc.)"
            ],
            "common_issues": [
                "Documents not relevant to query (low relevance scores)",
                "Too few or too many documents retrieved",
                "Low-quality or non-academic sources",
                "Missing recent research (all documents too old)",
                "Narrow scope (missing important aspects of query)",
                "Duplicate or redundant documents",
                "Missing metadata (authors, year, abstract)"
            ],
            "assessment_focus": [
                "Relevance of retrieved documents to user query",
                "Quantity and quality of documents",
                "Source credibility and diversity",
                "Coverage of different query aspects",
                "Recency and authority of sources"
            ],
            "improvement_strategies": [
                "Refine search keywords to improve relevance",
                "Add domain-specific terminology to query",
                "Include broader/specific aspects of the topic",
                "Specify date range requirements",
                "Add source quality filters",
                "Expand search to additional databases"
            ]
        }
    
    @staticmethod
    def get_literature_review_prompt() -> Dict[str, Any]:
        """
        Assessment criteria and prompts for the Literature Review agent.
        """
        return {
            "agent_name": "Literature Review",
            "agent_purpose": "Analyze retrieved documents and generate comprehensive literature review",
            "expected_outputs": [
                "Summary of key findings and trends",
                "Research gaps identification",
                "Theoretical frameworks and methodologies",
                "Full literature review text (800+ words)",
                "Citation of all source documents",
                "Critical analysis and synthesis"
            ],
            "success_criteria": [
                "Comprehensive coverage of retrieved documents",
                "Clear identification of research gaps",
                "Logical organization and flow",
                "Academic writing style and tone",
                "Proper citation of all sources",
                "Critical analysis rather than just summary",
                "Identification of trends and patterns"
            ],
            "common_issues": [
                "Incomplete coverage of documents",
                "Missing research gaps identification",
                "Poor organization and structure",
                "Non-academic writing style",
                "Missing or incorrect citations",
                "Lack of critical analysis",
                "Too brief or superficial review"
            ],
            "assessment_focus": [
                "Completeness of document coverage",
                "Quality of research gap identification",
                "Academic writing standards",
                "Critical analysis depth",
                "Citation accuracy and completeness"
            ],
            "improvement_strategies": [
                "Ensure all documents are analyzed and cited",
                "Focus on identifying clear research gaps",
                "Improve structure with clear sections",
                "Enhance academic writing style",
                "Add proper citations and references",
                "Include more critical analysis"
            ]
        }
    
    @staticmethod
    def get_initial_coding_prompt() -> Dict[str, Any]:
        """
        Assessment criteria and prompts for the Initial Coding agent.
        """
        return {
            "agent_name": "Initial Coding",
            "agent_purpose": "Perform open coding analysis on documents to identify themes and patterns",
            "expected_outputs": [
                "Coded units with identified themes",
                "Code definitions and descriptions",
                "Confidence scores for each code",
                "Coding summary statistics",
                "Code categories (primary, secondary, etc.)"
            ],
            "success_criteria": [
                "Comprehensive coverage of document content",
                "Clear and specific code definitions",
                "High confidence scores (>= 0.7 average)",
                "Logical code organization and categorization",
                "Sufficient number of unique codes (5-15)",
                "Codes are relevant to research domain"
            ],
            "common_issues": [
                "Incomplete coding coverage",
                "Vague or unclear code definitions",
                "Low confidence scores",
                "Poor code organization",
                "Too few or too many codes",
                "Irrelevant or off-topic codes"
            ],
            "assessment_focus": [
                "Completeness of coding coverage",
                "Clarity and specificity of codes",
                "Confidence scores and reliability",
                "Code organization and relevance",
                "Alignment with research domain"
            ],
            "improvement_strategies": [
                "Ensure thorough document analysis",
                "Provide specific code definitions",
                "Focus on high-confidence codes",
                "Improve code categorization",
                "Align codes with research objectives"
            ]
        }
    
    @staticmethod
    def get_thematic_grouping_prompt() -> Dict[str, Any]:
        """
        Assessment criteria and prompts for the Thematic Grouping agent.
        """
        return {
            "agent_name": "Thematic Grouping",
            "agent_purpose": "Group coded units into coherent themes and identify patterns",
            "expected_outputs": [
                "Thematic summary with key insights",
                "Grouped themes with associated codes",
                "Cross-cutting ideas and connections",
                "Theme descriptions and justifications",
                "Theme size and distribution statistics"
            ],
            "success_criteria": [
                "Logical theme grouping and organization",
                "Clear theme descriptions and boundaries",
                "Identified cross-cutting ideas",
                "Comprehensive coverage of all codes",
                "Themes are distinct and non-overlapping",
                "Themes advance research understanding"
            ],
            "common_issues": [
                "Poor theme organization",
                "Vague theme descriptions",
                "Missing cross-cutting ideas",
                "Incomplete code coverage",
                "Overlapping or redundant themes",
                "Themes don't advance research"
            ],
            "assessment_focus": [
                "Theme organization and logic",
                "Clarity of theme descriptions",
                "Cross-cutting idea identification",
                "Code coverage completeness",
                "Research advancement value"
            ],
            "improvement_strategies": [
                "Improve theme organization",
                "Enhance theme descriptions",
                "Focus on cross-cutting ideas",
                "Ensure complete code coverage",
                "Create distinct, valuable themes"
            ]
        }
    
    @staticmethod
    def get_theme_refiner_prompt() -> Dict[str, Any]:
        """
        Assessment criteria and prompts for the Theme Refiner agent.
        """
        return {
            "agent_name": "Theme Refiner",
            "agent_purpose": "Polish and refine themes with academic rigor and theoretical frameworks",
            "expected_outputs": [
                "Refined theme definitions with precision",
                "Academic quotes and citations",
                "Theoretical frameworks and concepts",
                "Research implications and significance",
                "Scope boundaries and limitations"
            ],
            "success_criteria": [
                "Clear and precise theme definitions",
                "Relevant academic quotes and citations",
                "Appropriate theoretical frameworks",
                "Clear research implications",
                "Well-defined scope boundaries",
                "Academic rigor and depth"
            ],
            "common_issues": [
                "Vague or imprecise definitions",
                "Irrelevant or missing quotes",
                "Missing theoretical frameworks",
                "Unclear research implications",
                "Poorly defined scope",
                "Lack of academic depth"
            ],
            "assessment_focus": [
                "Precision of theme definitions",
                "Relevance of academic quotes",
                "Theoretical framework integration",
                "Research implication clarity",
                "Academic rigor and depth"
            ],
            "improvement_strategies": [
                "Provide precise definitions",
                "Include relevant academic quotes",
                "Add theoretical frameworks",
                "Clarify research implications",
                "Enhance academic rigor"
            ]
        }
    
    @staticmethod
    def get_report_generator_prompt() -> Dict[str, Any]:
        """
        Assessment criteria and prompts for the Report Generator agent.
        """
        return {
            "agent_name": "Report Generator",
            "agent_purpose": "Generate comprehensive academic report integrating all previous outputs",
            "expected_outputs": [
                "Complete academic report (1500+ words)",
                "All required sections (Abstract, Introduction, etc.)",
                "Proper citations throughout",
                "Executive summary",
                "Research methodology and findings",
                "Conclusions and recommendations"
            ],
            "success_criteria": [
                "Comprehensive coverage of all pipeline outputs",
                "Proper academic structure and format",
                "Clear and coherent narrative flow",
                "Complete and accurate citations",
                "Professional academic writing style",
                "Logical conclusions and recommendations"
            ],
            "common_issues": [
                "Incomplete coverage of outputs",
                "Poor structure and organization",
                "Incoherent narrative flow",
                "Missing or incorrect citations",
                "Non-academic writing style",
                "Weak conclusions"
            ],
            "assessment_focus": [
                "Completeness of output integration",
                "Academic structure and format",
                "Narrative coherence and flow",
                "Citation accuracy and completeness",
                "Writing quality and style"
            ],
            "improvement_strategies": [
                "Ensure complete output coverage",
                "Improve structure and organization",
                "Enhance narrative flow",
                "Add missing citations",
                "Improve academic writing style"
            ]
        }
    
    @staticmethod
    def get_all_agent_prompts() -> Dict[str, Dict[str, Any]]:
        """
        Get all agent-specific prompts in a dictionary.
        """
        return {
            "data_extractor": AgentSpecificPrompts.get_data_extractor_prompt(),
            "literature_review": AgentSpecificPrompts.get_literature_review_prompt(),
            "initial_coding": AgentSpecificPrompts.get_initial_coding_prompt(),
            "thematic_grouping": AgentSpecificPrompts.get_thematic_grouping_prompt(),
            "theme_refiner": AgentSpecificPrompts.get_theme_refiner_prompt(),
            "report_generator": AgentSpecificPrompts.get_report_generator_prompt()
        }
    
    @staticmethod
    def format_agent_prompt_for_assessment(agent_type: str) -> str:
        """
        Format agent-specific prompt for assessment template.
        """
        agent_prompts = AgentSpecificPrompts.get_all_agent_prompts()
        
        if agent_type not in agent_prompts:
            return f"Unknown agent type: {agent_type}"
        
        prompt_data = agent_prompts[agent_type]
        
        expected_outputs = "\n".join([f"- {output}" for output in prompt_data["expected_outputs"]])
        success_criteria = "\n".join([f"- {criterion}" for criterion in prompt_data["success_criteria"]])
        common_issues = "\n".join([f"- {issue}" for issue in prompt_data["common_issues"]])
        
        return f"""**Assessment Criteria for {prompt_data['agent_name']}:**

**Agent Purpose:**
{prompt_data['agent_purpose']}

**Expected Outputs:**
{expected_outputs}

**Success Criteria:**
{success_criteria}

**Common Issues to Watch For:**
{common_issues}

**Assessment Focus Areas:**
{chr(10).join([f"- {focus}" for focus in prompt_data['assessment_focus']])}

**Improvement Strategies:**
{chr(10).join([f"- {strategy}" for strategy in prompt_data['improvement_strategies']])}""" 