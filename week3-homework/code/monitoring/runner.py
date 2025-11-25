"""
Log ingestion runner that reads logs from the logs/ directory and stores them in the database.
"""
import json
import os
import time
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

from .models import DatabaseManager, LogRecord, CheckRecord
from .evaluator import RuleBasedEvaluator, LLMEvaluator
from .schemas import LLMLogRecord


class LogIngestionRunner:
    """Runner that ingests logs from disk and stores them in the database."""
    
    def __init__(self, logs_dir: str = "logs", database_url: str = "sqlite:///monitoring.db", use_llm: bool = False):
        """
        Initialize the runner.
        
        Args:
            logs_dir: Directory containing log files
            database_url: SQLAlchemy database URL
            use_llm: Whether to use LLM-based evaluator
        """
        self.logs_dir = Path(logs_dir)
        self.db = DatabaseManager(database_url)
        self.db.create_tables()
        self.evaluator = LLMEvaluator() if use_llm else RuleBasedEvaluator()
        self.debug = False
    
    def process_logs(self) -> int:
        """
        Process all unprocessed log files in the logs directory.
        
        Returns:
            Number of logs processed
        """
        if not self.logs_dir.exists():
            print(f"Logs directory not found: {self.logs_dir}")
            return 0
        
        processed_count = 0
        
        for log_file in sorted(self.logs_dir.glob("agent_log_*.json")):
            # Skip already processed files (marked with leading underscore)
            if log_file.name.startswith("_"):
                continue
            
            try:
                processed = self._ingest_log_file(log_file)
                if processed:
                    processed_count += 1
                    # Mark as processed by renaming
                    new_name = log_file.parent / f"_{log_file.name}"
                    log_file.rename(new_name)
                    if self.debug:
                        print(f"Processed and archived: {log_file.name}")
            except Exception as e:
                print(f"Error processing {log_file.name}: {e}")
        
        return processed_count
    
    def _ingest_log_file(self, log_file: Path) -> bool:
        """
        Ingest a single log file.
        
        Args:
            log_file: Path to the log file
            
        Returns:
            True if successfully ingested, False otherwise
        """
        with open(log_file, "r") as f:
            data = json.load(f)
        
        # Extract key information from the log
        user_prompt = None
        assistant_answer = None
        
        interactions = data.get("interactions", [])
        for interaction in interactions:
            if interaction.get("type") == "query":
                user_prompt = interaction.get("content")
            elif interaction.get("type") == "response":
                assistant_answer = interaction.get("content")
        
        if not user_prompt:
            print(f"No user prompt found in {log_file.name}")
            return False
        
        # Parse timestamp from ISO format string
        timestamp_str = data.get("session_start")
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = None
        
        # Create LLMLogRecord
        record = LLMLogRecord(
            user_prompt=user_prompt,
            assistant_answer=assistant_answer or "",
            instructions=None,
            model=None,
            input_tokens=None,
            output_tokens=None,
            raw_json=json.dumps(data),
            timestamp=timestamp_str
        )
        
        # Store in database
        session = self.db.get_session()
        try:
            db_record = LogRecord(
                user_prompt=record.user_prompt,
                assistant_answer=record.assistant_answer,
                instructions=record.instructions,
                model=record.model,
                input_tokens=record.input_tokens,
                output_tokens=record.output_tokens,
                raw_json=record.raw_json,
                timestamp=timestamp or datetime.utcnow()
            )
            session.add(db_record)
            session.flush()  # Get the ID
            
            # Run evaluations
            checks = self.evaluator.evaluate(db_record.id, record)
            for check in checks:
                db_check = CheckRecord(
                    log_id=db_record.id,
                    check_name=check.check_name,
                    passed=check.passed,
                    score=check.score,
                    details=check.details
                )
                session.add(db_check)
            
            session.commit()
            
            if self.debug:
                print(f"✅ Ingested log with {len(checks)} checks")
            
            return True
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def watch(self, interval: int = 10):
        """
        Watch the logs directory and process new logs periodically.
        
        Args:
            interval: Interval in seconds between checks
        """
        print(f"Watching {self.logs_dir} for new logs (check every {interval}s)...")
        try:
            while True:
                processed = self.process_logs()
                if processed > 0:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processed {processed} log(s)")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopping watcher...")


def main():
    """Main entry point for the log ingestion runner."""
    parser = argparse.ArgumentParser(description="Process agent logs and store in database")
    parser.add_argument("--logs-dir", default="logs", help="Directory containing log files")
    parser.add_argument("--database-url", default="sqlite:///monitoring.db", help="Database URL")
    parser.add_argument("--watch", action="store_true", help="Watch for new logs continuously")
    parser.add_argument("--interval", type=int, default=10, help="Interval between checks when watching")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM-based evaluator")
    
    args = parser.parse_args()
    
    runner = LogIngestionRunner(
        logs_dir=args.logs_dir,
        database_url=args.database_url,
        use_llm=args.use_llm
    )
    runner.debug = args.debug
    
    if args.watch:
        runner.watch(interval=args.interval)
    else:
        processed = runner.process_logs()
        print(f"Processed {processed} log(s)")


if __name__ == "__main__":
    main()
