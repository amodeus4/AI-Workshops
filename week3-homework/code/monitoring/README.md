# Agent Monitoring System

A comprehensive monitoring and evaluation system for AI agent interactions. This system processes agent logs, evaluates them against multiple criteria, stores results in a database, and provides a dashboard for review and feedback.

## Features

- **Automatic Log Ingestion**: Reads logs from the `logs/` directory
- **Multi-Criteria Evaluation**: Evaluates agent responses against criteria like:
  - Instructions following
  - Answer relevance
  - Answer clarity
  - Citations presence
  - Completeness
  - Tool usage (search calls)
- **LLM-based Evaluator**: Uses pydantic-ai for intelligent evaluation
- **Database Storage**: SQLAlchemy-based ORM supporting SQLite, PostgreSQL, and other databases
- **Streamlit Dashboard**: View logs, evaluation results, and manage feedback
- **User Feedback**: Rate responses (thumbs up/down) and add comments
- **Extensible Architecture**: Easy to swap components (storage, evaluator, log source)

## Project Structure

```
monitoring/
├── __init__.py
├── schemas.py          # Data schemas and enums
├── evaluator.py        # Rule-based and LLM-based evaluators
├── models.py           # SQLAlchemy database models
├── runner.py           # Log ingestion runner
└── app.py              # Streamlit dashboard
```

## Installation

1. Install dependencies:
```bash
pip install sqlalchemy streamlit pydantic-ai
```

2. For PostgreSQL support:
```bash
pip install psycopg2-binary
```

## Quick Start (SQLite)

### Process existing logs:
```bash
python -m monitoring.runner --logs-dir logs --database-url sqlite:///monitoring.db
```

### Watch for new logs (continuous mode):
```bash
python -m monitoring.runner --logs-dir logs --database-url sqlite:///monitoring.db --watch --interval 10
```

### Start the Streamlit dashboard:
```bash
PYTHONPATH='.' streamlit run monitoring/app.py
```

## PostgreSQL Setup

### 1. Start PostgreSQL with Docker Compose:
```bash
docker-compose up postgres
```

### 2. Run the log ingestion runner:
```bash
export DATABASE_URL=postgresql://monitoring:monitoring@localhost:5432/monitoring
python -m monitoring.runner --logs-dir logs --watch --debug
```

### 3. Start the Streamlit dashboard:
```bash
export DATABASE_URL=postgresql://monitoring:monitoring@localhost:5432/monitoring
PYTHONPATH='.' streamlit run monitoring/app.py
```

## Usage

### Log Ingestion Runner

```bash
# Process all unprocessed logs once
python -m monitoring.runner

# Watch for new logs continuously
python -m monitoring.runner --watch

# Use LLM-based evaluator instead of rules
python -m monitoring.runner --use-llm

# Enable debug output
python -m monitoring.runner --debug

# Use PostgreSQL
export DATABASE_URL=postgresql://user:password@localhost:5432/dbname
python -m monitoring.runner
```

### Streamlit Dashboard

The dashboard provides:

- **Overview**: View all logs in a table
- **Log Details**: Inspect individual logs with evaluation results
- **Statistics**: View aggregate statistics on check pass rates
- **Feedback**: Add and manage user feedback for logs

## Database Schema

### LogRecord
- `id`: Primary key
- `user_prompt`: The original user query
- `assistant_answer`: The agent's response
- `instructions`: Any special instructions given to the agent
- `model`: Model name used
- `input_tokens`, `output_tokens`: Token usage
- `raw_json`: Complete raw log data
- `timestamp`: When the interaction occurred

### CheckRecord
- `id`: Primary key
- `log_id`: Foreign key to LogRecord
- `check_name`: Type of check (from CheckName enum)
- `passed`: Boolean result (True/False/None)
- `score`: Optional numeric score
- `details`: Human-readable explanation

### UserFeedback
- `id`: Primary key
- `log_id`: Foreign key to LogRecord (unique)
- `rating`: 1 (thumbs up), -1 (thumbs down), or None
- `comments`: User comments
- `reference_answer`: Optional correct/expected answer

## Evaluation Criteria

The system evaluates responses on:

1. **instructions_follow**: Does the answer follow special instructions?
2. **answer_relevant**: Is the answer relevant to the user's question?
3. **answer_clear**: Is the answer clearly written and well-structured?
4. **answer_citations**: Does the answer include citations or references?
5. **completeness**: Is the answer comprehensive and complete?
6. **tool_call_search**: Did the agent use search tools appropriately?

## Extending the System

### Custom Evaluator

Create a new evaluator class:

```python
from monitoring.evaluator import Evaluator
from monitoring.schemas import LLMLogRecord, CheckResult

class MyCustomEvaluator(Evaluator):
    def evaluate(self, log_id: int, record: LLMLogRecord) -> List[CheckResult]:
        # Your evaluation logic here
        return checks
```

### Different Storage Backend

Modify `DatabaseManager` to support any SQLAlchemy-compatible database by changing the `database_url`.

### Custom Log Sources

Modify `LogIngestionRunner._ingest_log_file()` to read from different sources (S3, Kafka, etc.).

## Configuration

Environment variables:
- `DATABASE_URL`: Database connection string (default: `sqlite:///monitoring.db`)

## Performance Notes

- SQLite: Suitable for development and small deployments
- PostgreSQL: Recommended for production use with multiple concurrent users
- The runner processes logs asynchronously and can watch multiple directories

## Troubleshooting

### Database connection errors
Ensure `DATABASE_URL` is properly set and the database is accessible.

### Streamlit not finding the module
Make sure to set `PYTHONPATH='.'` when running the app.

### Logs not being processed
Check that log files follow the expected format (JSON with `interactions` list).

## License

MIT
