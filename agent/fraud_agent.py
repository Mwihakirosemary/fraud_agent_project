"""
Fraud Detection Agent - Main Investigation Agent
=================================================

Implements the ReAct (Reasoning + Acting) pattern with Claude Sonnet 4.

The agent:
1. Receives a suspicious transaction alert
2. Reasons about what information it needs
3. Calls tools to gather evidence
4. Synthesizes findings into an investigation brief
5. Provides a recommendation with confidence score
"""

import anthropic
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from agent.agent_tools import FraudAgentTools, get_tool_descriptions


class FraudInvestigationAgent:
    """
    Autonomous fraud investigation agent using Claude Sonnet 4.
    
    Uses the ReAct pattern:
    - Reasoning: Thinks about what to do next
    - Acting: Calls appropriate tools
    - Observing: Processes tool results
    - Repeats until investigation is complete
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the fraud investigation agent.
        
        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        # Initialize Anthropic client
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set environment variable or pass api_key parameter.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        
        # Initialize tools
        print("🔧 Initializing fraud agent tools...")
        self.tools = FraudAgentTools()
        self.tool_descriptions = get_tool_descriptions()
        
        # System prompt for the agent
        self.system_prompt = """You are an expert fraud investigation agent for a financial institution.

Your role is to:
1. Investigate suspicious transactions systematically
2. Gather evidence from multiple data sources using available tools
3. Cross-reference information to identify fraud patterns
4. Generate comprehensive investigation briefs
5. Provide clear recommendations with confidence scores

Investigation Guidelines:
- Always start by examining the transaction details
- Check the customer's KYC profile and risk level
- Look for similar past cases to learn from precedents
- Search for matching fraud patterns
- Review security logs (SIEM) for suspicious activity
- Cross-reference findings across multiple sources
- Be thorough but efficient - aim for 3-5 tool calls per investigation

Output Requirements:
- Clear, structured investigation brief
- Evidence-based conclusions
- Specific fraud indicators found
- Confidence score (0.0-1.0) based on evidence strength
- Recommended action: ESCALATE, VERIFY, MONITOR, or DISMISS
- Audit trail of all findings

Be professional, objective, and always explain your reasoning."""
        
        print("✅ Fraud Investigation Agent initialized\n")
    
    def investigate(
        self,
        transaction_id: str,
        alert_description: str,
        initial_risk_score: float = 0.5,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """
        Conduct a full fraud investigation on a flagged transaction.
        
        Args:
            transaction_id: ID of the suspicious transaction
            alert_description: Why this transaction was flagged
            initial_risk_score: Initial fraud probability from ML model
            max_turns: Maximum reasoning-action cycles
            
        Returns:
            Complete investigation brief with recommendation
        """
        print("="*80)
        print(f"🔍 STARTING INVESTIGATION: {transaction_id}")
        print("="*80)
        print(f"Alert: {alert_description}")
        print(f"Initial Risk Score: {initial_risk_score:.2f}")
        print()
        
        # Start conversation
        messages = [
            {
                "role": "user",
                "content": f"""Investigate this suspicious transaction:

Transaction ID: {transaction_id}
Alert Reason: {alert_description}
Initial Risk Score: {initial_risk_score:.2f}

Please conduct a thorough fraud investigation using available tools. 

After gathering sufficient evidence, provide your investigation brief in this format:

INVESTIGATION BRIEF
==================
Case ID: {transaction_id}
Investigation Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

SUMMARY:
[One paragraph summary of what you found]

EVIDENCE:
1. [Evidence point 1]
2. [Evidence point 2]
3. [Evidence point 3]
...

FRAUD INDICATORS:
- [Specific red flags identified]

SIMILAR CASES:
[Brief mention of any similar past cases]

CONFIDENCE ASSESSMENT:
Score: [0.0-1.0]
Reasoning: [Why this confidence level]

RECOMMENDATION: [ESCALATE | VERIFY | MONITOR | DISMISS]
Reasoning: [Why this action is appropriate]

