"""
Supervisor Prompts Package

This package contains structured prompt templates for the supervisor agent
to provide consistent, comprehensive quality assessments.
"""

from .base_prompts import BaseSupervisorPrompts
from .agent_specific_prompts import AgentSpecificPrompts
from .assessment_templates import AssessmentTemplates

__all__ = [
    "BaseSupervisorPrompts",
    "AgentSpecificPrompts", 
    "AssessmentTemplates"
] 