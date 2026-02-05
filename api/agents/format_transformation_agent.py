"""
Format Transformation Agent

Intelligently transforms canonical report JSON into format-specific structures
using LLM to ensure semantic coherence and optimal presentation.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from api.utils.llm_backends import get_llm_backend

logger = logging.getLogger(__name__)


class FormatTransformationAgent:
    """
    Transforms canonical report JSON into format-optimized structures.
    Uses LLM to intelligently restructure content while preserving meaning.
    """

    def __init__(self, llm_backend=None):
        self.llm_backend = llm_backend or get_llm_backend("openai")

    def _get_format_prompt(self, target_format: str) -> str:
        """Get format-specific prompt template."""
        
        prompts = {
            "pptx": """
You are transforming a research report into a PowerPoint presentation deck structure.

TASK: Convert the canonical report JSON into a presentation-optimized structure that tells a compelling story.

CRITICAL RULES:
1. NEVER create slides with empty content arrays - every slide MUST have at least 3-6 bullet points
2. Focus on PRESENTATION structure, not academic document structure
3. Only create a slide if it has meaningful, audience-friendly content to display
4. Each slide should have ONE clear topic/focus
5. Group semantically related content together
6. Break long sections into logical, sequential slides
7. Create engaging, concise slide titles (max 60 chars) - use action-oriented language
8. Convert paragraphs into bullet points (3-6 bullets per slide minimum)
9. Ensure smooth narrative flow between slides - tell a story
10. Focus on key insights, findings, and takeaways - not exhaustive academic detail
11. Make content accessible and engaging for a presentation audience

OUTPUT JSON STRUCTURE:
{
  "slides": [
    {
      "slideNumber": 1,
      "slideType": "title" | "overview" | "insight" | "theme" | "finding" | "conclusion",
      "title": "Clear, engaging slide title",
      "content": [
        "Bullet point 1 - MUST have content",
        "Bullet point 2 - MUST have content",
        "Bullet point 3 - MUST have content"
      ],
      "notes": "Optional speaker notes or additional context"
    }
  ]
}

SLIDE TYPES:
- "title": Title slide with report name and topic (content can be empty for title slide only)
- "overview": Overview/agenda slide summarizing what will be covered
- "insight": Key insights or important points from the research
- "theme": Theme/finding slides with bullet points
- "finding": Specific research findings or discoveries
- "conclusion": Conclusion slides with key takeaways and implications

PRESENTATION STRUCTURE (NOT academic document structure):
- Title Slide: Report title and research domain
- Overview Slide: 3-5 key points about what the presentation covers (synthesize from abstract/intro)
- Key Insights: Extract the most important insights from introduction/literature review (2-3 slides max)
- Main Findings/Themes: Each theme gets its own slide with:
  * Clear theme title
  * 4-6 bullet points from precise_definition highlighting what matters
  * Focus on implications and significance, not just description
- Discussion/Implications: 1-2 slides on what the findings mean
- Conclusion: 3-5 key takeaways and future directions

CONTENT TRANSFORMATION GUIDELINES:
- Abstract/Introduction: Synthesize into 1-2 "Overview" or "Key Insights" slides - don't create separate "Abstract" or "Introduction" slides
- Literature Review: Extract only the most relevant studies/findings (2-3 slides max) - focus on what's important, not exhaustive review
- Methodology: Only include if it's critical for understanding - usually skip or make it 1 brief slide
- Findings/Themes: This is the CORE - each theme should be a compelling slide with clear insights
- Discussion: Convert to 1-2 slides on implications and significance
- Conclusion: Key takeaways, not full academic conclusion

CRITICAL: 
- DO NOT create slides titled "Abstract", "Introduction", "Literature Review", "Methodology" - these are document sections, not presentation slides
- Focus on STORY and INSIGHTS, not academic structure
- EVERY slide (except title) MUST have at least 3 bullet points in the content array
- If content is too academic/detailed, synthesize it into presentation-friendly insights
- Each bullet should be 1-2 sentences, clear, concise, and audience-friendly
- Prioritize what matters most - don't try to include everything
""",

            "html": """
You are transforming a research report into an HTML-optimized structure.

TASK: Convert the canonical report JSON into an HTML-friendly structure with semantic markup.

RULES:
1. Organize content into logical sections and subsections
2. Use proper heading hierarchy (h1, h2, h3)
3. Break long paragraphs into shorter, readable chunks
4. Add semantic structure for better HTML rendering
5. Preserve all content - don't omit information
6. Group related concepts together

OUTPUT JSON STRUCTURE:
{
  "sections": [
    {
      "level": 1,
      "heading": "Main Section Title",
      "paragraphs": [
        "First paragraph content",
        "Second paragraph content"
      ],
      "subsections": [
        {
          "level": 2,
          "heading": "Subsection Title",
          "paragraphs": ["Content..."],
          "subsections": []
        }
      ]
    }
  ]
}

IMPORTANT:
- Use proper heading hierarchy
- Break content into digestible paragraphs
- Maintain semantic structure
- Preserve all information
""",

            "pdf": """
