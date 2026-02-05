"""
Test Supervisor Prompts

This file demonstrates how the supervisor prompt templates work
and shows example outputs for different scenarios.
"""

from .assessment_templates import AssessmentTemplates
from .agent_specific_prompts import AgentSpecificPrompts

def test_data_extractor_prompt():
    """
    Test the data extractor assessment prompt.
    """
    # Sample agent output
    agent_output = {
        "success": True,
        "data": {
            "documents": [
                {
                    "title": "Machine Learning in Healthcare: A Comprehensive Review",
                    "authors": ["Smith, J.", "Johnson, A."],
                    "year": 2023,
                    "abstract": "This paper reviews the application of machine learning in healthcare...",
                    "source": "PubMed",
                    "relevance_score": 0.85,
                    "url": "https://example.com/paper1"
                },
                {
                    "title": "AI Applications in Medical Diagnosis",
                    "authors": ["Brown, M.", "Davis, K."],
                    "year": 2022,
                    "abstract": "Artificial intelligence has revolutionized medical diagnosis...",
                    "source": "IEEE",
                    "relevance_score": 0.78,
                    "url": "https://example.com/paper2"
                }
            ],
            "total_documents": 2,
            "search_query": "machine learning healthcare",
            "sources_used": ["PubMed", "IEEE"]
        }
    }
    
    # Build complete assessment prompt
    prompt = AssessmentTemplates.build_complete_assessment_prompt(
        agent_output=agent_output,
        agent_type="data_extractor",
        user_query="machine learning applications in healthcare",
        research_domain="Healthcare Technology",
        pipeline_step="document_retrieval",
        previous_steps=[]
    )
    
    print("=== DATA EXTRACTOR ASSESSMENT PROMPT ===")
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    return prompt

def test_literature_review_prompt():
    """
    Test the literature review assessment prompt.
    """
    # Sample agent output
    agent_output = {
        "success": True,
        "data": {
            "summary": "The literature review covers machine learning applications in healthcare...",
            "key_findings": [
                "ML improves diagnostic accuracy",
                "AI reduces healthcare costs",
                "Ethical considerations are important"
            ],
            "research_gaps": [
                "Long-term clinical validation needed",
                "Integration with existing systems"
            ],
            "full_literature_review": "A comprehensive review of machine learning in healthcare...",
            "citations": ["Smith et al., 2023", "Brown et al., 2022"]
        }
    }
    
    # Build complete assessment prompt
    prompt = AssessmentTemplates.build_complete_assessment_prompt(
        agent_output=agent_output,
        agent_type="literature_review",
        user_query="machine learning applications in healthcare",
        research_domain="Healthcare Technology",
        pipeline_step="literature_review",
        previous_steps=["document_retrieval"]
    )
    
    print("=== LITERATURE REVIEW ASSESSMENT PROMPT ===")
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    return prompt

def test_emergency_prompt():
    """
    Test the emergency assessment prompt.
    """
    # Sample error scenario
    prompt = AssessmentTemplates.build_emergency_assessment_prompt(
        error_message="Failed to connect to external database",
        error_type="ConnectionError",
        agent_type="data_extractor",
        user_query="machine learning applications in healthcare",
        research_domain="Healthcare Technology"
    )
    
    print("=== EMERGENCY ASSESSMENT PROMPT ===")
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    return prompt

def test_learning_prompt():
    """
    Test the learning assessment prompt with previous context.
    """
    # Sample previous assessments
    previous_assessments = [
        {
            "status": "REVISE",
            "quality_score": 0.6,
            "issues_found": ["Too few documents", "Low relevance scores"],
            "strengths_identified": ["Good source diversity"]
        },
        {
            "status": "APPROVE",
            "quality_score": 0.85,
            "issues_found": [],
            "strengths_identified": ["Comprehensive coverage", "High relevance"]
        }
    ]
    
    # Sample user feedback
    user_feedback = {
        "preferences": ["Recent papers", "High impact journals"],
        "corrections": ["Include more clinical studies"],
        "satisfaction": "Good"
    }
    
    # Sample agent output
    agent_output = {
        "success": True,
        "data": {
            "documents": [
                {
                    "title": "Recent ML Applications in Clinical Settings",
                    "relevance_score": 0.9,
                    "source": "Nature Medicine"
                }
            ]
        }
    }
    
    # Build learning assessment prompt
    prompt = AssessmentTemplates.build_learning_assessment_prompt(
        agent_output=agent_output,
        agent_type="data_extractor",
        user_query="machine learning applications in healthcare",
        research_domain="Healthcare Technology",
        previous_assessments=previous_assessments,
        user_feedback=user_feedback
    )
    
    print("=== LEARNING ASSESSMENT PROMPT ===")
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    return prompt

def show_agent_criteria():
    """
    Show the assessment criteria for all agents.
    """
    print("=== AGENT ASSESSMENT CRITERIA ===")
    
    agent_prompts = AgentSpecificPrompts.get_all_agent_prompts()
    
    for agent_type, prompt_data in agent_prompts.items():
        print(f"\n--- {prompt_data['agent_name']} ---")
        print(f"Purpose: {prompt_data['agent_purpose']}")
        print(f"Expected Outputs: {len(prompt_data['expected_outputs'])} items")
        print(f"Success Criteria: {len(prompt_data['success_criteria'])} criteria")
        print(f"Common Issues: {len(prompt_data['common_issues'])} issues")
        print(f"Improvement Strategies: {len(prompt_data['improvement_strategies'])} strategies")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    # Test all prompt types
    show_agent_criteria()
    test_data_extractor_prompt()
    test_literature_review_prompt()
    test_emergency_prompt()
    test_learning_prompt() 