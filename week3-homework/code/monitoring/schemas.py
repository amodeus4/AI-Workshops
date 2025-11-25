"""
Database schemas and data models for the monitoring system.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class CheckName(str, Enum):
    """Evaluation check names."""
    instructions_follow = "instructions_follow"
    instructions_avoid = "instructions_avoid"
    answer_relevant = "answer_relevant"
    answer_clear = "answer_clear"
    answer_citations = "answer_citations"
    completeness = "completeness"
    tool_call_search = "tool_call_search"


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    log_id: int
    check_name: CheckName
    passed: Optional[bool]
    score: Optional[float] = None
    details: Optional[str] = None


@dataclass
class LLMLogRecord:
    """Parsed log record from agent interaction."""
    user_prompt: str
    assistant_answer: str
    instructions: Optional[str] = None
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    raw_json: Optional[str] = None
    timestamp: Optional[str] = None
