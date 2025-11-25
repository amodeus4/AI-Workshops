"""
Export evaluation results to CSV format.
"""
import csv
import argparse
from pathlib import Path
from typing import Optional

from monitoring.models import DatabaseManager, LogRecord, CheckRecord
from monitoring.schemas import CheckName


def export_to_csv(
    output_file: str = "evaluation_results.csv",
    database_url: str = "sqlite:///monitoring.db"
) -> str:
    """
    Export evaluation results to a CSV file.
    
    Args:
        output_file: Path to the output CSV file
        database_url: Database URL
        
    Returns:
        Path to the created CSV file
    """
    db = DatabaseManager(database_url)
    session = db.get_session()
    
    try:
        logs = session.query(LogRecord).all()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Log ID',
                'User Prompt',
                'Agent Answer',
                'Timestamp',
                'instructions_follow',
                'answer_relevant',
                'answer_clear',
                'answer_citations',
                'completeness',
                'tool_call_search',
                'Overall Score',
                'Feedback Rating',
                'Comments'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in logs:
                # Build check results dictionary
                check_results = {}
                for check in log.checks:
                    check_results[check.check_name.value] = "✓" if check.passed is True else "✗" if check.passed is False else "−"
                
                # Calculate overall score
                passed_checks = sum(1 for c in log.checks if c.passed is True)
                total_checks = len(log.checks)
                overall_score = f"{passed_checks}/{total_checks}"
                
                # Get feedback if exists
                feedback_rating = ""
                feedback_comments = ""
                if log.feedback:
                    if log.feedback.rating == 1:
                        feedback_rating = "👍 Good"
                    elif log.feedback.rating == -1:
                        feedback_rating = "👎 Bad"
                    feedback_comments = log.feedback.comments or ""
                
                row = {
                    'Log ID': log.id,
                    'User Prompt': log.user_prompt,
                    'Agent Answer': log.assistant_answer[:100] + "..." if len(log.assistant_answer or "") > 100 else log.assistant_answer,
                    'Timestamp': log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "N/A",
                    'instructions_follow': check_results.get('instructions_follow', '−'),
                    'answer_relevant': check_results.get('answer_relevant', '−'),
                    'answer_clear': check_results.get('answer_clear', '−'),
                    'answer_citations': check_results.get('answer_citations', '−'),
                    'completeness': check_results.get('completeness', '−'),
                    'tool_call_search': check_results.get('tool_call_search', '−'),
                    'Overall Score': overall_score,
                    'Feedback Rating': feedback_rating,
                    'Comments': feedback_comments
                }
                
                writer.writerow(row)
        
        return output_file
    
    finally:
        session.close()


def export_detailed_csv(
    output_file: str = "evaluation_detailed.csv",
    database_url: str = "sqlite:///monitoring.db"
) -> str:
    """
    Export detailed evaluation results (one row per check).
    
    Args:
        output_file: Path to the output CSV file
        database_url: Database URL
        
    Returns:
        Path to the created CSV file
    """
    db = DatabaseManager(database_url)
    session = db.get_session()
    
    try:
        checks = session.query(CheckRecord).join(LogRecord).all()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Log ID',
                'User Prompt',
                'Check Name',
                'Passed',
                'Score',
                'Details'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for check in checks:
                log = check.log
                row = {
                    'Log ID': check.log_id,
                    'User Prompt': log.user_prompt,
                    'Check Name': check.check_name.value,
                    'Passed': "✓" if check.passed is True else "✗" if check.passed is False else "N/A",
                    'Score': f"{check.score:.3f}" if check.score is not None else "N/A",
                    'Details': check.details or ""
                }
                
                writer.writerow(row)
        
        return output_file
    
    finally:
        session.close()


def print_summary(database_url: str = "sqlite:///monitoring.db"):
    """Print a summary of evaluation results."""
    db = DatabaseManager(database_url)
    session = db.get_session()
    
    try:
        logs = session.query(LogRecord).all()
        checks = session.query(CheckRecord).all()
        
        print("\n" + "="*60)
        print("EVALUATION RESULTS SUMMARY")
        print("="*60 + "\n")
        
        print(f"Total Logs Processed: {len(logs)}")
        print(f"Total Checks Performed: {len(checks)}\n")
        
        # Summary by check type
        print("Results by Check Type:")
        print("-" * 60)
        
        check_summary = {}
        for check in checks:
            check_name = check.check_name.value
            if check_name not in check_summary:
                check_summary[check_name] = {'passed': 0, 'failed': 0, 'na': 0}
            
            if check.passed is True:
                check_summary[check_name]['passed'] += 1
            elif check.passed is False:
                check_summary[check_name]['failed'] += 1
            else:
                check_summary[check_name]['na'] += 1
        
        for check_name, stats in sorted(check_summary.items()):
            total = stats['passed'] + stats['failed'] + stats['na']
            pass_rate = (stats['passed'] / (stats['passed'] + stats['failed']) * 100) if (stats['passed'] + stats['failed']) > 0 else 0
            print(f"{check_name:25s}: ✓ {stats['passed']:2d}  ✗ {stats['failed']:2d}  − {stats['na']:2d}  ({pass_rate:5.1f}%)")
        
        print("\n" + "="*60 + "\n")
        
        # Log details
        for log in logs:
            passed_checks = sum(1 for c in log.checks if c.passed is True)
            total_checks = len(log.checks)
            print(f"Log #{log.id}: {passed_checks}/{total_checks} checks passed")
            print(f"  Prompt: {log.user_prompt}")
            print()
    
    finally:
        session.close()


def main():
    """Main entry point for export utility."""
    parser = argparse.ArgumentParser(description="Export evaluation results to CSV")
    parser.add_argument("--database-url", default="sqlite:///monitoring.db", help="Database URL")
    parser.add_argument("--output", default="evaluation_results.csv", help="Output CSV file")
    parser.add_argument("--detailed", action="store_true", help="Export detailed results (one row per check)")
    parser.add_argument("--summary", action="store_true", help="Print summary to console")
    
    args = parser.parse_args()
    
    if args.summary:
        print_summary(args.database_url)
    elif args.detailed:
        output = export_detailed_csv(args.output, args.database_url)
        print(f"✅ Detailed results exported to: {output}")
    else:
        output = export_to_csv(args.output, args.database_url)
        print(f"✅ Results exported to: {output}")


if __name__ == "__main__":
    main()
