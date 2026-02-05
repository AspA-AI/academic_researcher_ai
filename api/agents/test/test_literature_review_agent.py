import asyncio
from api.agents.literature_review_agent import LiteratureReviewAgent
from api.agents.retriever_agent import RetrieverAgent

async def main():
    print("🔍 Testing Literature Review Agent")
    print("=" * 50)
    
    # Step 1: Get documents from Retriever Agent
    print("📚 Step 1: Retrieving documents from Weaviate...")
    retriever = RetrieverAgent(
        collection_name="ResearchPaper", 
        research_domain="Web3 and Blockchain Technology"
    )
    
    # Get more documents for a comprehensive literature review
    retrieved_docs = await retriever.run(
        query="blockchain technology academic research",
        top_k=10  # Get more documents for better analysis
    )
    
    print(f"✅ Retrieved {len(retrieved_docs)} documents")
    
    if not retrieved_docs:
        print("❌ No documents retrieved. Cannot generate literature review.")
        return
    
    # Step 2: Generate literature review
    print("\n📝 Step 2: Generating literature review...")
    literature_agent = LiteratureReviewAgent()
    
    # Convert retrieved documents to the format expected by literature review agent
    # The retriever returns documents with 'properties' field, but literature review expects direct properties
    formatted_docs = []
    for doc in retrieved_docs:
        # Extract properties from the retrieved document
        props = doc.get('properties', {})
        formatted_doc = {
            'title': props.get('title', 'Unknown'),
            'authors': props.get('authors', 'Unknown'),
            'year': props.get('year', 'Unknown'),
            'doi': props.get('doi', 'Unknown'),
            'abstract': props.get('content', '')[:500] + "..." if len(props.get('content', '')) > 500 else props.get('content', ''),
            'extracted_content': props.get('content', ''),
            'source': props.get('source', 'Unknown'),
            'research_domain': props.get('research_domain', 'Unknown')
        }
        formatted_docs.append(formatted_doc)
    
    print(f"[DEBUG] Formatted {len(formatted_docs)} documents for literature review")
    
    # Generate the literature review
    literature_review = await literature_agent.run(
        documents=formatted_docs,
        research_domain="Web3 and Blockchain Technology"
    )
    
    # Step 3: Display results
    print("\n📊 AAAAAAAAAAAAAAAAAAAAAAAAAA Literature Review Results: AAAAAAAAAAAAAAAAAAAAAAAAAA")
    print(literature_review)
    
    if "error" in literature_review:
        print(f"❌ Error: {literature_review['error']}")
        return
    
    print(f"✅ Literature review generated successfully!")
    print(f"📄 Documents analyzed: {literature_review.get('documents_analyzed', 'Unknown')}")
    print(f"🔬 Research domain: {literature_review.get('research_domain', 'Unknown')}")
    print(f"⏰ Generated at: {literature_review.get('generated_at', 'Unknown')}")
    
    # Display the structured sections
    print("\n" + "="*50)
    print("📋 LITERATURE REVIEW")
    print("="*50)
    
    # Display the full literature review first
    if literature_review.get('full_literature_review'):
        print("\n📖 FULL LITERATURE REVIEW:")
        print("-" * 20)
        print(literature_review['full_literature_review'])
    
    # Summary
    if literature_review.get('summary'):
        print("\n📖 SUMMARY:")
        print("-" * 20)
        print(literature_review['summary'])
    
    # Key Findings
    if literature_review.get('key_findings'):
        print("\n🔍 KEY FINDINGS:")
        print("-" * 20)
        for i, finding in enumerate(literature_review['key_findings'][:5], 1):  # Show first 5
            print(f"{i}. {finding}")
    
    # Research Gaps
    if literature_review.get('research_gaps'):
        print("\n🕳️ RESEARCH GAPS:")
        print("-" * 20)
        for i, gap in enumerate(literature_review['research_gaps'][:5], 1):  # Show first 5
            print(f"{i}. {gap}")
    
    # Methodologies
    if literature_review.get('methodologies'):
        print("\n🔬 METHODOLOGIES:")
        print("-" * 20)
        for i, method in enumerate(literature_review['methodologies'][:5], 1):  # Show first 5
            print(f"{i}. {method}")
    
    # Future Directions
    if literature_review.get('future_directions'):
        print("\n🚀 FUTURE DIRECTIONS:")
        print("-" * 20)
        for i, direction in enumerate(literature_review['future_directions'][:5], 1):  # Show first 5
            print(f"{i}. {direction}")
    
    print("\n" + "="*50)
    print("✅ Literature Review Agent test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 