#!/usr/bin/env python3
"""
Test script for Report Generator Agent
Tests the complete pipeline: All agents → Report Generation
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import the agents

from report_generator_agent import ReportGeneratorAgent

async def test_report_generation():
    """Test the report generation with sample data from all previous agents"""
    
    print("🚀 ===== Testing Report Generator Agent =====")
    print(f"📅 Test started at: {datetime.now()}")
    
    # Sample data from all previous agents
    sample_sections = {
        "research_domain": "Blockchain and Web3 Governance",
        
        # Literature Review Agent output
        "literature_review": {
            "summary": "The literature review examines transparency mechanisms in blockchain, Web3, and AI governance, highlighting the evolution of decentralized systems and their impact on trust and accountability.",
            "key_findings": [
                "Blockchain technology enhances transparency through immutable records",
                "Web3 governance models emphasize decentralization and user empowerment",
                "AI transparency requires explainable algorithms and ethical frameworks"
            ],
            "research_gaps": [
                "Limited empirical studies on cross-platform transparency mechanisms",
                "Need for standardized transparency metrics across domains",
                "Gap in understanding user perception of transparency in Web3"
            ],
            "full_literature_review": """
            The literature on transparency in blockchain, Web3, and AI governance reveals a complex landscape of technological innovation and governance challenges. Scholars have identified blockchain's inherent transparency through its immutable ledger system as a foundational element for building trust in decentralized networks (Nakamoto, 2008). More recent work has expanded this understanding to encompass Web3 governance models that emphasize user sovereignty and participatory decision-making (Buterin, 2014).

            The integration of AI into these systems has introduced new dimensions of transparency requirements, particularly around algorithmic decision-making and data processing (Russell, 2019). Research has shown that transparency in AI systems is not merely about revealing the inner workings of algorithms, but also about ensuring that stakeholders can understand and contest decisions that affect them (Doshi-Velez & Kim, 2017).

            However, significant gaps remain in our understanding of how transparency mechanisms function across different technological domains and how they interact with traditional governance structures. This thematic analysis seeks to address these gaps by synthesizing existing knowledge and identifying patterns that can inform future research and practice.
            """
        },
        
        # Initial Coding Agent output
        "initial_coding": {
            "coding_summary": {
                "total_units_coded": 15,
                "unique_codes_generated": 12,
                "average_confidence": 0.85,
                "primary_codes": ["governance transparency", "decentralized systems", "trust mechanisms"],
                "sub_codes": ["algorithmic accountability", "user empowerment", "immutable records"]
            },
            "coded_units": [
                {
                    "unit_id": "unit_0001",
                    "content": "Blockchain governance models emphasize transparency through public ledgers.",
                    "codes": [
                        {"name": "governance transparency", "definition": "Transparency in governance structures", "confidence": 0.9, "category": "primary"}
                    ],
                    "harvard_citation": "(Smith, 2022)"
                }
            ]
        },
        
        # Thematic Grouping Agent output
        "thematic_grouping": {
            "thematic_summary": {
                "total_themes_generated": 3,
                "total_codes_analyzed": 12,
                "cross_cutting_ideas": ["Trust as a foundational element", "User-centric design principles"]
            },
            "themes": [
                {
                    "theme_name": "Transparency and Security Applications of Blockchain",
                    "description": "This theme explores how blockchain technology is leveraged to enhance transparency and security across different sectors.",
                    "codes": [
                        {"name": "Transparency in genomic", "definition": "Transparency in blockchain governance", "confidence": 0.8, "category": "primary"}
                    ],
                    "justification": "These codes are grouped together because they all focus on the application of blockchain technology to enhance transparency and security in various domains.",
                    "cross_cutting_ideas": ["Blockchain as a cross-sectoral innovator"],
                    "academic_reasoning": "The grouping reflects the broader application of blockchain principles across different sectors."
                },
                {
                    "theme_name": "Blockchain-Enhanced Governance Models",
                    "description": "This theme focuses on governance frameworks and models enhanced by blockchain technology.",
                    "codes": [
                        {"name": "Governance models in blockchain", "definition": "Governance models in blockchain", "confidence": 0.8, "category": "primary"}
                    ],
                    "justification": "These codes are grouped together because they focus on governance structures and models that are enhanced or enabled by blockchain technology.",
                    "cross_cutting_ideas": ["Governance innovation through blockchain"],
                    "academic_reasoning": "The grouping emphasizes the role of blockchain in redefining governance approaches."
                }
            ]
        },
        
        # Theme Refinement Agent output
        "theme_refinement": {
            "refinement_summary": {
                "total_themes_refined": 2,
                "total_academic_quotes": 4,
                "total_key_concepts": 8
            },
            "refined_themes": [
                {
                    "original_name": "Transparency and Security Applications of Blockchain",
                    "refined_name": "Blockchain-Powered Transparency and Security Enhancements",
                    "precise_definition": "This theme examines the utilization of blockchain technology as a foundational tool for augmenting transparency and security within various sectors.",
                    "scope_boundaries": "Includes applications in finance, healthcare, supply chain, and environmental governance. Excludes non-blockchain transparency mechanisms.",
                    "academic_quotes": [
                        {"quote": "Blockchain technology presents an unparalleled opportunity to enhance sector-wide transparency and security.", "citation": "Smith & Doe, 2022"},
                        {"quote": "The application of blockchain in environmental agreements exemplifies its potential to ensure transparency.", "citation": "Johnson, 2021"}
                    ],
                    "key_concepts": ["immutable records", "decentralized verification", "trustless systems"],
                    "theoretical_framework": "Grounded in institutional theory and trust mechanisms in digital environments.",
                    "research_implications": "Suggests need for cross-sectoral studies on blockchain transparency implementation."
                },
                {
                    "original_name": "Blockchain-Enhanced Governance Models",
                    "refined_name": "Decentralized Governance Innovation through Blockchain",
                    "precise_definition": "This theme focuses on the transformation of governance structures through blockchain-enabled decentralization and participatory mechanisms.",
                    "scope_boundaries": "Encompasses DAOs, decentralized decision-making, and community governance. Excludes traditional centralized governance models.",
                    "academic_quotes": [
                        {"quote": "Decentralized governance models represent a paradigm shift in organizational structure.", "citation": "Brown, 2023"},
                        {"quote": "Blockchain governance requires new frameworks for accountability and participation.", "citation": "Wilson & Lee, 2022"}
                    ],
                    "key_concepts": ["decentralized autonomous organizations", "participatory governance", "consensus mechanisms"],
                    "theoretical_framework": "Based on democratic theory and organizational innovation literature.",
                    "research_implications": "Indicates need for empirical studies on DAO effectiveness and governance outcomes."
                }
            ]
        }
    }
    
    try:
        print(f"\n📝 Step 1: Initializing Report Generator Agent...")
        report_generator = ReportGeneratorAgent()
        
        print(f"\n📄 Step 2: Generating complete academic report...")
        print("   ⚠️  This will make an LLM API call for full report generation!")
        
        result = await report_generator.run(sample_sections)
        
        if "error" in result:
            print(f"   ❌ Report generation failed: {result['error']}")
            return False
        
        print(f"   ✅ Report generation completed successfully!")
        
        # Display report summary
        report_summary = result.get("report_summary", {})
        print(f"\n📊 Report Summary:")
        print(f"   Word Count: {report_summary.get('word_count', 0)}")
        print(f"   Total References: {report_summary.get('total_references', 0)}")
        print(f"   Report Length: {report_summary.get('report_length', 0)} characters")
        
        # Display sections included
        sections_included = report_summary.get("sections_included", {})
        print(f"\n📋 Sections Included:")
        for section, included in sections_included.items():
            status = "✅" if included else "❌"
            print(f"   {status} {section}")
        
        # Display file path
        file_path = result.get("file_path", "")
        if file_path:
            print(f"\n💾 Report saved to: {file_path}")
        else:
            print(f"\n⚠️  Report was not saved locally")
        
        # Display references
        references = result.get("references", [])
        if references:
            print(f"\n📚 References ({len(references)} total):")
            for i, ref in enumerate(references[:5], 1):  # Show first 5
                print(f"   {i}. {ref.get('full_citation', 'Unknown')}")
            if len(references) > 5:
                print(f"   ... and {len(references) - 5} more")
        
        # Show preview of report content
        report_content = result.get("report_content", "")
        if report_content:
            print(f"\n📖 Report Preview (first 500 characters):")
            print(f"{'='*60}")
            print(report_content[:500] + "..." if len(report_content) > 500 else report_content)
            print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Report Generator Agent Test")
    print("=" * 60)
    
    success = await test_report_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Report generation test completed successfully!")
    else:
        print("⚠️  Report generation test failed - check the output above for details")
    
    print(f"📅 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main()) 