import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import os, json_repair, json
# Add the api directory to the path
from api.utils.llm_backends import get_llm_backend
from api.agents.supervisor_prompts.assessment_templates import AssessmentTemplates

class RetrieverValidatorAgent:
    """
    Validity Control validator Agent that reviews retriever agnet output and decides whether to proceed.
    """
    def __init__(self, llm_backend=None):
        # Initialize with OpenAI backend by default
        self.llm_backend = llm_backend or get_llm_backend("openai")

    @staticmethod
    def extract_json(response, quite=False):
        try:   
            """ Json Extraction """ 

            if isinstance(response, (dict, list)):
                # return as it is 
                # if not quite: print("extract_json", "response is already in json format")
                return response       
            elif isinstance(response, str):
                # Method 1
                try:
                    # try simple to load it as jsonfrom collections import defaultdict

                    res = json.loads(response)
                    # if not quite: print("extract_json", "response is already in jsons format")
                    return res
                except:
                    pass
                    # if not quite: print("extract_json: simple json load failed. Trying to fix json string ...")
                
                # Method 2 
                try:
                    # if not quite: print("extract_json", "response is not in json format. Trying to extract json from response")
                    text = response
                    if '```json' in text:                
                        out = text.split('```json')[1].split('```')[0].replace('\n','')
                    elif '```' in text:
                        out = text.split('```')[1].split('```')[0].replace('\n','')
                    else:
                        out = text

                    res = json.loads(out)
                    return res        
                except Exception as e:
                    # if not quite: print(f"extract_json: unable to fix json string. Trying with json_repair ...")
                    pass         
                    # it is not in json string format
                    
                    # Method 3
                    text = response
                    try:                
                        res = json_repair.loads(text)
                        if isinstance(res, (dict, list)):
                            # if not quite: print("extract_json: result obtained using repair json")
                            return res
                    except:
                        # if not quite: print("extract_json: unable to repair json string using json_repair. Raise exception")
                        raise
            else:
                if not quite: print("extract_json", "response is not a string or a dictionary")
                return {}
            
        except Exception as e:
            return {'error': str(e)}
    

    def _build_prompt(self, query, documents: List[Dict[str, Any]], research_domain: str = "General") -> str:
        """
        Construct a prompt for the LLM to generate a literature review.
        """
        from api.agents.agent_prompts.retriever_validation_prompts import RetriverValidationPrompts
        
        return RetriverValidationPrompts.build_retriver_validation_prompt(
            documents=documents,
            research_domain=research_domain,
            query=query
        )

    async def run(self, query, documents: List[Dict[str, Any]], research_domain: str = "General") -> Dict[str, Any]:
        """
        Main entry point for literature review generation.
        Args:
            documents (List[Dict]): List of academic documents (with extracted content).
            research_domain (str): The research domain/topic.
            query(str): The user query
        Returns:
            Dict: Structured validation result including retrieval_validation and academic_feasibility.
        """
        # Allow empty documents for early academic-feasibility checks; prompt will see no retrieved docs.
        print(f"[DEBUG] ReviewerValidationAgent.run called with {len(documents)} documents")
        print(f"[DEBUG] Research domain: {research_domain}")
        
        prompt = self._build_prompt(query, documents, research_domain)
        print(f"[DEBUG] Generated prompt length: {len(prompt)} characters")
        
        if not self.llm_backend:
            return {"error": "No LLM backend provided."}
        
        print(f"[DEBUG] Using LLM backend: {self.llm_backend.get_model_info()}")
        
        try:
            llm_response = await self.llm_backend.generate(prompt)

            print(f"[DEBUG] LLM response received, length: {len(llm_response)} characters")
            
            if not llm_response:
                return {"error": "LLM generation failed: No response received."}
            
            structured_result = self.extract_json(llm_response)
            
            print(f"[DEBUG] Structured result created with sections: {structured_result}")
            return structured_result
            
        except Exception as e:
            print(f"[ERROR] Reviewer validation failed: {e}")
            return {"error": f"Reviewer validation failed: {str(e)}"} 