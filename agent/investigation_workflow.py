"""
Fraud Detection Agent - Investigation Workflow
==============================================

Pipeline:
1. Receive alert → 2. Agent investigates → 3. Generate brief → 4. Store result
"""

import google.generativeai as genai
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from agent import config
from agent.agent_tools import FraudAgentTools, get_tool_descriptions


class FraudInvestigationAgent:
    """
    Fraud investigation agent using Google Gemini with function calling.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the agent with Gemini API.
        
        Args:
            api_key: Google API key (or use GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or config.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set environment variable or pass api_key.\n"
                "Get your free key at: https://aistudio.google.com/app/apikey"
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model WITHOUT system_instruction (compatibility fix)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        # Store system prompt to prepend to first message instead
        self.system_prompt = config.SYSTEM_PROMPT
        
        # Initialize tools
        print("🔧 Initializing fraud agent tools...")
        try:
            self.tools = FraudAgentTools()
            print("✅ Tools initialized successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize all tools: {e}")
            print("   Some features may be limited.")
            self.tools = None
        
        # Convert tool descriptions to Gemini format
        # this converter was added to preserve compatibility since my tools were originally written in Anthropic-style, but I switched my agent to run on Google Gemini
        self.gemini_tools = self._convert_tools_to_gemini_format()
        
        print(f"✅ Agent initialized with {config.GEMINI_MODEL}\n")
    
    def _convert_tools_to_gemini_format(self) -> List[Dict]:
        """
        Convert Anthropic tool format to Gemini function declarations.
        """
        anthropic_tools = get_tool_descriptions()
        gemini_tools = []
        
        for tool in anthropic_tools:
            gemini_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool["input_schema"]["properties"],
                    "required": tool["input_schema"].get("required", [])
                }
            }
            gemini_tools.append(gemini_tool)
        
        return gemini_tools
    
    def investigate(
        self,
        transaction_id: str,
        alert_description: str,
        initial_risk_score: float = 0.5,
        max_turns: int = None
    ) -> Dict[str, Any]:
        """
        Conduct a full fraud investigation.
        
        Args:
            transaction_id: ID of suspicious transaction
            alert_description: Why transaction was flagged
            initial_risk_score: Initial ML model score
            max_turns: Max reasoning cycles (default from config)
            
        Returns:
            Complete investigation brief
        """
        if max_turns is None:
            max_turns = config.MAX_INVESTIGATION_TURNS
        
        print("="*80)
        print(f"🔍 STARTING INVESTIGATION: {transaction_id}")
        print("="*80)
        print(f"Alert: {alert_description}")
        print(f"Initial Risk Score: {initial_risk_score:.2f}")
        print()
        
        # Format investigation prompt with system prompt prepended
        investigation_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        investigation_prompt = config.INVESTIGATION_PROMPT_TEMPLATE.format(
            transaction_id=transaction_id,
            alert_description=alert_description,
            initial_risk_score=initial_risk_score,
            investigation_date=investigation_date
        )
        
        # Combine system prompt with investigation prompt
        prompt = f"{self.system_prompt}\n\n{investigation_prompt}"
        
        # Start chat session (compatible with older versions)
        chat = self.model.start_chat()
        
        investigation_log = []
        turn_count = 0
        
        # Send initial prompt
        try:
            response = chat.send_message(prompt)
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "error": str(e)
            }
        
        # Investigation loop
        while turn_count < max_turns:
            turn_count += 1
            print(f"\n--- Turn {turn_count}/{max_turns} ---")
            
            # Check if we have function calls
            has_function_calls = False
            try:
                # Check for function calls in response
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        break
            except (AttributeError, IndexError) as e:
                print(f"⚠️ Warning parsing response: {e}")
                has_function_calls = False
            
            if has_function_calls:
                # Model wants to use tools
                function_responses = []
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        tool_name = function_call.name
                        tool_args = dict(function_call.args)
                        
                        print(f"🔧 Agent calling: {tool_name}")
                        print(f"   Input: {json.dumps(tool_args, indent=2)}")
                        
                        # Execute tool
                        result = self._execute_tool(tool_name, tool_args)
                        
                        print(f"   ✅ Result received")
                        
                        # Log
                        investigation_log.append({
                            "turn": turn_count,
                            "tool": tool_name,
                            "input": tool_args,
                            "result": result
                        })
                        
                        # Create function response
                        function_responses.append({
                            "name": tool_name,
                            "response": result
                        })
                
                # Send function results back - format as text for compatibility
                function_results_text = "Tool Results:\n\n"
                for fr in function_responses:
                    function_results_text += f"Tool: {fr['name']}\n"
                    function_results_text += f"Result: {json.dumps(fr['response'], indent=2)}\n\n"
                
                try:
                    response = chat.send_message(function_results_text)
                except Exception as e:
                    print(f"❌ Error sending function results: {e}")
                    break
                
            else:
                # Model has finished and provided final answer
                try:
                    final_response = response.text
                except Exception as e:
                    print(f"⚠️ Could not extract text: {e}")
                    final_response = str(response)
                
                print("\n" + "="*80)
                print("📋 INVESTIGATION COMPLETE")
                print("="*80)
                print(final_response)
                
                # Parse brief
                investigation_brief = self._parse_investigation_brief(
                    final_response,
                    transaction_id,
                    investigation_log
                )
                
                return investigation_brief
        
        # Max turns reached
        print(f"\n⚠️ Max turns ({max_turns}) reached")
        return {
            "status": "incomplete",
            "transaction_id": transaction_id,
            "message": "Investigation incomplete - max turns reached",
            "investigation_log": investigation_log
        }
    
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a tool function."""
        if self.tools is None:
            return {"error": "Tools not initialized"}
        
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
        """Parse agent's response into structured format."""
        import re
        
        # Extract confidence score
        confidence = 0.5
        match = re.search(r"Score:\s*(0\.\d+|1\.0)", response_text)
        if match:
            confidence = float(match.group(1))
        
        # Extract recommendation
        recommendation = "VERIFY"
        for action in ["ESCALATE", "VERIFY", "MONITOR", "DISMISS"]:
            if action in response_text:
                recommendation = action
                break
        
        # Count tools used
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


