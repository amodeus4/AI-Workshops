"""
Logging functionality for tracking agent interactions.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path


class AgentLogger:
    """Logger for tracking user interactions and agent responses."""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the logger.
        
        Args:
            log_dir: Directory where logs will be stored.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create a timestamp-based log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"agent_log_{timestamp}.json"
        
        self.interactions: List[Dict[str, Any]] = []
        self.session_start = datetime.now().isoformat()
    
    def log_query(self, query: str, query_time: str = None) -> None:
        """
        Log a user query.
        
        Args:
            query: The user's query string.
            query_time: Optional timestamp for the query (defaults to now).
        """
        if query_time is None:
            query_time = datetime.now().isoformat()
        
        interaction = {
            "timestamp": query_time,
            "type": "query",
            "content": query
        }
        self.interactions.append(interaction)
    
    def log_response(self, response: str, response_time: str = None) -> None:
        """
        Log an agent response.
        
        Args:
            response: The agent's response string.
            response_time: Optional timestamp for the response (defaults to now).
        """
        if response_time is None:
            response_time = datetime.now().isoformat()
        
        interaction = {
            "timestamp": response_time,
            "type": "response",
            "content": response
        }
        self.interactions.append(interaction)
    
    def log_tool_call(self, tool_name: str, tool_input: Dict[str, Any], 
                     tool_output: Any = None, call_time: str = None) -> None:
        """
        Log a tool call made by the agent.
        
        Args:
            tool_name: Name of the tool called.
            tool_input: Input parameters to the tool.
            tool_output: Output from the tool (optional).
            call_time: Optional timestamp for the call (defaults to now).
        """
        if call_time is None:
            call_time = datetime.now().isoformat()
        
        interaction = {
            "timestamp": call_time,
            "type": "tool_call",
            "tool": tool_name,
            "input": tool_input,
            "output": tool_output
        }
        self.interactions.append(interaction)
    
    def log_error(self, error_msg: str, error_type: str = "unknown", 
                 error_time: str = None) -> None:
        """
        Log an error that occurred during agent execution.
        
        Args:
            error_msg: Error message.
            error_type: Type of error.
            error_time: Optional timestamp for the error (defaults to now).
        """
        if error_time is None:
            error_time = datetime.now().isoformat()
        
        interaction = {
            "timestamp": error_time,
            "type": "error",
            "error_type": error_type,
            "message": error_msg
        }
        self.interactions.append(interaction)
    
    def save(self) -> str:
        """
        Save all logged interactions to a JSON file.
        
        Returns:
            Path to the saved log file.
        """
        log_data = {
            "session_start": self.session_start,
            "session_end": datetime.now().isoformat(),
            "interactions": self.interactions
        }
        
        with open(self.log_file, "w") as f:
            json.dump(log_data, f, indent=2)
        
        return str(self.log_file)
    
    def get_log_file(self) -> str:
        """Get the path to the current log file."""
        return str(self.log_file)
