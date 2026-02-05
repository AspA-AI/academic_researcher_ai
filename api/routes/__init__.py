"""
Routes package for the Research Pipeline API.
Contains all route handlers organized by functionality.
"""

from . import pipeline_routes, agent_routes, quality_routes, data_routes, report_routes

__all__ = [
    "pipeline_routes",
    "agent_routes", 
    "quality_routes",
    "data_routes",
    "report_routes"
] 