#!/usr/bin/env python3
"""
End-to-End Test script for Initial Coding Agent
Tests the full pipeline: Data Extractor → Retriever → Initial Coding Agent
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import the agents

from retriever_agent import RetrieverAgent
from initial_coding_agent import InitialCodingAgent

async def test_full_pipeline():
    """Test the complete pipeline: Retrieval → Initial Coding (skip data extraction)"""
    
    print("🚀 ===== Testing Full Pipeline: Retrieval → Initial Coding =====")
    print(f"📅 Test started at: {datetime.now()}")
    
    research_domain = "Blockchain and Web3 Governance"
    search_query = "blockchain governance transparency mechanisms"
    
    try:
        # Step 1: Retrieve existing documents from vector store
        print(f"\n🔍 Step 1: Retrieving existing documents...")
        print(f"   Query: '{search_query}'")
        print(f"   Domain: {research_domain}")
        
        # Retrieve existing data from vector store
        retriever = RetrieverAgent(collection_name="ResearchPaper", research_domain=research_domain)
        documents = await retriever.run(search_query, top_k=5)  # Get more documents for better testing
        
        if not documents or len(documents) == 0:
            print("   ❌ No documents found in vector store")
            print("   💡 Run data extraction first to populate the vector store")
            return False
        
        print(f"   ✅ Retrieved {len(documents)} existing documents from vector store")
        
        # Step 2: Display retrieved documents
        print(f"\n📄 Step 2: Document Overview...")
        print(f"   Retrieved {len(documents)} documents for coding")
        
        # Display retrieved documents
        for i, doc in enumerate(documents[:3]):  # Show first 3 docs
            print(f"   Document {i+1}:")
            print(f"      Title: {doc.get('title', 'Unknown')[:60]}...")
            print(f"      Authors: {doc.get('authors', 'Unknown')}")
            print(f"      Year: {doc.get('year', 'Unknown')}")
            print(f"      Content length: {len(doc.get('content', ''))} characters")
            print()
        
        # Step 3: Initial Coding
        print(f"\n🎯 Step 3: Initial Coding...")
        print("   ⚠️  This will make an LLM API call - ensure you have valid API keys!")
        
        # Debug: Show document structure
        print(f"\n🔍 DEBUG: Document structure check:")
        for i, doc in enumerate(documents[:2]):
            print(f"   Doc {i+1} keys: {list(doc.keys())}")
            print(f"   Doc {i+1} content length: {len(doc.get('content', ''))}")
            print(f"   Doc {i+1} content preview: {doc.get('content', '')[:200]}...")
            print()
        
        initial_coder = InitialCodingAgent()
        
        coding_result = await initial_coder.run(documents, research_domain)
        
        if "error" in coding_result:
            print(f"   ❌ Initial coding failed: {coding_result['error']}")
            return False
        
        print("   ✅ Initial coding completed successfully!")
        print(f"\n🔍 DEBUG: Raw coding result keys: {list(coding_result.keys())}")
        print(f"🔍 DEBUG: Coding summary: {coding_result.get('coding_summary', {})}")
        print(f"🔍 DEBUG: Number of coded units: {len(coding_result.get('coded_units', []))}")
        
        # If no coded units, let's see what went wrong
        if len(coding_result.get('coded_units', [])) == 0:
            print(f"\n⚠️  WARNING: No coded units found!")
            print(f"🔍 DEBUG: Documents analyzed: {coding_result.get('documents_analyzed', 0)}")
            print(f"🔍 DEBUG: Research domain: {coding_result.get('research_domain', 'Unknown')}")
            print(f"🔍 DEBUG: Generated at: {coding_result.get('generated_at', 'Unknown')}")
            
            # Check if there's an error
            if 'error' in coding_result:
                print(f"🔍 DEBUG: Error found: {coding_result['error']}")
        
        print(coding_result)
        
        # Display coding results
        summary = coding_result.get("coding_summary", {})
        print(f"\n📊 Coding Results Summary:")
        print(f"   Total units coded: {summary.get('total_units_coded', 0)}")
        print(f"   Unique codes generated: {summary.get('unique_codes_generated', 0)}")
        print(f"   Average confidence: {summary.get('average_confidence', 0):.2f}")
        
        # Show top codes
        code_frequencies = summary.get("code_frequencies", {})
        if code_frequencies:
            print(f"\n🏷️  Top Codes (by frequency):")
            sorted_codes = sorted(code_frequencies.items(), key=lambda x: x[1]['count'], reverse=True)
            for i, (code_name, data) in enumerate(sorted_codes[:5]):
                print(f"   {i+1}. {code_name} (count: {data['count']}, confidence: {data['avg_confidence']:.2f})")
        
        # Show sample coded units
        coded_units = coding_result.get("coded_units", [])
        if coded_units:
            print(f"\n📝 Sample Coded Units:")
            for i, unit in enumerate(coded_units[:2]):
                print(f"   Unit {i+1} (ID: {unit['unit_id']}):")
                print(f"      Source: {unit['source'][:50]}...")
                print(f"      Citation: {unit['harvard_citation']}")
                print(f"      Codes: {[code['name'] for code in unit['codes']]}")
                print(f"      Content preview: {unit['content'][:100]}...")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_retriever_only():
    """Test just the retriever to see what documents are available"""
    
    print("\n🔍 ===== Testing Retriever Only =====")
    
    research_domain = "Blockchain and Web3 Governance"
    search_queries = [
        "blockchain governance",
        "transparency mechanisms", 
        "stakeholder engagement",
        "decentralized governance"
    ]
    
    retriever = RetrieverAgent(collection_name="ResearchPaper", research_domain=research_domain)
    
    for query in search_queries:
        print(f"\n📚 Searching for: '{query}'")
        try:
            documents = await retriever.run(query, top_k=3)
            print(f"   Found {len(documents)} documents")
            
            for i, doc in enumerate(documents):
                print(f"   Doc {i+1}: {doc.get('title', 'Unknown')[:60]}...")
                print(f"      Authors: {doc.get('authors', 'Unknown')}")
                print(f"      Year: {doc.get('year', 'Unknown')}")
                print(f"      Content: {len(doc.get('content', ''))} chars")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Main test function with multiple test options."""
    print("🚀 Starting Initial Coding Agent End-to-End Tests")
    print("=" * 60)
    
    # Test options
    test_mode = "full"  # Options: "full", "retriever"
    
    if test_mode == "full":
        success = await test_full_pipeline()
    elif test_mode == "retriever":
        await test_retriever_only()
        success = True
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