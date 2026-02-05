import os
import aiohttp
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone
from io import BytesIO
import PyPDF2
import sys
import os
import random
# Add the api directory to the path
# Robust import to work in both direct and package contexts
try:
    from utils.vector_store_manager import VectorStoreManager
except ImportError:  # pragma: no cover
    from api.utils.vector_store_manager import VectorStoreManager  # type: ignore

class DataExtractorAgent:
    """
    Fetches raw academic texts from external sources (e.g., CORE API, Arxiv, Semantic Scholar),
    extracts relevant metadata, and stores documents in a vector database for retrieval.
    """
    def __init__(self):
        # Initialize any API clients, vector store managers, etc.
        pass

    async def fetch_papers(self, query: str, max_results: int = None, year_from: int = None, year_to: int = None) -> List[Dict[str, Any]]:
        """
        Fetch academic papers and metadata from CORE API with retries, backoff, and pagination.
        """
        api_key = os.getenv("CORE_API_KEY")
        print(f"[DEBUG] CORE_API_KEY found: {bool(api_key)}")

        if not api_key:
            print(f"[WARNING] CORE API key not found, returning empty results")
            return []
        
        # Respect incoming params; provide conservative fallbacks
        target_total = max_results if max_results is not None else 20
        y_from = year_from if year_from is not None else 2020
        y_to = year_to if year_to is not None else 2024

        print(f"[DEBUG] Fetching papers with query: '{query}', max_results: {target_total}")
        
        url = "https://api.core.ac.uk/v3/search/works"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Use small page size to reduce load on CORE; we page until target_total
        page_size = min(5, target_total) if target_total > 0 else 0
        papers: List[Dict[str, Any]] = []
        scroll_id: str | None = None

        # Retry policy
        max_attempts = 3
        timeout = aiohttp.ClientTimeout(total=12)

        async def _attempt_request(session: aiohttp.ClientSession, payload: Dict[str, Any]) -> Dict[str, Any] | None:
            for attempt in range(max_attempts):
                try:
                    async with session.post(url, headers=headers, json=payload) as response:
                        print(f"[DEBUG] CORE API response status: {response.status}")
                        if response.status == 200:
                            data = await response.json()
                            print(f"[DEBUG] CORE API response received successfully")
                            return data
                        # Transient errors: 429/5xx → backoff and retry
                        if response.status in (429, 500, 502, 503, 504):
                            body_text = await response.text()
                            if response.status == 429:
                                print(f"[WARNING] CORE API rate limit exceeded (429)")
                            else:
                                print(f"[WARNING] CORE API server error ({response.status}): {body_text}")
                            retry_after = response.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    delay = min(10.0, float(retry_after))
                                except ValueError:
                                    delay = 0.0
                            else:
                                delay = (1.5 ** attempt) + random.random() * 0.5
                            print(f"[INFO] Backing off for {delay:.2f}s before retry {attempt+1}/{max_attempts}")
                            await asyncio.sleep(delay)
                            continue
                        # Non-retryable
                        error_text = await response.text()
                        print(f"[ERROR] CORE API request failed with status {response.status}")
                        print(f"[ERROR] Response: {error_text}")
                        return None
                except asyncio.TimeoutError:
                    print(f"[ERROR] CORE API request timed out (attempt {attempt+1}/{max_attempts})")
                    delay = (1.5 ** attempt) + random.random() * 0.5
                    await asyncio.sleep(delay)
                except Exception as e:
                    print(f"[ERROR] Unexpected error fetching papers (attempt {attempt+1}/{max_attempts}): {e}")
                    delay = (1.5 ** attempt) + random.random() * 0.5
                    await asyncio.sleep(delay)
            return None
        
        if page_size <= 0:
            return []

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                while len(papers) < target_total:
                    # Build payload for this page
                    payload: Dict[str, Any] = {
                        "q": query,
                        "limit": min(page_size, target_total - len(papers)),
                        "scroll": True,
                        "year_from": y_from,
                        "year_to": y_to,
                        "fields": [
                            "title", "authors", "abstract", "year", "doi", "downloadUrl", "citations", "language"
                        ]
                    }
                    if scroll_id:
                        payload["scroll_id"] = scroll_id

                    print(f"[DEBUG] CORE API payload: {payload}")
                    data = await _attempt_request(session, payload)
                    if not data:
                        print("[INFO] Returning what we have due to repeated CORE errors")
                        break

                    results = data.get("results", []) or []
                    scroll_id = data.get("scroll_id")
                    print(f"[DEBUG] Found {len(results)} papers in this page; scroll_id present: {bool(scroll_id)}")

                    # Map results
                    for result in results:
                        paper = {
                            "title": result.get("title", "Unknown Title"),
                            "authors": result.get("authors", []),
                            "abstract": result.get("abstract", ""),
                            "year": result.get("year", y_to),
                            "doi": result.get("doi", ""),
                            "downloadUrl": result.get("downloadUrl", ""),
                            "citations": result.get("citations", []),
                            "language": result.get("language", "en")
                        }
                        papers.append(paper)
                        if len(papers) >= target_total:
                            break

                    # Stop if no more results or no scroll token
                    if not results or not scroll_id:
                        break
        except Exception as e:
            print(f"[ERROR] Unexpected error in fetch_papers loop: {e}")
            return papers

        print(f"[DEBUG] Successfully processed {len(papers)} papers (requested {target_total})")
        return papers

    async def extract_pdf_content(self, pdf_url: str, paper_id: str) -> Dict[str, Any]:
        """
        Extract text content from a PDF file given its URL.
        """
        print(f"[DEBUG] Extracting PDF content for paper_id: {paper_id}")
        print(f"[DEBUG] PDF URL: {pdf_url}")
        
        # Handle arXiv URLs
        if "arxiv.org/abs/" in pdf_url:
            pdf_url = pdf_url.replace("/abs/", "/pdf/") + ".pdf"
            print(f"[DEBUG] Converted arXiv URL to: {pdf_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                print(f"[DEBUG] PDF download response status: {response.status}")
                
                if response.status == 200:
                    content_bytes = await response.read()
                    print(f"[DEBUG] Downloaded {len(content_bytes)} bytes")
                    
                    if content_bytes.startswith(b'%PDF'):
                        print(f"[DEBUG] Content is a valid PDF")
                        try:
                            pdf_file = BytesIO(content_bytes)
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            print(f"[DEBUG] PDF has {len(pdf_reader.pages)} pages")
                            
                            extracted_text = ""
                            for page_num, page in enumerate(pdf_reader.pages):
                                try:
                                    page_text = page.extract_text()
                                    if page_text:
                                        extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                                        print(f"[DEBUG] Extracted {len(page_text)} characters from page {page_num + 1}")
                                except Exception as e:
                                    print(f"[WARNING] Could not extract text from page {page_num + 1}: {e}")
                                    continue
                            
                            if extracted_text.strip():
                                cleaned_text = extracted_text.strip()
                                word_count = len(cleaned_text.split())
                                print(f"[DEBUG] Successfully extracted {word_count} words from PDF")
                                
                                return {
                                    "paper_id": paper_id,
                                    "extraction_status": "success",
                                    "content": cleaned_text,
                                    "word_count": word_count
                                }
                        except Exception as e:
                            print(f"[ERROR] Failed to process PDF content: {e}")
                            return {
                                "paper_id": paper_id,
                                "extraction_status": "failed",
                                "error": str(e)
                            }
                else:
                    print(f"[ERROR] Failed to download PDF. Status: {response.status}")
                    return {
                        "paper_id": paper_id,
                        "extraction_status": "failed",
                        "error": f"HTTP status {response.status}"
                    }

        return {
            "paper_id": paper_id,
            "extraction_status": "failed",
            "error": "Invalid PDF content"
        }

    async def store_in_vector_db(self, papers: List[Dict[str, Any]], research_domain: str) -> Dict[str, Any]:
        """
        Store papers and their content in a Weaviate vector database for retrieval.
        """
        print(f"[DEBUG] store_in_vector_db called with {len(papers)} papers")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        vstore = VectorStoreManager(collection_name="ResearchPaper", research_domain=research_domain)
        chunks = []
        metadata_list = []
        
        for i, paper in enumerate[Dict[str, Any]](papers):
            print(f"[DEBUG] Processing paper {i+1}/{len(papers)}")
            print(f"[DEBUG] Paper title: {paper.get('title', 'No title')[:50]}...")
            
            content = paper.get("extracted_content") or paper.get("content")
            if not content:
                print(f"[WARNING] No content found for paper {i+1}")
                continue
            
            print(f"[DEBUG] Paper content length: {len(content)} characters")
            
            # Simple chunking (could use utils.chunking for more advanced)
            paper_chunks = [content[j:j+1000] for j in range(0, len(content), 1000)]
            print(f"[DEBUG] Created {len(paper_chunks)} chunks for paper {i+1}")
            
            for j, chunk in enumerate(paper_chunks):
                chunks.append(chunk)
                
                # Handle authors - convert list to string if needed
                authors = paper.get("authors", [])
                if isinstance(authors, list):
                    authors_str = ", ".join([str(author) for author in authors])
                else:
                    authors_str = str(authors)
                
                meta = {
                    "title": paper.get("title", ""),
                    "authors": authors_str,  # Convert to string
                    "year": paper.get("year"),
                    "doi": paper.get("doi", ""),
                    "source": paper.get("source", ""),
                    "paper_id": paper.get("doi", paper.get("title", "")),
                    "chunk_index": j
                }
                metadata_list.append(meta)
                
                if j < 2:  # Log first few chunks
                    print(f"[DEBUG] Chunk {j+1}: {len(chunk)} chars, metadata: {meta}")
        
        print(f"[DEBUG] Total chunks to store: {len(chunks)}")
        print(f"[DEBUG] Total metadata entries: {len(metadata_list)}")
        
        if chunks:
            print(f"[DEBUG] Calling vstore.add_chunks...")
            result = vstore.add_chunks(chunks, metadata_list)
            print(f"[DEBUG] vstore.add_chunks returned: {result}")
            return {
                "status": "success",
                "papers_processed": len(papers),
                "chunks_stored": len(chunks),
                "vectorstore_name": "ResearchPaper"
            }
        else:
            print(f"[ERROR] No chunks to store!")
            return {
                "status": "error",
                "error": "No content chunks to store"
            }

    async def run(self, query: str, max_results: int = None, year_from: int = None, year_to: int = None, research_domain: str = None) -> Dict[str, Any]:
        """
        Main entry point for data extraction pipeline.
        1. Fetch papers
        2. Extract PDF content
        3. Store in vector DB
        Returns a summary of the ingestion process.
        """
        print(f"[DEBUG] ===== Starting DataExtractorAgent.run =====")
        print(f"[DEBUG] Query: {query}")
        print(f"[DEBUG] Max results: {max_results}")
        print(f"[DEBUG] Year from: {year_from}")
        print(f"[DEBUG] Year to: {year_to}")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        # Step 1: Fetch papers
        print(f"[DEBUG] Step 1: Fetching papers...")
        papers = await self.fetch_papers(query, max_results or 20, year_from or 2020, year_to or 2024)
        print(f"[DEBUG] Fetched {len(papers)} papers")
        
        # Handle case where no papers were found
        if not papers:
            print(f"[WARNING] No papers found for query: {query}")
            print(f"[INFO] This could be due to:")
            print(f"[INFO] - API being temporarily unavailable")
            print(f"[INFO] - No papers matching the search criteria")
            print(f"[INFO] - Network connectivity issues")
            
            final_result = {
                "papers_fetched": 0,
                "papers_extracted": 0,
                "vector_store_result": {
                    "status": "warning",
                    "message": "No papers found to process",
                    "papers_processed": 0,
                    "chunks_stored": 0
                }
            }
            
            print(f"[DEBUG] ===== DataExtractorAgent.run completed (no papers) =====")
            return final_result
        
        # Step 2: Extract PDF content
        print(f"[DEBUG] Step 2: Extracting PDF content...")
        extracted_papers = []
        for i, paper in enumerate(papers):
            print(f"[DEBUG] Processing paper {i+1}/{len(papers)}")
            pdf_url = paper.get('downloadUrl', '')
            if not pdf_url:
                print(f"[WARNING] No PDF URL for paper {i+1}")
                continue
            
            extraction_result = await self.extract_pdf_content(pdf_url, f"paper_{i}")
            print(f"[DEBUG] Extraction result for paper {i+1}: {extraction_result.get('extraction_status')}")
            
            if extraction_result.get("extraction_status") == "success":
                enriched_paper = {**paper, "extracted_content": extraction_result.get("content", "")}
                extracted_papers.append(enriched_paper)
                print(f"[DEBUG] Successfully enriched paper {i+1}")
            else:
                print(f"[ERROR] Failed to extract paper {i+1}: {extraction_result.get('error')}")
        
        print(f"[DEBUG] Successfully extracted content from {len(extracted_papers)} papers")
        
        # Step 3: Store in vector DB
        print(f"[DEBUG] Step 3: Storing in vector database...")
        if extracted_papers:
            store_result = await self.store_in_vector_db(extracted_papers, research_domain or "General")
        else:
            print(f"[WARNING] No papers successfully extracted")
            store_result = {
                "status": "warning",
                "message": "No papers had extractable content",
                "papers_processed": 0,
                "chunks_stored": 0
            }
        
        print(f"[DEBUG] Store result: {store_result}")
        
        final_result = {
            "papers_fetched": len(papers),
            "papers_extracted": len(extracted_papers),
            "vector_store_result": store_result
        }
        
        print(f"[DEBUG] ===== DataExtractorAgent.run completed =====")
        print(f"[DEBUG] Final result: {final_result}")
        
        return final_result 

    async def process_documents(self, documents: List[Dict[str, Any]], research_domain: str = "General") -> Dict[str, Any]:
        """
        Process existing documents without fetching from external sources.
        Handles documents that users provide directly.
        """
        print(f"[DEBUG] ===== Starting DataExtractorAgent.process_documents =====")
        print(f"[DEBUG] Documents to process: {len(documents)}")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        processed_documents = []
        
        for i, doc in enumerate(documents):
            print(f"[DEBUG] Processing document {i+1}/{len(documents)}")
            
            # Handle optional fields with defaults
            title = doc.get('title', f'Document_{i+1}')
            content = doc.get('content', '')
            authors = doc.get('authors', [])
            year = doc.get('year', 2024)
            
            # If no content, try to use title as search query
            if not content and title:
                print(f"[DEBUG] No content provided, using title as research indication")
                content = f"Research document about: {title}"
            
            # Create a standardized document structure
            processed_doc = {
                'title': title,
                'authors': authors,
                'year': year,
                'abstract': content[:500] + "..." if len(content) > 500 else content,
                'extracted_content': content,
                'doi': doc.get('doi', ''),
                'downloadUrl': doc.get('url', ''),
                'language': doc.get('language', 'en'),
                'document_source': 'user_provided'
            }
            
            processed_documents.append(processed_doc)
            print(f"[DEBUG] Successfully processed document: {title}")
        
        # Store in vector database
        print(f"[DEBUG] Storing {len(processed_documents)} documents in vector database...")
        store_result = await self.store_in_vector_db(processed_documents, research_domain)
        print(f"[DEBUG] Store result: {store_result}")
        
        final_result = {
            "documents_provided": len(documents),
            "documents_processed": len(processed_documents),
            "vector_store_result": store_result,
            "extraction_mode": "document_processing"
        }
        
        print(f"[DEBUG] ===== DataExtractorAgent.process_documents completed =====")
        print(f"[DEBUG] Final result: {final_result}")
        
        return final_result 