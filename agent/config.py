"""
Fraud Detection Agent - Configuration
=====================================

Central configuration file for the fraud investigation agent.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys - Try Streamlit secrets first, then environment variables
def get_api_key():
    """Get API key from Streamlit secrets or environment."""
    try:
        import streamlit as st
        return st.secrets.get("GOOGLE_API_KEY")
    except:
        return os.getenv("GOOGLE_API_KEY")

GOOGLE_API_KEY = get_api_key()

# Project Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
VECTOR_DB_DIR = BASE_DIR / "vector_db"

# Model Configuration
GEMINI_MODEL = "gemini-2.5-pro"
MAX_INVESTIGATION_TURNS = 10

# Confidence Thresholds
CONFIDENCE_THRESHOLDS = {
    "ESCALATE": 0.85,
    "VERIFY": 0.60,
    "MONITOR": 0.40,
    "DISMISS": 0.00
}

# Dashboard Configuration
PAGE_TITLE = "Fraud Detection Agent"
PAGE_ICON = "🔍"
LAYOUT = "wide"

# System Prompt for the Agent
SYSTEM_PROMPT = """You are an expert fraud investigation agent working for a financial institution's fraud prevention team.

Your role is to:
1. Analyze suspicious transactions using available tools
2. Gather evidence from multiple data sources
3. Identify patterns and risk indicators
4. Make informed recommendations

Investigation Process:
- Start by examining the flagged transaction details
- Check customer KYC profile and risk history
- Review security events (SIEM logs) for suspicious activity
- Search for similar past fraud cases
- Match patterns to known fraud schemes
- Consider timing, amounts, devices, and locations

Available Tools:
- query_similar_cases: Find past investigations with similar patterns
- search_fraud_patterns: Match indicators to known fraud types
- fetch_kyc_profile: Get customer background and risk score
- query_siem_events: Check security logs for suspicious activity
- get_transaction_details: Examine the flagged transaction
- get_transaction_history: Analyze transaction patterns over time

Final Recommendation Options:
- ESCALATE: Strong evidence of fraud, requires immediate action
- VERIFY: Suspicious but needs human verification
- MONITOR: Minor red flags, continue monitoring
- DISMISS: Likely legitimate, low fraud risk

Always provide:
1. Clear recommendation (ESCALATE/VERIFY/MONITOR/DISMISS)
2. Confidence score (0.0 to 1.0)
3. Key evidence points
4. Reasoning for your decision

Be thorough but efficient. Use tools strategically - don't call the same tool repeatedly with similar inputs."""

# Investigation Prompt Template
INVESTIGATION_PROMPT_TEMPLATE = """
NEW FRAUD ALERT RECEIVED
========================

**Transaction ID:** {transaction_id}
**Alert Description:** {alert_description}
**Initial ML Risk Score:** {initial_risk_score}
**Investigation Date:** {investigation_date}

**Your Task:**
Conduct a thorough fraud investigation using available tools. Gather evidence, analyze patterns, and provide a clear recommendation with your confidence level.

**Investigation Steps:**
1. Get transaction details
2. Check customer KYC profile
3. Review recent security events
4. Search for similar fraud cases
5. Match to known fraud patterns
6. Analyze transaction history if needed

**Expected Output Format:**
After your investigation, provide a structured brief with:

**RECOMMENDATION:** [ESCALATE/VERIFY/MONITOR/DISMISS]
**CONFIDENCE SCORE:** [0.XX]

**KEY FINDINGS:**
- [Finding 1]
- [Finding 2]
- [Finding 3]

**EVIDENCE:**
- [Evidence point 1]
- [Evidence point 2]

**REASONING:**
[Your detailed reasoning for the recommendation]

**NEXT STEPS:**
[Suggested actions for the analyst]

Begin your investigation now.
"""

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = OUTPUTS_DIR / "agent_logs.txt"

# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_config():
    """
    Validate configuration and check required files exist.
    Returns list of warnings/errors.
    """
    issues = []
    
    # Check API key
    if not GOOGLE_API_KEY:
        issues.append("⚠️ GOOGLE_API_KEY not set. Set in .env file or environment variable.")
    
    # Check required directories
    required_dirs = [DATA_DIR, OUTPUTS_DIR, CLEANED_DIR, EMBEDDINGS_DIR]
    for directory in required_dirs:
        if not directory.exists():
            issues.append(f"⚠️ Directory not found: {directory}")
    
    # Check required data files
    required_files = [
        CLEANED_DIR / "creditcard_cleaned.parquet",
        CLEANED_DIR / "siem_logs_cleaned.parquet",
        CLEANED_DIR / "kyc_profiles_cleaned.parquet"
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            issues.append(f"⚠️ Required file not found: {file_path}")
    
    # Check ChromaDB
    if not VECTOR_DB_DIR.exists():
        issues.append(f"⚠️ ChromaDB directory not found: {VECTOR_DB_DIR}")
    
    return issues


def print_config():
    """Print current configuration for debugging."""
    print("="*80)
    print("FRAUD AGENT CONFIGURATION")
    print("="*80)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Gemini Model: {GEMINI_MODEL}")
    print(f"API Key Set: {'Yes' if GOOGLE_API_KEY else 'No'}")
    print(f"Max Turns: {MAX_INVESTIGATION_TURNS}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print("\nConfidence Thresholds:")
    for action, threshold in CONFIDENCE_THRESHOLDS.items():
        print(f"  {action}: {threshold}")
    
    # Validation
    issues = validate_config()
    if issues:
        print("\n⚠️ Configuration Issues:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Configuration validated successfully")
    
    print("="*80)


if __name__ == "__main__":
    print_config()