class InvestigationWorkflow:
    """
    Complete investigation workflow manager.
    Handles alert queue, investigation execution, and result storage.
    """
    
    def __init__(self):
        """Initialize workflow."""
        self.agent = FraudInvestigationAgent()
        self.results_dir = config.OUTPUTS_DIR / "investigations"
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def process_alert(
        self,
        transaction_id: str,
        alert_description: str,
        initial_risk_score: float,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single fraud alert through complete workflow.
        
        Args:
            transaction_id: Transaction ID
            alert_description: Alert description
            initial_risk_score: ML model risk score
            save_results: Whether to save results to file
            
        Returns:
            Investigation results
        """
        # Run investigation
        result = self.agent.investigate(
            transaction_id=transaction_id,
            alert_description=alert_description,
            initial_risk_score=initial_risk_score
        )
        
        # Save results
        if save_results and result.get("status") == "complete":
            self._save_investigation(result)
        
        return result
    
    def process_alert_queue(
        self,
        alerts: List[Dict[str, Any]],
        max_alerts: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple alerts from queue.
        
        Args:
            alerts: List of alert dicts with transaction_id, description, risk_score
            max_alerts: Max number to process
            
        Returns:
            List of investigation results
        """
        if max_alerts:
            alerts = alerts[:max_alerts]
        
        results = []
        
        print(f"\n📋 Processing {len(alerts)} alerts...\n")
        
        for i, alert in enumerate(alerts, 1):
            print(f"\n{'='*80}")
            print(f"Alert {i}/{len(alerts)}")
            print(f"{'='*80}")
            
            result = self.process_alert(
                transaction_id=alert["transaction_id"],
                alert_description=alert["description"],
                initial_risk_score=alert["risk_score"]
            )
            
            results.append(result)
        
        # Generate summary
        self._print_summary(results)
        
        return results
    
    def _save_investigation(self, result: Dict[str, Any]):
        """Save investigation result to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result['case_id']}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Investigation saved: {filepath}")
    
    def _print_summary(self, results: List[Dict[str, Any]]):
        """Print summary of processed alerts."""
        print("\n" + "="*80)
        print("📊 INVESTIGATION SUMMARY")
        print("="*80)
        
        # Count by recommendation
        recommendations = {}
        for result in results:
            rec = result.get("recommendation", "UNKNOWN")
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        print(f"\nTotal Investigations: {len(results)}")
        print("\nRecommendations:")
        for rec, count in sorted(recommendations.items()):
            print(f"  {rec}: {count}")
        
        # Average confidence
        avg_confidence = sum(r.get("confidence_score", 0) for r in results) / len(results)
        print(f"\nAverage Confidence: {avg_confidence:.2f}")
        
        # Average tool calls
        avg_tools = sum(r.get("total_tool_calls", 0) for r in results) / len(results)
        print(f"Average Tool Calls: {avg_tools:.1f}")
        
        print("="*80)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Process a single alert
    workflow = InvestigationWorkflow()
    
    result = workflow.process_alert(
        transaction_id="TXN_00012345",
        alert_description="Large transaction ($5,000) at unusual hour (3 AM) from new device",
        initial_risk_score=0.85
    )
    
    # Check if investigation was successful
    if result.get("status") == "complete":
        print(f"\n✅ Investigation complete!")
        print(f"   Recommendation: {result['recommendation']}")
        print(f"   Confidence: {result['confidence_score']:.2f}")
    elif result.get("status") == "error":
        print(f"\n❌ Investigation failed!")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"\n⚠️ Investigation incomplete!")
        print(f"   Status: {result.get('status', 'Unknown')}")
    
    # Example: Process multiple alerts
    # alerts = [
    #     {
    #         "transaction_id": "TXN_00012345",
    #         "description": "Large late-night transaction",
    #         "risk_score": 0.85
    #     },
    #     {
    #         "transaction_id": "TXN_00012346",
    #         "description": "Multiple small transactions",
    #         "risk_score": 0.72
    #     }
    # ]
    # 
    # results = workflow.process_alert_queue(alerts)