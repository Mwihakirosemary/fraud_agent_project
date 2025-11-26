"""
Fraud Detection Agent - Tool Functions
======================================

This module provides all the tools (functions) that the fraud investigation
agent can use to gather information during its investigation.

Each tool queries a specific data source and returns structured information.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta


class FraudAgentTools:
    """
    Collection of tools for the fraud investigation agent.
    
    Each tool provides access to a different data source:
    - ChromaDB vector database (for semantic search)
    - Transaction data (creditcard.csv)
    - SIEM logs (security events)
    - KYC profiles (customer data)
    - Fraud patterns (known fraud types)
    """
    
def __init__(self):
    """
    Initialize all data sources and connections.
    """
    # Get the project root (parent of the agent folder)
    self.project_root = Path(__file__).parent.parent.resolve()
    
    # Define all paths relative to project root
    self.cleaned_dir = self.project_root / "outputs" / "cleaned"
    self.cases_dir = self.project_root / "outputs" / "cases"
    self.kyc_dir = self.project_root / "outputs" / "kyc_profiles"
    self.patterns_dir = self.project_root / "outputs" / "patterns"
    self.siem_dir = self.project_root / "outputs" / "siem_logs"
    self.chroma_dir = self.project_root / "vector_db" / "chroma"
    
    # Debug: Print paths
    print(f"📂 Project root: {self.project_root}")
    print(f"📂 Cleaned data: {self.cleaned_dir}")
    print(f"📂 ChromaDB: {self.chroma_dir}")
    
    # Verify critical paths exist
    if not self.cleaned_dir.exists():
        raise FileNotFoundError(f"Cleaned data directory not found: {self.cleaned_dir}")
    if not self.chroma_dir.exists():
        raise FileNotFoundError(f"ChromaDB directory not found: {self.chroma_dir}")
    
    # Initialize embedding model
    print("📥 Loading embedding model...")
    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Initialize ChromaDB
    print("🔧 Connecting to ChromaDB...")
    self.chroma_client = chromadb.PersistentClient(
        path=str(self.chroma_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Load collections
    try:
        self.cases_collection = self.chroma_client.get_collection("investigation_cases")
        print("✓ Loaded investigation_cases collection")
    except ValueError:
        print("⚠️ Warning: investigation_cases collection not found. Run embedding notebook first.")
        self.cases_collection = None
    
    try:
        self.patterns_collection = self.chroma_client.get_collection("fraud_patterns")
        print("✓ Loaded fraud_patterns collection")
    except ValueError:
        print("⚠️ Warning: fraud_patterns collection not found. Run embedding notebook first.")
        self.patterns_collection = None
    
    try:
        self.kyc_collection = self.chroma_client.get_collection("kyc_profiles")
        print("✓ Loaded kyc_profiles collection")
    except ValueError:
        print("⚠️ Warning: kyc_profiles collection not found. Run embedding notebook first.")
        self.kyc_collection = None
    
    # Load static datasets
    print("📊 Loading datasets...")
    try:
        self.df_transactions = pd.read_parquet(self.cleaned_dir / "creditcard_cleaned.parquet")
        print(f"✓ Loaded {len(self.df_transactions)} transactions")
    except FileNotFoundError:
        raise FileNotFoundError(f"Transaction data not found: {self.cleaned_dir / 'creditcard_cleaned.parquet'}")
    
    try:
        self.df_siem = pd.read_parquet(self.cleaned_dir / "siem_logs_cleaned.parquet")
        print(f"✓ Loaded {len(self.df_siem)} SIEM logs")
    except FileNotFoundError:
        raise FileNotFoundError(f"SIEM data not found: {self.cleaned_dir / 'siem_logs_cleaned.parquet'}")
    
    try:
        self.df_kyc = pd.read_parquet(self.cleaned_dir / "kyc_profiles_cleaned.parquet")
        print(f"✓ Loaded {len(self.df_kyc)} KYC profiles")
    except FileNotFoundError:
        raise FileNotFoundError(f"KYC data not found: {self.cleaned_dir / 'kyc_profiles_cleaned.parquet'}")
    
    print("✅ All tools initialized successfully\n")
    
    # ========================================================================
    # TOOL 1: QUERY SIMILAR CASES
    # ========================================================================
    
    def query_similar_cases(
        self, 
        description: str, 
        n_results: int = 5,
        fraud_type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find past investigation cases similar to the given description.
        
        Use this when: You want to see how similar fraud cases were handled.
        
        Args:
            description: Description of the suspicious activity
            n_results: Number of similar cases to return
            fraud_type_filter: Optional filter by fraud type
            
        Returns:
            Dictionary with similar cases and their details
            
        Example:
            >>> tools.query_similar_cases(
                    "Password reset followed by large transfer",
                    n_results=3
                )
        """
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode(description)
        
        # Build metadata filter
        where_clause = {"fraud_type": fraud_type_filter} if fraud_type_filter else None
        
        # Search ChromaDB
        results = self.cases_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        similar_cases = []
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            similarity = 1 / (1 + distance)  
            similar_cases.append({
                "rank": i + 1,
                "case_id": meta.get('case_id', 'Unknown'),
                "fraud_type": meta.get('fraud_type', 'Unknown'),
                "status": meta.get('status', 'Unknown'),
                "similarity_score": round(similarity, 3),
                "summary": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        return {
            "query": description,
            "num_results": len(similar_cases),
            "similar_cases": similar_cases
        }
    
    # ========================================================================
    # TOOL 2: SEARCH FRAUD PATTERNS
    # ========================================================================
    
    def search_fraud_patterns(
        self,
        indicators: str,
        n_results: int = 3,
        risk_level_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Match transaction indicators to known fraud patterns.
        
        Use this when: You want to identify what type of fraud this might be.
        
        Args:
            indicators: Description of observed indicators/red flags
            n_results: Number of patterns to return
            risk_level_filter: Filter by risk level (Low, Medium, High)
            
        Returns:
            Dictionary with matching fraud patterns
            
        Example:
            >>> tools.search_fraud_patterns(
                    "Multiple small transactions, different countries",
                    n_results=3
                )
        """
        # Generate embedding
        query_embedding = self.embedding_model.encode(indicators)
        
        # Build filter
        where_clause = {"risk_level": risk_level_filter} if risk_level_filter else None
        
        # Search patterns
        results = self.patterns_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        matching_patterns = []
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            similarity = 1 / (1 + distance)
            matching_patterns.append({
                "rank": i + 1,
                "pattern_name": meta.get('name', 'Unknown'),
                "risk_level": meta.get('risk_level', 'Unknown'),
                "match_score": round(similarity, 3),
                "description": doc[:300] + "..." if len(doc) > 300 else doc
            })
        
        return {
            "query": indicators,
            "num_patterns": len(matching_patterns),
            "matching_patterns": matching_patterns
        }
    
    # ========================================================================
    # TOOL 3: FETCH KYC PROFILE
    # ========================================================================
    
    def fetch_kyc_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve customer KYC profile and risk information.
        
        Use this when: You need to understand the customer's background.
        
        Args:
            user_id: Customer user ID
            
        Returns:
            Dictionary with customer profile information
            
        Example:
            >>> tools.fetch_kyc_profile("USER_12345")
        """
        # Search in KYC dataframe
        profile = self.df_kyc[self.df_kyc['user_id'] == user_id]
        
        if profile.empty:
            return {
                "found": False,
                "user_id": user_id,
                "message": "No KYC profile found for this user"
            }
        
        # Extract profile data
        profile = profile.iloc[0]
        
        return {
            "found": True,
            "user_id": user_id,
            "full_name": profile.get('full_name', 'N/A'),
            "age": int(profile.get('age', 0)),
            "country": profile.get('country', 'N/A'),
            "employment": profile.get('employment', 'N/A'),
            "account_type": profile.get('account_type', 'N/A'),
            "risk_score": int(profile.get('risk_score', 0)),
            "risk_level": profile.get('risk_level', 'N/A'),
            "avg_monthly_transactions": int(profile.get('avg_monthly_txn', 0)),
            "device_count": int(profile.get('device_count', 0)),
            "account_age_days": int(profile.get('account_age_days', 0)) if 'account_age_days' in profile else None,
            "profile_summary": profile.get('profile_text', 'No summary available')
        }
    
    # ========================================================================
    # TOOL 4: QUERY SIEM EVENTS
    # ========================================================================
    
    def query_siem_events(
        self,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        event_type: Optional[str] = None,
        hours_back: int = 24,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search security event logs (SIEM) for user/device activity.
        
        Use this when: You want to see recent security events.
        
        Args:
            user_id: Filter by user ID
            device_id: Filter by device ID
            event_type: Filter by event type
            hours_back: How many hours of history to search
            limit: Maximum number of events to return
            
        Returns:
            Dictionary with matching security events
            
        Example:
            >>> tools.query_siem_events(
                    user_id="USER_12345",
                    hours_back=48
                )
        """
        # Start with full dataset
        df = self.df_siem.copy()
        
        # Apply filters
        if user_id:
            df = df[df['user_id'] == user_id]
        
        if device_id:
            df = df[df['device_id'] == device_id]
        
        if event_type:
            df = df[df['event_type'] == event_type]
        
        # Time filter (if timestamp column exists)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            df = df[df['timestamp'] >= cutoff_time]
        
        # Sort by most recent
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)
        
        # Limit results
        df = df.head(limit)
        
        # Format events
        events = []
        for _, row in df.iterrows():
            events.append({
                "event_id": row.get('event_id', 'N/A'),
                "timestamp": str(row.get('timestamp', 'N/A')),
                "event_type": row.get('event_type', 'N/A'),
                "severity": row.get('severity', 'N/A'),
                "user_id": row.get('user_id', 'N/A'),
                "device_id": row.get('device_id', 'N/A'),
                "ip_address": row.get('ip_address', 'N/A'),
                "country": row.get('country', row.get('geo_country', 'N/A')),
                "details": row.get('details_reason', 'No details available')
            })
        
        # Calculate statistics
        high_risk_count = df['is_high_risk'].sum() if 'is_high_risk' in df.columns else 0
        suspicious_count = df['is_suspicious'].sum() if 'is_suspicious' in df.columns else 0
        
        return {
            "filters_applied": {
                "user_id": user_id,
                "device_id": device_id,
                "event_type": event_type,
                "hours_back": hours_back
            },
            "total_events_found": len(df),
            "high_risk_events": int(high_risk_count),
            "suspicious_events": int(suspicious_count),
            "events": events
        }
    
    # ========================================================================
    # TOOL 5: GET TRANSACTION DETAILS
    # ========================================================================
    
    def get_transaction_details(self, transaction_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific transaction.
        
        Use this when: You need full details about the flagged transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Dictionary with transaction details
            
        Example:
            >>> tools.get_transaction_details("TXN_00012345")
        """
        # Search transaction
        txn = self.df_transactions[self.df_transactions['TransactionID'] == transaction_id]
        
        if txn.empty:
            return {
                "found": False,
                "transaction_id": transaction_id,
                "message": "Transaction not found"
            }
        
        txn = txn.iloc[0]
        
        return {
            "found": True,
            "transaction_id": transaction_id,
            "amount": float(txn.get('Amount', 0)),
            "timestamp": str(txn.get('timestamp', 'N/A')),
            "hour": int(txn.get('hour', 0)),
            "day_of_week": int(txn.get('day_of_week', 0)),
            "is_weekend": bool(txn.get('is_weekend', False)),
            "is_night": bool(txn.get('is_night', False)),
            "amount_log": float(txn.get('amount_log', 0)),
            "amount_zscore": float(txn.get('amount_zscore', 0)),
            "is_fraud": bool(txn.get('Class', 0)),
            "pca_features": {f"V{i}": float(txn.get(f"V{i}", 0)) for i in range(1, 29)}
        }
    
    # ========================================================================
    # TOOL 6: GET TRANSACTION HISTORY
    # ========================================================================
    
    def get_transaction_history(
        self,
        user_id: Optional[str] = None,
        days_back: int = 30,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get transaction history for analysis of patterns.
        
        Use this when: You want to see a user's transaction behavior over time.
        
        Args:
            user_id: User ID (optional - for future linking)
            days_back: Number of days of history
            limit: Maximum transactions to return
            
        Returns:
            Dictionary with transaction history and statistics
            
        Example:
            >>> tools.get_transaction_history(days_back=30, limit=100)
        """
        # For demo purposes, we'll return random sample
        # In production, we would filter by user_id using a mapping table
        
        df = self.df_transactions.copy()
        
        # Time filter
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = datetime.now() - timedelta(days=days_back)
            df = df[df['timestamp'] >= cutoff]
        
        # Limit and sample
        df = df.head(limit)
        
        # Calculate statistics
        stats = {
            "total_transactions": len(df),
            "total_amount": float(df['Amount'].sum()) if 'Amount' in df.columns else 0,
            "avg_amount": float(df['Amount'].mean()) if 'Amount' in df.columns else 0,
            "fraud_count": int(df['Class'].sum()) if 'Class' in df.columns else 0,
            "fraud_rate": float(df['Class'].mean() * 100) if 'Class' in df.columns else 0,
            "night_transactions": int(df['is_night'].sum()) if 'is_night' in df.columns else 0,
            "weekend_transactions": int(df['is_weekend'].sum()) if 'is_weekend' in df.columns else 0
        }
        
        return {
            "user_id": user_id or "N/A",
            "days_searched": days_back,
            "statistics": stats,
            "sample_transactions": [
                {
                    "transaction_id": row.get('TransactionID', 'N/A'),
                    "amount": float(row.get('Amount', 0)),
                    "timestamp": str(row.get('timestamp', 'N/A')),
                    "is_fraud": bool(row.get('Class', 0))
                }
                for _, row in df.head(10).iterrows()
            ]
        }
    
    # ========================================================================
    # TOOL 7: SEARCH SIMILAR KYC PROFILES
    # ========================================================================
    
    def search_similar_kyc_profiles(
        self,
        description: str,
        n_results: int = 5,
        risk_level_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find customers with similar profiles (semantic search).
        
        Use this when: You want to see if other similar customers had fraud.
        
        Args:
            description: Description of customer characteristics
            n_results: Number of similar profiles to return
            risk_level_filter: Filter by risk level
            
        Returns:
            Dictionary with similar customer profiles
            
        Example:
            >>> tools.search_similar_kyc_profiles(
                    "High risk customer with multiple devices in Nigeria",
                    n_results=5
                )
        """
        # Generate embedding
        query_embedding = self.embedding_model.encode(description)
        
        # Build filter
        where_clause = {"risk_level": risk_level_filter} if risk_level_filter else None
        
        # Search
        results = self.kyc_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        similar_profiles = []
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            similarity = 1 / (1 + distance)
            similar_profiles.append({
                "rank": i + 1,
                "user_id": meta.get('user_id', 'Unknown'),
                "risk_score": int(meta.get('risk_score', 0)),
                "risk_level": meta.get('risk_level', 'Unknown'),
                "country": meta.get('country', 'Unknown'),
                "similarity_score": round(similarity, 3),
                "profile_summary": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        return {
            "query": description,
            "num_results": len(similar_profiles),
            "similar_profiles": similar_profiles
        }


# ============================================================================
# HELPER FUNCTION: Get tool descriptions for the agent
# ============================================================================

def get_tool_descriptions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "query_similar_cases",
            "description": "Search for past investigation cases similar to a given description. Returns cases with fraud types, outcomes, and similarity scores. Use this to learn from how similar fraud was investigated before.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the suspicious activity or fraud scenario"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of similar cases to return (default 5)",
                        "default": 5
                    },
                    "fraud_type_filter": {
                        "type": "string",
                        "description": "Optional: filter by specific fraud type"
                    }
                },
                "required": ["description"]
            }
        },
        {
            "name": "search_fraud_patterns",
            "description": "Match observed indicators to known fraud patterns. Returns pattern names, risk levels, and descriptions. Use this to identify what type of fraud scheme this might be.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "indicators": {
                        "type": "string",
                        "description": "Description of observed red flags or suspicious indicators"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of patterns to return (default 3)",
                        "default": 3
                    }
                },
                "required": ["indicators"]
            }
        },
        {
            "name": "fetch_kyc_profile",
            "description": "Retrieve customer KYC profile including name, age, country, employment, risk score, and account details. Use this to understand the customer's background and risk profile.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Customer user ID"
                    }
                },
                "required": ["user_id"]
            }
        },
        {
            "name": "query_siem_events",
            "description": "Search security event logs for user or device activity. Returns login events, password resets, suspicious locations, etc. Use this to check for security red flags.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Filter by user ID"
                    },
                    "device_id": {
                        "type": "string",
                        "description": "Filter by device ID"
                    },
                    "event_type": {
                        "type": "string",
                        "description": "Filter by event type (e.g., 'login_failure', 'suspicious_location')"
                    },
                    "hours_back": {
                        "type": "integer",
                        "description": "Hours of history to search (default 24)",
                        "default": 24
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_transaction_details",
            "description": "Get detailed information about a specific transaction including amount, timestamp, PCA features, and fraud label. Use this to examine the flagged transaction.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Transaction ID to lookup"
                    }
                },
                "required": ["transaction_id"]
            }
        },
        {
            "name": "get_transaction_history",
            "description": "Get transaction history and statistics over a time period. Use this to analyze transaction patterns and behavior over time.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (optional)"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days of history (default 30)",
                        "default": 30
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum transactions to return (default 50)",
                        "default": 50
                    }
                },
                "required": []
            }
        }
    ]


if __name__ == "__main__":
    # Test the tools
    print("="*80)
    print("TESTING FRAUD AGENT TOOLS")
    print("="*80 + "\n")
    
    tools = FraudAgentTools()
    
    # Test 1: Query similar cases
    print("\n🔍 Test 1: Query Similar Cases")
    result = tools.query_similar_cases("Password reset followed by unusual transfer")
    print(json.dumps(result, indent=2))
    
    # Test 2: Search fraud patterns
    print("\n🎯 Test 2: Search Fraud Patterns")
    result = tools.search_fraud_patterns("Multiple small transactions in short time")
    print(json.dumps(result, indent=2))
    
    print("\n✅ Tool tests complete!")