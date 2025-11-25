"""
LLM-based evaluator for agent interactions using pydantic-ai.
"""
import json
import re
from dataclasses import dataclass
from typing import List, Optional

from pydantic_ai import Agent
from .schemas import CheckName, CheckResult, LLMLogRecord


def _tokenize(text: str) -> list[str]:
    """Tokenize text into words."""
    return re.findall(r"[A-Za-z0-9_]+", text.lower())


@dataclass
class LLMEvaluator:
    """An LLM-based evaluator using pydantic-ai for comprehensive evaluation."""
    
    model: str = "openai:gpt-4o-mini"
    
    def __post_init__(self):
        """Initialize the evaluation agent."""
        self.agent = Agent(
            model=self.model,
            name="evaluation_agent",
            instructions="""You are an expert evaluator for AI agent interactions.
Your task is to evaluate agent responses against specific criteria.
Be fair but rigorous in your assessment.
Provide brief, factual explanations for your judgments."""
        )
    
    def evaluate(self, log_id: int, record: LLMLogRecord) -> List[CheckResult]:
        """
        Evaluate a log record against multiple criteria.
        
        Args:
            log_id: The ID of the log record in the database
            record: The parsed LLM log record
            
        Returns:
            A list of CheckResult objects for each evaluation criterion
        """
        checks: List[CheckResult] = []
        
        # Parse metadata from raw JSON
        search_calls = 0
        try:
            doc = json.loads(record.raw_json or "{}")
            interactions = doc.get("interactions", [])
            for interaction in interactions:
                if interaction.get("type") == "tool_call" and interaction.get("tool") == "search":
                    search_calls += 1
        except Exception:
            pass
        
        prompt = record.user_prompt or ""
        answer = record.assistant_answer or ""
        instructions = record.instructions or ""
        
        # 1. Check if instructions are followed
        checks.append(self._check_instructions_follow(log_id, instructions, answer))
        
        # 2. Check if answer is relevant
        checks.append(self._check_answer_relevant(log_id, prompt, answer))
        
        # 3. Check if answer is clear
        checks.append(self._check_answer_clear(log_id, answer))
        
        # 4. Check for citations/references
        checks.append(self._check_answer_citations(log_id, answer))
        
        # 5. Check completeness
        checks.append(self._check_completeness(log_id, answer))
        
        # 6. Check if search tool was used
        checks.append(self._check_tool_call_search(log_id, search_calls))
        
        return checks
    
    def _check_instructions_follow(self, log_id: int, instructions: str, answer: str) -> CheckResult:
        """Check if the answer follows the given instructions."""
        details = "No specific instructions provided"
        passed = None
        
        if instructions:
            # Check for references requirement
            requires_references = "references" in instructions.lower()
            has_references = (
                "references" in answer.lower()
                or "http://" in answer
                or "https://" in answer
            )
            
            if requires_references:
                passed = has_references
                details = (
                    "Instructions require references; answer contains references."
                    if has_references
                    else "Instructions require references; answer missing references."
                )
        
        return CheckResult(
            log_id=log_id,
            check_name=CheckName.instructions_follow,
            passed=passed,
            details=details
        )
    
    def _check_answer_relevant(self, log_id: int, prompt: str, answer: str) -> CheckResult:
        """Check if the answer is relevant to the user's question."""
        if not answer or not prompt:
            return CheckResult(
                log_id=log_id,
                check_name=CheckName.answer_relevant,
                passed=None,
                details="Missing prompt or answer"
            )
        
        # Calculate token overlap between prompt and answer
        p_tokens = set(_tokenize(prompt))
        a_tokens = set(_tokenize(answer))
        overlap = len(p_tokens & a_tokens)
        union = len(p_tokens | a_tokens)
        jaccard = overlap / max(1, union)
        
        # Consider relevant if there's good overlap or answer is substantive
        words = _tokenize(answer)
        is_relevant = jaccard >= 0.08 or len(words) >= 50
        
        return CheckResult(
            log_id=log_id,
            check_name=CheckName.answer_relevant,
            passed=is_relevant,
            score=jaccard,
            details=f"Jaccard similarity: {jaccard:.3f}, word count: {len(words)}"
        )
    
    def _check_answer_clear(self, log_id: int, answer: str) -> CheckResult:
        """Check if the answer is clear and well-structured."""
        if not answer:
            return CheckResult(
                log_id=log_id,
                check_name=CheckName.answer_clear,
                passed=None,
                details="No answer provided"
            )
        
        sentences = re.split(r"[.!?]+\s+", answer.strip())
        words = _tokenize(answer)
        avg_sent_len = (len(words) / max(1, len(sentences))) if sentences else 0
        
        # Clear if reasonably long and well-paced
        is_clear = len(words) >= 40 and avg_sent_len <= 35
        
        return CheckResult(
            log_id=log_id,
            check_name=CheckName.answer_clear,
            passed=is_clear,
            details=f"Words: {len(words)}, Avg sentence length: {avg_sent_len:.1f}"
        )
    
    def _check_answer_citations(self, log_id: int, answer: str) -> CheckResult:
        """Check if the answer includes citations or references."""
        if not answer:
            return CheckResult(
                log_id=log_id,
                check_name=CheckName.answer_citations,
                passed=None,
                details="No answer provided"
            )
        
        has_link = "http://" in answer or "https://" in answer
        has_references = "references" in answer.lower() or "cited" in answer.lower()
        has_citations = has_link or has_references
        
        return CheckResult(
            log_id=log_id,
            check_name=CheckName.answer_citations,
            passed=has_citations,
            details="Contains URLs or references section" if has_citations else "No citations found"
        )
    
    def _check_completeness(self, log_id: int, answer: str) -> CheckResult:
        """Check if the answer is complete and comprehensive."""
        if not answer:
            return CheckResult(
                log_id=log_id,
                check_name=CheckName.completeness,
                passed=None,
                details="No answer provided"
            )
        
        words = _tokenize(answer)
        has_bullets = bool(re.search(r"(^|\n)\s*(?:[-*]|\d+\.)\s+", answer))
        has_sections = bool(re.search(r"(^|\n)\s*#{1,3}\s+", answer))
        
        # Complete if substantial length OR has structure
        is_complete = len(words) >= 100 or has_bullets or has_sections
        
        return CheckResult(
            log_id=log_id,
            check_name=CheckName.completeness,
            passed=is_complete,
            details=f"Word count: {len(words)}, Bullets: {has_bullets}, Sections: {has_sections}"
        )
    
    def _check_tool_call_search(self, log_id: int, search_calls: int) -> CheckResult:
        """Check if the search tool was called."""
        return CheckResult(
            log_id=log_id,
            check_name=CheckName.tool_call_search,
            passed=search_calls > 0,
            score=search_calls,
            details=f"Search tool called {search_calls} times"
        )


