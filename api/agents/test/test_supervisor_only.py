#!/usr/bin/env python3
"""
Test Supervisor Agent feedback for Theme Refinement step
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import the agents

from supervisor_agent import SupervisorAgent

async def test_supervisor_feedback():
    """Test supervisor feedback for theme refinement"""
    
    print("🔍 Testing Supervisor Agent Feedback")
    print("=" * 50)
    
    # Sample theme refinement output (from the failed run)
    sample_refinement_output = {
        "refinement_summary": {
            "total_themes_refined": 6,
            "total_academic_quotes": 0,  # This is likely the issue
            "total_key_concepts": 0,
            "average_quotes_per_theme": 0,
            "average_concepts_per_theme": 0,
            "themes_with_framework": 0,
            "themes_with_implications": 0
        },
        "refined_themes": [
            {
                "original_name": "Governance Dynamics in Blockchain and Web3",
                "refined_name": "Governance Dynamics within Blockchain Ecosystems",
                "precise_definition": "This theme examines the evolving structures...",
                "scope_boundaries": "Includes governance mechanisms...",
                "academic_quotes": [],  # Empty quotes
                "key_concepts": [],
                "theoretical_framework": "",
                "research_implications": ""
            }
        ],
        "generated_at": "2025-07-19T14:06:13.914773",
        "themes_refined": 6,
        "research_domain": "Blockchain and Web3 Governance"
    }
    
    # Initialize supervisor
    supervisor = SupervisorAgent()
    research_domain = "Blockchain and Web3 Governance"
    
    print(f"Testing supervisor quality check for theme refinement...")
    print(f"Research domain: {research_domain}")
    
    # Check quality
    quality_assessment = await supervisor.check_quality(
        agent_output=sample_refinement_output,
        agent_type="theme_refinement",
        research_domain=research_domain
    )
    
    print(f"\n📊 Quality Assessment Results:")
    print(f"Status: {quality_assessment.status}")
    print(f"Confidence: {quality_assessment.confidence:.2f}")
    print(f"Quality Score: {quality_assessment.quality_score:.2f}")
    print(f"Action: {quality_assessment.action}")
    
    print(f"\n📝 Feedback:")
    for i, feedback in enumerate(quality_assessment.feedback, 1):
        print(f"  {i}. {feedback}")
    
    print(f"\n🚨 Issues Found:")
    for i, issue in enumerate(quality_assessment.issues_found, 1):
        print(f"  {i}. {issue}")
    
    return quality_assessment

async def main():
    """Main test function."""
    print("🚀 Starting Supervisor Feedback Test")
    print("=" * 80)
    
    assessment = await test_supervisor_feedback()
    
    print("\n" + "=" * 80)
    if assessment.status == "HALT":
        print("❌ Supervisor would halt the pipeline")
    elif assessment.status == "REVISE":
        print("⚠️  Supervisor suggests revision")
    else:
        print("✅ Supervisor would approve")
    
    print(f"📅 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main()) 