Begin your investigation now."""
            }
        ]
        
        # Investigation loop
        investigation_log = []
        turn_count = 0
        
        while turn_count < max_turns:
            turn_count += 1
            print(f"\n--- Turn {turn_count}/{max_turns} ---")
            
            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tool_descriptions,
                messages=messages
            )
            
            # Process response
            stop_reason = response.stop_reason
            
            # Check if agent wants to use tools
            if stop_reason == "tool_use":
                # Agent wants to call tools
                tool_results = []
                
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id
                        
                        print(f"🔧 Agent calling: {tool_name}")
                        print(f"   Input: {json.dumps(tool_input, indent=2)}")
                        
                        # Execute tool
                        result = self._execute_tool(tool_name, tool_input)
                        
                        print(f"   ✅ Result received")
                        
                        # Log the tool call
                        investigation_log.append({
                            "turn": turn_count,
                            "tool": tool_name,
                            "input": tool_input,
                            "result": result
                        })
                        
                        # Add tool result to messages
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result)
                        })
                
                # Add assistant's tool use and tool results to conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                
            elif stop_reason == "end_turn":
                # Agent has finished reasoning and provided final answer
                final_response = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        final_response += content_block.text
                
                print("\n" + "="*80)
                print("📋 INVESTIGATION COMPLETE")
                print("="*80)
                print(final_response)
                
                # Parse the investigation brief
                investigation_brief = self._parse_investigation_brief(
                    final_response,
                    transaction_id,
                    investigation_log
                )
                
                return investigation_brief
            
            else:
                # Unexpected stop reason
                print(f"⚠️ Unexpected stop reason: {stop_reason}")
                break
        
        # Max turns reached
        print(f"\n⚠️ Max turns ({max_turns}) reached. Ending investigation.")
        
        return {
            "status": "incomplete",
            "transaction_id": transaction_id,
            "message": "Investigation incomplete - max turns reached",
            "investigation_log": investigation_log
        }
    
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Execute a tool function and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            
        Returns:
            Tool execution result
        """
        # Map tool names to functions
        tool_map = {
            "query_similar_cases": self.tools.query_similar_cases,
            "search_fraud_patterns": self.tools.search_fraud_patterns,
            "fetch_kyc_profile": self.tools.fetch_kyc_profile,
            "query_siem_events": self.tools.query_siem_events,
            "get_transaction_details": self.tools.get_transaction_details,
            "get_transaction_history": self.tools.get_transaction_history,
        }
        
        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            # Call the tool function
            result = tool_map[tool_name](**tool_input)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_investigation_brief(
        self,
        response_text: str,
        transaction_id: str,
        investigation_log: List[Dict]
    ) -> Dict[str, Any]:
        """
        Parse the agent's final response into structured format.
        
        Args:
            response_text: Agent's text response
            investigation_log: Log of all tool calls made
            
        Returns:
            Structured investigation brief
        """
        # Extract confidence score
        confidence = 0.5  # Default
        if "Confidence" in response_text or "Score:" in response_text:
            import re
            match = re.search(r"Score:\s*(0\.\d+|1\.0)", response_text)
            if match:
                confidence = float(match.group(1))
        
        # Extract recommendation
        recommendation = "VERIFY"  # Default
        for action in ["ESCALATE", "VERIFY", "MONITOR", "DISMISS"]:
            if action in response_text:
                recommendation = action
                break
        
        # Count tool calls by type
        tools_used = {}
        for log_entry in investigation_log:
            tool = log_entry["tool"]
            tools_used[tool] = tools_used.get(tool, 0) + 1
        
        return {
            "case_id": transaction_id,
            "investigation_date": datetime.now().isoformat(),
            "recommendation": recommendation,
            "confidence_score": confidence,
            "investigation_brief": response_text,
            "tools_used": tools_used,
            "total_tool_calls": len(investigation_log),
            "investigation_log": investigation_log,
            "status": "complete"
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example investigation
    agent = FraudInvestigationAgent()
    
    # Investigate a suspicious transaction
    result = agent.investigate(
        transaction_id="TXN_00012345",
        alert_description="Large transaction ($5,000) at unusual hour (3 AM) from new device",
        initial_risk_score=0.85,
        max_turns=8
    )
    
    print("\n" + "="*80)
    print("INVESTIGATION RESULT")
    print("="*80)
    print(json.dumps(result, indent=2, default=str))
    
    print(f"\n✅ Investigation complete!")
    print(f"   Recommendation: {result['recommendation']}")
    print(f"   Confidence: {result['confidence_score']:.2f}")
    print(f"   Tools used: {result['total_tool_calls']}")