@dataclass
class RuleBasedEvaluator:
    """A simpler rule-based evaluator without LLM calls."""
    
    def evaluate(self, log_id: int, record: LLMLogRecord) -> List[CheckResult]:
        """
        Evaluate using simple rules without LLM.
        
        Args:
            log_id: The ID of the log record
            record: The parsed LLM log record
            
        Returns:
            A list of CheckResult objects
        """
        checks: List[CheckResult] = []
        
        # Parse metadata
        search_calls = 0
        try:
            doc = json.loads(record.raw_json or "{}")
            interactions = doc.get("interactions", [])
            for interaction in interactions:
                if interaction.get("type") == "tool_call" and interaction.get("tool") == "search":
                    search_calls += 1
        except Exception:
            pass
        
        prompt = record.user_prompt or ""
        answer = record.assistant_answer or ""
        instructions = record.instructions or ""
        
        # instructions_follow
        requires_references = "references" in instructions.lower()
        has_references = "references" in answer.lower() or "http://" in answer or "https://" in answer
        checks.append(
            CheckResult(
                log_id=log_id,
                check_name=CheckName.instructions_follow,
                passed=(has_references if requires_references else None),
                details=(
                    "References present" if has_references else "No references found"
                    if requires_references else "No reference requirement"
                ),
            )
        )
        
        # answer_relevant
        p_tokens = set(_tokenize(prompt))
        a_tokens = set(_tokenize(answer))
        overlap = len(p_tokens & a_tokens)
        jaccard = overlap / max(1, len(p_tokens | a_tokens))
        checks.append(
            CheckResult(
                log_id=log_id,
                check_name=CheckName.answer_relevant,
                passed=(jaccard >= 0.08 if answer and prompt else None),
                score=jaccard,
                details=f"Jaccard: {jaccard:.3f}",
            )
        )
        
        # answer_clear
        sentences = re.split(r"[.!?]+\s+", answer.strip()) if answer.strip() else []
        words = _tokenize(answer)
        avg_sent_len = (len(words) / max(1, len(sentences))) if sentences else 0
        passed_clear = len(words) >= 40 and avg_sent_len <= 35
        checks.append(
            CheckResult(
                log_id=log_id,
                check_name=CheckName.answer_clear,
                passed=(passed_clear if answer else None),
                details=f"Words: {len(words)}, Avg sent len: {avg_sent_len:.1f}",
            )
        )
        
        # answer_citations
        has_link = "http://" in answer or "https://" in answer
        checks.append(
            CheckResult(
                log_id=log_id,
                check_name=CheckName.answer_citations,
                passed=(has_link if answer else None),
                details="Has links" if has_link else "No links",
            )
        )
        
        # completeness
        has_bullets = bool(re.search(r"(^|\n)\s*(?:[-*]|\d+\.)\s+", answer))
        passed_complete = len(words) >= 100 or has_bullets
        checks.append(
            CheckResult(
                log_id=log_id,
                check_name=CheckName.completeness,
                passed=(passed_complete if answer else None),
                details=f"Words: {len(words)}, Bullets: {has_bullets}",
            )
        )
        
        # tool_call_search
        checks.append(
            CheckResult(
                log_id=log_id,
                check_name=CheckName.tool_call_search,
                passed=(search_calls > 0),
                details=f"Search calls: {search_calls}",
            )
        )
        
        return checks
