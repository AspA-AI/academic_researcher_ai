import asyncio
from api.agents.retriever_agent import RetrieverAgent
from api.utils.weaviate_client import get_weaviate_manager

async def main():
    # First, let's check what collections exist
    print("🔍 Checking all available collections...")
    weaviate = get_weaviate_manager()
    
    try:
        # List all collections using the correct API
        collections = weaviate.client.collections.list_all()
        print(f"[DEBUG] Available collections: {collections}")
        
        # Check each collection for documents
        for collection_name in collections:
            print(f"\n📊 Collection: {collection_name}")
            try:
                collection = weaviate.client.collections.get(collection_name)
                count_result = collection.aggregate.over_all(total_count=True)
                total_count = count_result.total_count
                print(f"   Documents: {total_count}")
                
                if total_count > 0:
                    # Get a sample document
                    sample_docs = collection.with_limit(1).do()
                    if sample_docs.objects:
                        print(f"   Sample document keys: {list(sample_docs.objects[0].properties.keys())}")
                    else:
                        print("   No objects found")
                    
            except Exception as e:
                print(f"   Error checking collection: {e}")
        
        # Now specifically check ResearchPaper collection
        print(f"\n🔍 Specifically checking ResearchPaper collection...")
        try:
            research_paper_collection = weaviate.client.collections.get("ResearchPaper")
            count_result = research_paper_collection.aggregate.over_all(total_count=True)
            total_count = count_result.total_count
            print(f"[DEBUG] Total documents in ResearchPaper collection: {total_count}")
            
            if total_count > 0:
                # Get a few sample documents to see what's there
                sample_docs = research_paper_collection.with_limit(2).do()
                print(f"[DEBUG] Sample documents from ResearchPaper:")
                for i, doc in enumerate(sample_docs.objects):
                    print(f"  Document {i+1}:")
                    for key, value in doc.properties.items():
                        if key == 'content' and len(str(value)) > 100:
                            print(f"    {key}: {str(value)[:100]}...")
                        else:
                            print(f"    {key}: {value}")
            else:
                print("❌ ResearchPaper collection exists but has 0 documents")
                
        except Exception as e:
            print(f"[ERROR] Could not check ResearchPaper collection: {e}")
            
    except Exception as e:
        print(f"[ERROR] Could not list collections: {e}")
        return

    # Now run the retriever agent
    print("\n🔍 Running similarity search...")
    agent = RetrieverAgent(
        collection_name="ResearchPaper", 
        research_domain="Web3 and Blockchain Technology"
        )
    
    results = await agent.run(
        query="blockchain technology academic research",
        top_k=3
    )
    
    print(f"\n📊 Search Results:")
    print(f"Query: 'blockchain technology academic research'")
    print(f"Results found: {len(results)}")
    
    if results:
        print("\nTop retrieved documents:")
        for i, doc in enumerate(results, 1):
            print(f"\nDocument {i}:")
            for k, v in doc.items():
                if k == 'content' and len(str(v)) > 200:
                    print(f"  {k}: {str(v)[:200]}...")
                else:
                    print(f"  {k}: {v}")
    else:
        print("❌ No documents found matching the query")

if __name__ == "__main__":
    asyncio.run(main()) 