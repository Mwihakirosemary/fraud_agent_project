"""
Fraud Detection Agent - Investigation Dashboard
===============================================

Interactive Streamlit dashboard for fraud analysts.

Features:
- Alert queue with priority sorting
- Real-time investigation execution
- Interactive investigation brief viewer
- Evidence panel with expandable sections
- Analyst feedback mechanism
- Investigation history
- Analytics dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import agent modules
from agent import config
from agent.investigation_workflow import InvestigationWorkflow


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        margin: 0.5rem 0;
    }
    .evidence-item {
        background: #f8f9fa;
        padding: 1rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .recommendation-badge {
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: bold;
        display: inline-block;
    }
    .escalate { background: #ef4444; color: white; }
    .verify { background: #f59e0b; color: white; }
    .monitor { background: #3b82f6; color: white; }
    .dismiss { background: #10b981; color: white; }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'workflow' not in st.session_state:
    st.session_state.workflow = None

if 'current_investigation' not in st.session_state:
    st.session_state.current_investigation = None

if 'investigation_history' not in st.session_state:
    st.session_state.investigation_history = []

if 'selected_alert' not in st.session_state:
    st.session_state.selected_alert = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def initialize_workflow():
    """Initialize the investigation workflow."""
    try:
        with st.spinner("🔧 Initializing fraud detection agent..."):
            workflow = InvestigationWorkflow()
        st.session_state.workflow = workflow
        return True
    except Exception as e:
        st.error(f"❌ Failed to initialize: {str(e)}")
        st.exception(e)  # Show full error for debugging
        return False


def generate_sample_alerts(n=10):
    """Generate sample fraud alerts for demo."""
    import random
    
    alert_types = [
        ("Large late-night transaction", 0.85),
        ("Multiple small transactions in short time", 0.78),
        ("Transaction from unusual location", 0.72),
        ("High-risk merchant category", 0.68),
        ("Velocity check failed - too many transactions", 0.82),
        ("New device, high-value transaction", 0.88),
        ("Suspicious international transfer", 0.80),
        ("Card-not-present transaction spike", 0.75),
    ]
    
    alerts = []
    for i in range(n):
        description, base_risk = random.choice(alert_types)
        risk = base_risk + random.uniform(-0.1, 0.1)
        
        alerts.append({
            "transaction_id": f"TXN_{random.randint(10000, 99999):05d}",
            "description": description,
            "risk_score": min(max(risk, 0), 1),
            "timestamp": datetime.now() - timedelta(hours=random.randint(0, 24)),
            "amount": random.randint(100, 10000),
            "status": "pending"
        })
    
    return sorted(alerts, key=lambda x: x['risk_score'], reverse=True)


def get_recommendation_color(recommendation):
    """Get color for recommendation badge."""
    colors = {
        "ESCALATE": "#ef4444",
        "VERIFY": "#f59e0b",
        "MONITOR": "#3b82f6",
        "DISMISS": "#10b981"
    }
    return colors.get(recommendation, "#6b7280")


def format_confidence_score(score):
    """Format confidence score with color."""
    if score >= 0.85:
        return f"🔴 {score:.2%} (Very High)"
    elif score >= 0.60:
        return f"🟠 {score:.2%} (High)"
    elif score >= 0.40:
        return f"🟡 {score:.2%} (Medium)"
    else:
        return f"🟢 {score:.2%} (Low)"


# ============================================================================
# SIDEBAR - NAVIGATION & CONTROLS
# ============================================================================

with st.sidebar:
    st.title("🔍 Fraud Detection")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📋 Alert Queue", "🔎 Investigate", "📊 Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick Stats
    st.subheader("Quick Stats")
    
    if st.session_state.investigation_history:
        total_investigations = len(st.session_state.investigation_history)
        escalated = sum(1 for inv in st.session_state.investigation_history 
                       if inv.get('recommendation') == 'ESCALATE')
        avg_confidence = sum(inv.get('confidence_score', 0) 
                           for inv in st.session_state.investigation_history) / total_investigations
        
        col1, col2 = st.columns(2)
        col1.metric("Total Cases", total_investigations)
        col2.metric("Escalated", escalated)
        st.metric("Avg Confidence", f"{avg_confidence:.0%}")
    else:
        st.info("No investigations yet")
    
    st.markdown("---")
    
    # System Status
    st.subheader("System Status")
    if st.session_state.workflow:
        st.success("✅ Agent Online")
    else:
        if st.button("🚀 Initialize Agent"):
            initialize_workflow()
    
    st.markdown("---")
    st.caption("Built by Rosemary | 2025")


# ============================================================================
# MAIN PAGES
# ============================================================================

if page == "🏠 Dashboard":
    # ========================================================================
    # DASHBOARD HOME
    # ========================================================================
    
    st.title("🏠 Fraud Investigation Dashboard")
    st.markdown("Real-time fraud detection and investigation platform")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Alerts",
            "10",
            delta="2 new",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "Avg Investigation Time",
            "2.3 min",
            delta="-0.5 min",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Precision Rate",
            "92%",
            delta="+3%"
        )
    
    with col4:
        st.metric(
            "Cases Today",
            len(st.session_state.investigation_history),
            delta=f"+{len(st.session_state.investigation_history)}"
        )
    
    st.markdown("---")
    
    # Recent Investigations
    st.subheader("📋 Recent Investigations")
    
    if st.session_state.investigation_history:
        for inv in reversed(st.session_state.investigation_history[-5:]):
            with st.expander(
                f"🔍 {inv['case_id']} - {inv['recommendation']} "
                f"(Confidence: {inv['confidence_score']:.0%})"
            ):
                st.text(inv['investigation_brief'][:300] + "...")
                if st.button("View Full Report", key=f"view_{inv['case_id']}"):
                    st.session_state.current_investigation = inv
                    st.rerun()
    else:
        st.info("👋 No investigations yet. Head to **Alert Queue** to start investigating!")
    
    # Quick Charts
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Investigation Trends")
        if st.session_state.investigation_history:
            df = pd.DataFrame(st.session_state.investigation_history)
            fig = px.pie(
                df,
                names='recommendation',
                title='Recommendations Distribution',
                color_discrete_map={
                    'ESCALATE': '#ef4444',
                    'VERIFY': '#f59e0b',
                    'MONITOR': '#3b82f6',
                    'DISMISS': '#10b981'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet")
    
    with col2:
        st.subheader("🎯 Confidence Distribution")
        if st.session_state.investigation_history:
            df = pd.DataFrame(st.session_state.investigation_history)
            fig = px.histogram(
                df,
                x='confidence_score',
                nbins=10,
                title='Confidence Score Distribution'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet")


elif page == "📋 Alert Queue":
    # ========================================================================
    # ALERT QUEUE
    # ========================================================================
    
    st.title("📋 Fraud Alert Queue")
    st.markdown("Prioritized list of suspicious transactions requiring investigation")
    
    # Generate sample alerts
    if 'alerts' not in st.session_state:
        st.session_state.alerts = generate_sample_alerts(15)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        min_risk = st.slider("Minimum Risk Score", 0.0, 1.0, 0.5)
    with col2:
        sort_by = st.selectbox("Sort By", ["Risk Score", "Amount", "Time"])
    with col3:
        if st.button("🔄 Refresh Alerts"):
            st.session_state.alerts = generate_sample_alerts(15)
            st.rerun()
    
    # Filter alerts
    filtered_alerts = [a for a in st.session_state.alerts if a['risk_score'] >= min_risk]
    
    st.markdown(f"**Showing {len(filtered_alerts)} alerts**")
    
    # Alert table
    for alert in filtered_alerts:
        risk_color = "🔴" if alert['risk_score'] > 0.8 else "🟠" if alert['risk_score'] > 0.6 else "🟡"
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.markdown(f"**{alert['transaction_id']}**")
                st.caption(alert['description'])
            
            with col2:
                st.metric("Risk Score", f"{risk_color} {alert['risk_score']:.0%}")
            
            with col3:
                st.metric("Amount", f"${alert['amount']:,}")
            
            with col4:
                if st.button("🔎 Investigate", key=f"inv_{alert['transaction_id']}"):
                    st.session_state.selected_alert = alert
                    st.session_state.page = "🔎 Investigate"
                    st.rerun()
            
            st.markdown("---")


elif page == "🔎 Investigate":
    # ========================================================================
    # INVESTIGATION PAGE
    # ========================================================================
    
    st.title("🔎 Fraud Investigation")
    
    # Initialize workflow if needed
    if not st.session_state.workflow:
        if not initialize_workflow():
            st.stop()
    
    # Investigation form
    st.subheader("Case Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transaction_id = st.text_input(
            "Transaction ID",
            value=st.session_state.selected_alert['transaction_id'] if st.session_state.selected_alert else "TXN_00012345"
        )
    
    with col2:
        risk_score = st.slider(
            "Initial Risk Score",
            0.0, 1.0,
            value=st.session_state.selected_alert['risk_score'] if st.session_state.selected_alert else 0.75
        )
    
    alert_description = st.text_area(
        "Alert Description",
        value=st.session_state.selected_alert['description'] if st.session_state.selected_alert else "Suspicious transaction pattern detected",
        height=100
    )
    
    # Start investigation button
    if st.button("🚀 Start Investigation", type="primary", use_container_width=True):
        with st.spinner("🔍 Agent is investigating... This may take 1-2 minutes"):
            try:
                result = st.session_state.workflow.process_alert(
                    transaction_id=transaction_id,
                    alert_description=alert_description,
                    initial_risk_score=risk_score,
                    save_results=True
                )
                
                st.session_state.current_investigation = result
                st.session_state.investigation_history.append(result)
                
                st.success("✅ Investigation Complete!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Investigation failed: {str(e)}")
                st.exception(e)
    
    # Display results if available
    if st.session_state.current_investigation:
        st.markdown("---")
        inv = st.session_state.current_investigation
        
        # Header with recommendation
        st.markdown(f"""
        <div style='background: {get_recommendation_color(inv['recommendation'])}; 
                    padding: 1.5rem; border-radius: 1rem; color: white; margin-bottom: 1rem;'>
            <h2>Recommendation: {inv['recommendation']}</h2>
            <p style='font-size: 1.2rem; margin: 0;'>
                Confidence: {format_confidence_score(inv['confidence_score'])}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Investigation Brief
        st.subheader("📋 Investigation Brief")
        st.markdown(inv['investigation_brief'])
        
        # Tools Used
        with st.expander("🔧 Tools Used"):
            for tool, count in inv['tools_used'].items():
                st.markdown(f"- **{tool}**: {count} call(s)")
        
        # Investigation Log
        with st.expander("📝 Detailed Investigation Log"):
            for i, log_entry in enumerate(inv['investigation_log'], 1):
                st.markdown(f"**Step {i}: {log_entry['tool']}**")
                st.json(log_entry['input'])
                st.caption(f"Turn {log_entry['turn']}")
                st.markdown("---")
        
        # Analyst Feedback
        st.subheader("👤 Analyst Feedback")
        col1, col2 = st.columns(2)
        
        with col1:
            analyst_decision = st.selectbox(
                "Your Decision",
                ["Agree", "Disagree - Should be different", "Needs more investigation"]
            )
        
        with col2:
            confidence_rating = st.slider("Quality Rating", 1, 5, 4)
        
        analyst_notes = st.text_area("Notes", placeholder="Add your notes here...")
        
        if st.button("📤 Submit Feedback"):
            st.success("✅ Feedback submitted! This will help improve the agent.")


