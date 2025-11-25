"""
Streamlit dashboard for viewing logs, evaluation results, and adding feedback.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os

from monitoring.models import DatabaseManager, LogRecord, CheckRecord, UserFeedback
from monitoring.schemas import CheckName


def get_db_url():
    """Get database URL from environment or use default."""
    return os.getenv("DATABASE_URL", "sqlite:///monitoring.db")


@st.cache_resource
def get_db_manager():
    """Get cached database manager."""
    return DatabaseManager(get_db_url())


def load_logs():
    """Load all logs from the database."""
    db = get_db_manager()
    session = db.get_session()
    try:
        logs = session.query(LogRecord).order_by(LogRecord.created_at.desc()).all()
        return logs
    finally:
        session.close()


def load_log_detail(log_id: int):
    """Load detailed information about a log."""
    db = get_db_manager()
    session = db.get_session()
    try:
        log = session.query(LogRecord).filter(LogRecord.id == log_id).first()
        if log:
            # Detach from session
            checks = session.query(CheckRecord).filter(CheckRecord.log_id == log_id).all()
            feedback = session.query(UserFeedback).filter(UserFeedback.log_id == log_id).first()
            return log, checks, feedback
        return None, None, None
    finally:
        session.close()


def save_feedback(log_id: int, rating: int, comments: str, reference_answer: str):
    """Save user feedback."""
    db = get_db_manager()
    session = db.get_session()
    try:
        feedback = session.query(UserFeedback).filter(UserFeedback.log_id == log_id).first()
        if feedback:
            feedback.rating = rating
            feedback.comments = comments
            feedback.reference_answer = reference_answer
            feedback.updated_at = datetime.utcnow()
        else:
            feedback = UserFeedback(
                log_id=log_id,
                rating=rating,
                comments=comments,
                reference_answer=reference_answer
            )
            session.add(feedback)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error saving feedback: {e}")
        return False
    finally:
        session.close()


def get_check_stats():
    """Get statistics about evaluation checks."""
    db = get_db_manager()
    session = db.get_session()
    try:
        checks = session.query(CheckRecord).all()
        
        stats = {}
        for check_name in CheckName:
            check_list = [c for c in checks if c.check_name == check_name]
            if check_list:
                passed = sum(1 for c in check_list if c.passed is True)
                total = len(check_list)
                stats[check_name.value] = {"passed": passed, "total": total, "pass_rate": passed / total if total > 0 else 0}
        
        return stats
    finally:
        session.close()


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="Agent Monitoring Dashboard", layout="wide")
    
    st.title("🤖 Agent Monitoring Dashboard")
    
    # Sidebar for navigation
    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Log Details", "Statistics", "Feedback"]
    )
    
    if page == "Overview":
        st.header("Logs Overview")
        
        logs = load_logs()
        
        if not logs:
            st.info("No logs found in the database.")
        else:
            # Display as table
            log_data = []
            for log in logs:
                log_data.append({
                    "ID": log.id,
                    "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "N/A",
                    "User Prompt": log.user_prompt[:50] + "..." if len(log.user_prompt) > 50 else log.user_prompt,
                    "Has Feedback": "✓" if log.feedback else "✗",
                    "Created": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                })
            
            df = pd.DataFrame(log_data)
            st.dataframe(df, use_container_width=True)
    
    elif page == "Log Details":
        st.header("Log Details")
        
        logs = load_logs()
        if not logs:
            st.info("No logs found.")
        else:
            log_ids = {f"[{log.id}] {log.user_prompt[:40]}...": log.id for log in logs}
            selected = st.selectbox("Select a log", options=list(log_ids.keys()))
            
            if selected:
                log_id = log_ids[selected]
                log, checks, feedback = load_log_detail(log_id)
                
                if log:
                    st.subheader("User Prompt")
                    st.text(log.user_prompt)
                    
                    st.subheader("Agent Answer")
                    st.text_area("Answer:", value=log.assistant_answer or "", disabled=True, height=200)
                    
                    st.subheader("Evaluation Results")
                    if checks:
                        check_data = []
                        for check in checks:
                            status = "✓" if check.passed is True else "✗" if check.passed is False else "−"
                            check_data.append({
                                "Check": check.check_name.value,
                                "Status": status,
                                "Score": f"{check.score:.3f}" if check.score is not None else "N/A",
                                "Details": check.details or "N/A"
                            })
                        df = pd.DataFrame(check_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No checks found.")
    
    elif page == "Statistics":
        st.header("Evaluation Statistics")
        
        stats = get_check_stats()
        
        if not stats:
            st.info("No evaluation data available yet.")
        else:
            cols = st.columns(2)
            for idx, (check_name, data) in enumerate(stats.items()):
                with cols[idx % 2]:
                    st.metric(
                        check_name,
                        f"{data['pass_rate']*100:.1f}%",
                        f"{data['passed']}/{data['total']} passed"
                    )
    
    elif page == "Feedback":
        st.header("Add Feedback")
        
        logs = load_logs()
        if not logs:
            st.info("No logs available.")
        else:
            log_ids = {f"[{log.id}] {log.user_prompt[:40]}...": log.id for log in logs}
            selected = st.selectbox("Select a log for feedback", options=list(log_ids.keys()))
            
            if selected:
                log_id = log_ids[selected]
                log, _, existing_feedback = load_log_detail(log_id)
                
                if log:
                    st.text_area("User Prompt:", value=log.user_prompt, disabled=True)
                    st.text_area("Agent Answer:", value=log.assistant_answer or "", disabled=True, height=150)
                    
                    st.subheader("Your Feedback")
                    
                    rating = st.radio(
                        "Rate this response:",
                        ["👍 Good (Thumbs Up)", "👎 Bad (Thumbs Down)", "No rating"],
                        index=2 if not existing_feedback or existing_feedback.rating is None
                              else (0 if existing_feedback.rating > 0 else 1)
                    )
                    
                    rating_value = None
                    if rating == "👍 Good (Thumbs Up)":
                        rating_value = 1
                    elif rating == "👎 Bad (Thumbs Down)":
                        rating_value = -1
                    
                    comments = st.text_area(
                        "Comments:",
                        value=existing_feedback.comments if existing_feedback else "",
                        height=100
                    )
                    
                    reference_answer = st.text_area(
                        "Reference Answer (if applicable):",
                        value=existing_feedback.reference_answer if existing_feedback else "",
                        height=100
                    )
                    
                    if st.button("Save Feedback"):
                        if save_feedback(log_id, rating_value, comments, reference_answer):
                            st.success("Feedback saved!")
                            st.rerun()
                        else:
                            st.error("Failed to save feedback")


if __name__ == "__main__":
    main()
