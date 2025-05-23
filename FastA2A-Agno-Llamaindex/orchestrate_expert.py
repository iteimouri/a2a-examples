import anyio
from fasta2a.client import A2AClient
from fasta2a.schema import Message, TextPart
from typing import Dict, Any
from config import config

class CollaborativeOrchestrator:
    """Sophisticated orchestrator for multi-agent collaboration."""
    
    def __init__(self):
        self.agno_client = A2AClient(base_url=config.AGNO_SERVICE_URL)
        self.llama_client = A2AClient(base_url=config.LLAMAINDEX_SERVICE_URL)
        self.conversation_history = []
    
    async def send_task_and_wait(self, client: A2AClient, prompt: str, service_name: str) -> str:
        """Send a task and wait for completion."""
        send = await client.send_task(
            message=Message(
                role="user",
                parts=[TextPart(type="text", text=prompt)]
            )
        )
        task_id = send["result"]["id"]
        print(f"[ORCH] {service_name} task {task_id} started")
        
        while True:
            reply = await client.get_task(task_id)
            state = reply["result"]["status"]["state"]
            
            if state == "completed":
                result = reply["result"]["artifacts"][0]["parts"][0]["text"]
                self.conversation_history.append({
                    "service": service_name,
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "response": result[:200] + "..." if len(result) > 200 else result
                })
                return result
            elif state in ["failed", "canceled"]:
                raise Exception(f"{service_name} task {state}")
            
            await anyio.sleep(2)
    
    async def expert_consultation_workflow(self, user_question: str) -> Dict[str, Any]:
        """
        Simulates a consultation where:
        1. LlamaIndex acts as the "research specialist" 
        2. Agno acts as the "communication expert"
        3. They collaborate through multiple rounds
        """
        
        print(f"[ORCH] Starting expert consultation for: '{user_question}'")
        
        # Phase 1: Research and Analysis
        print("\n=== Phase 1: Research Analysis ===")
        research_prompt = f"""
        As a research specialist, please provide a comprehensive technical analysis of:
        
        "{user_question}"
        
        Include:
        - Core concepts and principles
        - Technical details and mechanisms
        - Historical context or background
        - Current understanding and any recent developments
        - Potential areas of complexity or common misconceptions
        
        Focus on accuracy and completeness. This will be used by a communication expert to create an accessible explanation.
        """
        
        research_result = await self.send_task_and_wait(
            self.llama_client, research_prompt, "LlamaIndex-Research"
        )
        
        print(f"Research analysis completed: {len(research_result)} characters")
        
        # Phase 2: Communication Strategy
        print("\n=== Phase 2: Communication Strategy ===")
        comm_strategy_prompt = f"""
        As a communication expert, review this technical research about "{user_question}":
        
        RESEARCH ANALYSIS:
        {research_result}
        
        Please develop a communication strategy that:
        1. Identifies the key points that must be conveyed
        2. Suggests analogies, examples, or metaphors that could help understanding
        3. Determines the appropriate level of technical detail
        4. Identifies potential areas where readers might get confused
        5. Recommends the best structure for the explanation
        
        Don't write the final explanation yet - just the communication strategy.
        """
        
        comm_strategy = await self.send_task_and_wait(
            self.agno_client, comm_strategy_prompt, "Agno-Strategy"
        )
        
        print(f"Communication strategy developed: {len(comm_strategy)} characters")
        
        # Phase 3: Research Review of Communication Strategy
        print("\n=== Phase 3: Strategy Review ===")
        strategy_review_prompt = f"""
        As a research specialist, please review this communication strategy for explaining "{user_question}":
        
        COMMUNICATION STRATEGY:
        {comm_strategy}
        
        ORIGINAL RESEARCH:
        {research_result}
        
        Please evaluate:
        1. Are there any scientific inaccuracies in the proposed approach?
        2. Are any critical technical details being oversimplified?
        3. Would any of the suggested analogies be misleading?
        4. What technical caveats or limitations should be mentioned?
        5. Any suggestions for improvement while maintaining accessibility?
        
        Provide feedback to refine the communication approach.
        """
        
        strategy_feedback = await self.send_task_and_wait(
            self.llama_client, strategy_review_prompt, "LlamaIndex-Review"
        )
        
        print(f"Strategy review completed: {len(strategy_feedback)} characters")
        
        # Phase 4: Final Explanation Creation
        print("\n=== Phase 4: Final Explanation ===")
        final_explanation_prompt = f"""
        As a communication expert, create the final explanation for "{user_question}" using:
        
        RESEARCH FOUNDATION:
        {research_result}
        
        COMMUNICATION STRATEGY:
        {comm_strategy}
        
        TECHNICAL FEEDBACK:
        {strategy_feedback}
        
        Create a response that:
        - Is scientifically accurate (incorporating the technical feedback)
        - Follows your communication strategy
        - Is engaging and accessible
        - Addresses the user's question completely
        - Maintains appropriate technical depth
        
        This is the final answer that will be presented to the user.
        """
        
        final_explanation = await self.send_task_and_wait(
            self.agno_client, final_explanation_prompt, "Agno-Final"
        )
        
        # Phase 5: Final Fact-Check
        print("\n=== Phase 5: Final Validation ===")
        final_check_prompt = f"""
        Please perform a final fact-check on this explanation of "{user_question}":
        
        FINAL EXPLANATION:
        {final_explanation}
        
        Verify:
        1. Scientific accuracy
        2. Completeness of core concepts
        3. Appropriateness of examples/analogies
        4. Any missing important caveats
        
        If the explanation is accurate and complete, endorse it.
        If there are issues, provide specific corrections.
        """
        
        final_validation = await self.send_task_and_wait(
            self.llama_client, final_check_prompt, "LlamaIndex-Validation"
        )
        
        return {
            "final_answer": final_explanation,
            "research_analysis": research_result,
            "communication_strategy": comm_strategy,
            "strategy_feedback": strategy_feedback,
            "final_validation": final_validation,
            "conversation_history": self.conversation_history
        }
    
    def print_workflow_summary(self, results: Dict[str, Any]):
        """Print a summary of the collaborative workflow."""
        print("\n" + "="*80)
        print("COLLABORATIVE WORKFLOW SUMMARY")
        print("="*80)
        
        print(f"\nTotal interactions: {len(self.conversation_history)}")
        
        print("\nWorkflow Steps:")
        for i, step in enumerate(self.conversation_history, 1):
            print(f"{i}. {step['service']}: {step['prompt']}")
        
        print("\n" + "="*80)
        print("FINAL COLLABORATIVE ANSWER")
        print("="*80)
        print(results["final_answer"])
        
        print("\n" + "="*80)
        print("FINAL VALIDATION")
        print("="*80)
        print(results["final_validation"])
        print("="*80)

async def main():
    orchestrator = CollaborativeOrchestrator()
    
    # You can change this question or make it interactive
    user_question = "Explain the Pauli exclusion principle in one paragraph."
    
    try:
        print("Starting sophisticated collaborative workflow...")
        print("This will involve multiple rounds of expert consultation.")
        
        results = await orchestrator.expert_consultation_workflow(user_question)
        orchestrator.print_workflow_summary(results)
        
    except Exception as e:
        print(f"[ORCH] Error in collaborative workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    anyio.run(main)
