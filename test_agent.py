"""
Quick test to verify agent setup
"""
from agent.agent_tools import FraudAgentTools
import json

print("Testing agent tools setup...\n")

# Initialize tools
tools = FraudAgentTools()

# Test 1: Query similar cases
print("🔍 Test 1: Querying similar cases...")
result = tools.query_similar_cases(
    "Account takeover with password reset",
    n_results=3
)
print(f"✅ Found {result['num_results']} similar cases")

# Test 2: Fetch KYC profile
print("\n👤 Test 2: Fetching KYC profile...")
# Use a real user_id from your data
result = tools.fetch_kyc_profile("USER_001")
print(f"✅ Profile found: {result.get('found', False)}")

print("\n🎉 Agent tools are working correctly!")