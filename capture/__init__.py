"""
capture/__init__.py

Behaviour capture pipeline.
WHAT (Playwright Trace) → WHY (MCP) → HOW (Windsurf)
"""

from capture.trace_recorder import TraceRecorder
from capture.mcp_analyser import MCPAnalyser, MCPAnalysis
from capture.windsurf_exporter import WindsurfExporter
from capture.ci_failure_capture import CIFailureCapture

__all__ = [
    "TraceRecorder",
    "MCPAnalyser",
    "MCPAnalysis",
    "WindsurfExporter",
    "CIFailureCapture",
]