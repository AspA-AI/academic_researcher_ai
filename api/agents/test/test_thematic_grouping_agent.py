#!/usr/bin/env python3
"""
End-to-End Test script for Thematic Grouping Agent
Tests the pipeline: Retrieval → Initial Coding → Thematic Grouping
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import the agents

from retriever_agent import RetrieverAgent
from initial_coding_agent import InitialCodingAgent
from thematic_grouping_agent import ThematicGroupingAgent

async def test_full_pipeline():
    """Test the complete pipeline: Retrieval → Initial Coding → Thematic Grouping"""
    
    print("🚀 ===== Testing Full Pipeline: Retrieval → Initial Coding → Thematic Grouping =====")
    print(f"📅 Test started at: {datetime.now()}")
    
    research_domain = "Blockchain and Web3 Governance"
    search_query = "blockchain governance transparency mechanisms"
    
    try:
        # Step 1: Retrieve existing documents from vector store
        print(f"\n🔍 Step 1: Retrieving existing documents...")
        print(f"   Query: '{search_query}'")
        print(f"   Domain: {research_domain}")
        
        retriever = RetrieverAgent(collection_name="ResearchPaper", research_domain=research_domain)
        documents = await retriever.run(search_query, top_k=5)
        
        if not documents or len(documents) == 0:
            print("   ❌ No documents found in vector store")
            print("   💡 Run data extraction first to populate the vector store")
            return False
        
        print(f"   ✅ Retrieved {len(documents)} existing documents from vector store")
        
        # Step 2: Initial Coding
        print(f"\n🎯 Step 2: Initial Coding...")
        print("   ⚠️  This will make an LLM API call - ensure you have valid API keys!")
        
        initial_coder = InitialCodingAgent()
        coding_result = await initial_coder.run(documents, research_domain)
        
        if "error" in coding_result:
            print(f"   ❌ Initial coding failed: {coding_result['error']}")
            return False
        
        print("   ✅ Initial coding completed successfully!")
        
        # Display coding results
        summary = coding_result.get("coding_summary", {})
        print(f"  Intial Coding Summary: =================================")
        print(coding_result)
        print(f"      Total units coded: {summary.get('total_units_coded', 0)}")
        print(f"      Unique codes generated: {summary.get('unique_codes_generated', 0)}")
        print(f"      Average confidence: {summary.get('average_confidence', 0):.2f}")
        
        # Step 3: Thematic Grouping
        print(f"\n🎨 Step 3: Thematic Grouping...")
        print("   ⚠️  This will make another LLM API call for thematic analysis!")
        
        thematic_grouper = ThematicGroupingAgent()
        coded_units = coding_result.get("coded_units", [])
        print("Thematic Grouping Agent: coded_units =================================")
        print(coded_units)
        if not coded_units:
            print("   ❌ No coded units available for thematic grouping")
            return False
        
        thematic_result = await thematic_grouper.run(coded_units, research_domain)
        
        if "error" in thematic_result:
            print(f"   ❌ Thematic grouping failed: {thematic_result['error']}")
            return False
        
        print("   ✅ Thematic grouping completed successfully!")
        
        # Display thematic results
        thematic_summary = thematic_result.get("thematic_summary", {})
        print(f"\n📊 Thematic Analysis Summary:")
        print(f"   Total themes generated: {thematic_summary.get('total_themes_generated', 0)}")
        print(f"   Total codes analyzed: {thematic_summary.get('total_codes_analyzed', 0)}")
        print(f"   Unique codes clustered: {thematic_summary.get('unique_codes_clustered', 0)}")
        print(f"   Average codes per theme: {thematic_summary.get('average_codes_per_theme', 0):.1f}")
        
        # Show themes
        themes = thematic_result.get("themes", [])
        if themes:
            print(f"\n🎨 Generated Themes:")
            for i, theme in enumerate(themes, 1):
                print(f"   Theme {i}: {theme['theme_name']}")
                print(f"      Description: {theme['description'][:100]}...")
                print(f"      Codes included: {len(theme['codes'])}")
                print(f"      Justification: {theme['justification'][:100]}...")
                print()
        
        # Show cross-cutting ideas
        cross_cutting = thematic_summary.get("cross_cutting_ideas", [])
        if cross_cutting:
            print(f"\n🔗 Cross-Cutting Ideas:")
            for i, idea in enumerate(cross_cutting[:5], 1):
                print(f"   {i}. {idea}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_thematic_grouping_only():
    """Test just the thematic grouping with sample coded units"""
    
    print("\n🎨 ===== Testing Thematic Grouping Only =====")
    
    # Sample coded units from previous Initial Coding Agent run
    sample_coded_units = [
        {
            "unit_id": "unit_0000",
            "content": "A governance model to distribute power, decision-making, and responsibilities in the network.",
            "source": "Blockchain For Food: Making Sense of Technology",
            "authors": ["Coppoolse, Kirsten", "Walton, Jenny"],
            "year": 2024,
            "codes": [
                {
                    "name": "Governance models in",
                    "definition": "Governance models in blockchain",
                    "confidence": 0.8,
                    "category": "primary"
                },
                {
                    "name": "Decentralized governance",
                    "definition": "A model of governance in blockchain that emphasizes distributed and democratic decision-making processes.",
                    "confidence": 0.8,
                    "category": "sub"
                }
            ],
            "harvard_citation": "(Coppoolse et al., 2024)",
            "insights": ["Governance is central to blockchain functionality"]
        },
        {
            "unit_id": "unit_0001",
            "content": "Transparency protects the functioning of genomic research.",
            "source": "Dwarna: a blockchain solution for dynamic consent",
            "authors": ["Desira, Maria", "Martin, Gillian M."],
            "year": 2024,
            "codes": [
                {
                    "name": "Transparency in blockchain",
                    "definition": "Transparency in blockchain governance",
                    "confidence": 0.8,
                    "category": "primary"
                },
                {
                    "name": "Trust and consent",
                    "definition": "Trust and consent in genomic research",
                    "confidence": 0.8,
                    "category": "sub"
                }
            ],
            "harvard_citation": "(Desira et al., 2024)",
            "insights": ["Transparent governance bolsters trust and consent"]
        }
    ]
    
    research_domain = "Blockchain and Web3 Governance"
    
    try:
        thematic_grouper = ThematicGroupingAgent()
        result = await thematic_grouper.run(sample_coded_units, research_domain)
        
        if "error" in result:
            print(f"❌ Thematic grouping failed: {result['error']}")
            return False
        
        print(f"✅ Thematic grouping completed successfully!")
        print(f"📊 Generated {result.get('thematic_summary', {}).get('total_themes_generated', 0)} themes")
        
        return True
        
    except Exception as e:
        print(f"❌ Thematic grouping test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function with multiple test options."""
    print("🚀 Starting Thematic Grouping Agent End-to-End Tests")
    print("=" * 60)
    
    # Test options
    test_mode = "full"  # Options: "full", "thematic_only"
    
    if test_mode == "full":
        success = await test_full_pipeline()
    elif test_mode == "thematic_only":
        success = await test_thematic_grouping_only()
    else:
        print("❌ Invalid test mode")
        return
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("⚠️  Some tests failed - check the output above for details")
    
    print(f"📅 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main()) 