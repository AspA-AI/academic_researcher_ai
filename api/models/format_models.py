"""
Format-specific data models for report transformation.
Defines the expected JSON structures for each output format.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# PPTX Format Models
class PPTXSlide(BaseModel):
    """Single slide in a PowerPoint presentation."""
    slideNumber: int = Field(..., description="Slide number in sequence")
    slideType: Literal["title", "content", "theme", "conclusion", "section_header"] = Field(
        ..., description="Type of slide"
    )
    title: str = Field(..., description="Slide title", max_length=100)
    content: List[str] = Field(..., description="Bullet points or content items")
    notes: Optional[str] = Field(None, description="Optional speaker notes")


class PPTXStructure(BaseModel):
    """Complete PowerPoint slide deck structure."""
    slides: List[PPTXSlide] = Field(..., description="List of slides")


# HTML Format Models
class HTMLSubsection(BaseModel):
    """HTML subsection with nested structure."""
    level: int = Field(..., description="Heading level (2, 3, etc.)", ge=2, le=6)
    heading: str = Field(..., description="Subsection heading")
    paragraphs: List[str] = Field(..., description="Paragraph content")
    subsections: List["HTMLSubsection"] = Field(default_factory=list)


class HTMLSection(BaseModel):
    """HTML section with heading and content."""
    level: int = Field(1, description="Heading level", ge=1, le=6)
    heading: str = Field(..., description="Section heading")
    paragraphs: List[str] = Field(..., description="Paragraph content")
    subsections: List[HTMLSubsection] = Field(default_factory=list)


class HTMLStructure(BaseModel):
    """Complete HTML document structure."""
    sections: List[HTMLSection] = Field(..., description="Document sections")


# DOCX Format Models
class DOCXSubsection(BaseModel):
    """DOCX subsection."""
    heading: str = Field(..., description="Subsection heading")
    level: int = Field(..., description="Heading level", ge=2, le=6)
    content: str = Field(..., description="Subsection content")
    subsections: List["DOCXSubsection"] = Field(default_factory=list)


class DOCXSection(BaseModel):
    """DOCX section."""
    heading: str = Field(..., description="Section heading")
    level: int = Field(1, description="Heading level", ge=1, le=6)
    content: str = Field(..., description="Section content")
    subsections: List[DOCXSubsection] = Field(default_factory=list)


class DOCXStructure(BaseModel):
    """Complete DOCX document structure."""
    title: str = Field(..., description="Document title")
    sections: List[DOCXSection] = Field(..., description="Document sections")


# PDF Format Model (uses canonical structure)
class PDFStructure(BaseModel):
    """PDF structure (uses canonical report format)."""
    title: str
    research_domain: Optional[str] = None
    generated_at: Optional[str] = None
    sections: Dict[str, Any]


# Format Transformation Request/Response
class FormatTransformRequest(BaseModel):
    """Request to transform report to specific format."""
    report: Dict[str, Any] = Field(..., description="Canonical report JSON")
    targetFormat: Literal["pptx", "html", "pdf", "docx"] = Field(
        ..., description="Target output format"
    )


class FormatTransformResponse(BaseModel):
    """Response from format transformation."""
    success: bool = Field(..., description="Whether transformation succeeded")
    format: str = Field(..., description="Target format")
    data: Dict[str, Any] = Field(..., description="Format-specific structure")
    error: Optional[str] = Field(None, description="Error message if failed")