elif page == "📊 Analytics":
    # ========================================================================
    # ANALYTICS PAGE
    # ========================================================================
    
    st.title("📊 Investigation Analytics")
    
    if not st.session_state.investigation_history:
        st.info("👋 No data yet. Complete some investigations to see analytics!")
        st.stop()
    
    df = pd.DataFrame(st.session_state.investigation_history)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Cases", len(df))
    col2.metric("Avg Confidence", f"{df['confidence_score'].mean():.0%}")
    col3.metric("Avg Tools Used", f"{df['total_tool_calls'].mean():.1f}")
    
    escalation_rate = (df['recommendation'] == 'ESCALATE').mean()
    col4.metric("Escalation Rate", f"{escalation_rate:.0%}")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recommendations Over Time")
        df_time = df.copy()
        df_time['investigation_date'] = pd.to_datetime(df_time['investigation_date'])
        
        fig = px.scatter(
            df_time,
            x='investigation_date',
            y='confidence_score',
            color='recommendation',
            size='total_tool_calls',
            hover_data=['case_id'],
            title='Investigation Timeline'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Tool Usage Distribution")
        
        # Flatten tools_used
        all_tools = []
        for inv in st.session_state.investigation_history:
            for tool, count in inv['tools_used'].items():
                all_tools.extend([tool] * count)
        
        if all_tools:
            tool_df = pd.DataFrame({'tool': all_tools})
            fig = px.bar(
                tool_df['tool'].value_counts().reset_index(),
                x='count',
                y='tool',
                orientation='h',
                title='Most Used Tools'
            )
            st.plotly_chart(fig, use_container_width=True)


else:  # Settings
    # ========================================================================
    # SETTINGS PAGE
    # ========================================================================
    
    st.title("⚙️ Settings")
    
    st.subheader("🔧 Configuration")
    
    with st.expander("API Configuration"):
        st.text_input("Google API Key", value="***********", type="password")
        st.selectbox("Gemini Model", [config.GEMINI_MODEL])
        st.number_input("Max Investigation Turns", value=config.MAX_INVESTIGATION_TURNS)
    
    with st.expander("Confidence Thresholds"):
        for action, threshold in config.CONFIDENCE_THRESHOLDS.items():
            st.slider(f"{action} Threshold", 0.0, 1.0, threshold, key=f"thresh_{action}")
    
    with st.expander("System Status"):
        st.code(f"""
Base Directory: {config.BASE_DIR}
Model: {config.GEMINI_MODEL}
Vector DB: {config.VECTOR_DB_DIR}
        """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset Investigation History"):
            st.session_state.investigation_history = []
            st.success("✅ History cleared")
    
    with col2:
        if st.button("📥 Export Data"):
            st.download_button(
                "Download Investigations",
                data=json.dumps(st.session_state.investigation_history, indent=2),
                file_name="investigations.json",
                mime="application/json"
            )


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6b7280;'>"
    "🔍 Fraud Detection Agent | Built with Streamlit & Google Gemini | Rosemary 2025"
    "</div>",
    unsafe_allow_html=True
)