You are transforming a research report for PDF output.

TASK: The canonical structure is already PDF-optimized, but ensure it's well-formatted.

RULES:
1. Maintain the existing structure (it's already PDF-friendly)
2. Ensure proper section organization
3. Verify content completeness
4. Optimize paragraph lengths for readability

OUTPUT JSON STRUCTURE:
{
  "title": "Report Title",
  "research_domain": "Domain",
  "generated_at": "ISO date",
  "sections": {
    "abstract": "Full abstract text",
    "introduction": "Full introduction text",
    "literature_review": "Full literature review text",
    "methodology": "Full methodology text",
    "findings": [
      {
        "theme_name": "Theme name",
        "precise_definition": "Full definition text"
      }
    ],
    "discussion": "Full discussion text",
    "conclusion": "Full conclusion text",
    "references": []
  }
}

IMPORTANT:
- Keep full paragraphs (PDF can handle long text)
- Maintain academic structure
- Preserve all details
""",

            "docx": """
You are transforming a research report for Word document output.

TASK: Convert to DOCX-optimized structure with proper heading hierarchy.

RULES:
1. Use Word-friendly heading structure
2. Organize content into sections with proper headings
3. Maintain full paragraphs (Word handles long text well)
4. Preserve all content

OUTPUT JSON STRUCTURE:
{
  "title": "Report Title",
  "sections": [
    {
      "heading": "Abstract",
      "level": 1,
      "content": "Full abstract text"
    },
    {
      "heading": "Introduction",
      "level": 1,
      "content": "Full introduction text"
    },
    {
      "heading": "Findings",
      "level": 1,
      "subsections": [
        {
          "heading": "Theme Name",
          "level": 2,
          "content": "Theme definition and details"
        }
      ]
    }
  ]
}

IMPORTANT:
- Use proper heading levels
- Maintain full content
- Structure for Word document formatting
"""
        }
        
        return prompts.get(target_format.lower(), prompts["pdf"])

    async def transform(
        self, 
        canonical_report: Dict[str, Any], 
        target_format: str
    ) -> Dict[str, Any]:
        """
        Transform canonical report into format-specific structure.
        
        Args:
            canonical_report: The canonical report JSON
            target_format: Target format ("pptx", "html", "pdf", "docx")
            
        Returns:
            Format-specific JSON structure
        """
        
        format_prompt = self._get_format_prompt(target_format)
        
        # Prepare the full prompt
        full_prompt = f"""
{format_prompt}

CANONICAL REPORT JSON:
{json.dumps(canonical_report, indent=2)}

Transform this report into the {target_format.upper()} format structure as specified above.

CRITICAL REMINDERS:
- For PPTX: Every slide (except title) MUST have at least 3 bullet points in the content array
- DO NOT create slides with empty content arrays
- Convert all text sections into bullet points
- Skip sections that have no content in the original report
- Return ONLY valid JSON matching the output structure
- Do not include any explanatory text outside the JSON
"""
        
        # Call LLM
        try:
            logger.info(f"🔄 Starting LLM transformation for format: {target_format}")
            logger.debug(f"Report title: {canonical_report.get('title', 'Unknown')}")
            
            response = await self.llm_backend.generate(
                prompt=full_prompt,
                temperature=0.3,  # Lower temperature for more consistent structure
                max_tokens=4000
            )
            
            logger.info(f"✅ LLM response received (length: {len(response) if response else 0})")
            
            # Parse JSON response
            # LLM might wrap response in markdown code blocks
            response_text = response.strip() if response else ""
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            transformed = json.loads(response_text)
            logger.info(f"✅ Successfully parsed transformed structure")
            
            # Post-process: Filter out empty slides for PPTX
            if target_format.lower() == "pptx" and "slides" in transformed:
                original_count = len(transformed["slides"])
                # Filter out slides with empty content (except title slides)
                transformed["slides"] = [
                    slide for slide in transformed["slides"]
                    if slide.get("slideType") == "title" or 
                       (isinstance(slide.get("content"), list) and len(slide.get("content", [])) > 0)
                ]
                # Renumber slides
                for idx, slide in enumerate(transformed["slides"], 1):
                    slide["slideNumber"] = idx
                
                filtered_count = len(transformed["slides"])
                if original_count != filtered_count:
                    logger.warning(f"⚠️ Filtered out {original_count - filtered_count} empty slides")
            
            return transformed
            
        except json.JSONDecodeError as e:
            # Fallback: return canonical structure if parsing fails
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.debug(f"Raw response (first 500 chars): {response_text[:500] if 'response_text' in locals() else 'No response'}")
            return {
                "error": f"Failed to parse LLM response: {str(e)}",
                "fallback": canonical_report,
                "raw_response": response_text[:500] if 'response_text' in locals() else None
            }
        except Exception as e:
            logger.error(f"❌ Transformation error: {e}", exc_info=True)
            return {
                "error": str(e),
                "fallback": canonical_report
            }

