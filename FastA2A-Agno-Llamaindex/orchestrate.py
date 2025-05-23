import anyio
from fasta2a.client import A2AClient
from fasta2a.schema import Message, TextPart
from config import config

async def wait_for_task_completion(client: A2AClient, task_id: str, service_name: str):
    """Wait for a task to complete and return the result."""
    max_attempts = 60  # 2 minutes timeout
    attempts = 0
    
    while attempts < max_attempts:
        try:
            reply = await client.get_task(task_id)
            state = reply["result"]["status"]["state"]
            print(f"[ORCH] {service_name} task {task_id} state = {state}")
            
            if state == "completed":
                return reply["result"]["artifacts"][0]["parts"][0]["text"]
            elif state == "failed":
                # Get error details if available
                error_info = reply["result"].get("error", "No error details available")
                raise Exception(f"{service_name} task failed: {error_info}")
            elif state == "canceled":
                raise Exception(f"{service_name} task was canceled")
            
            attempts += 1
            await anyio.sleep(2)
            
        except Exception as e:
            if "500" in str(e) or "Internal Server Error" in str(e):
                print(f"[ORCH] {service_name} service error, retrying... ({attempts + 1}/{max_attempts})")
                attempts += 1
                await anyio.sleep(5)  # Wait longer for server errors
                continue
            else:
                raise e
    
    raise Exception(f"{service_name} task timed out after {max_attempts * 2} seconds")

async def send_task_to_service(client: A2AClient, prompt: str, service_name: str):
    """Send a task to a service and return the task ID."""
    send = await client.send_task(
        message=Message(
            role="user",
            parts=[TextPart(type="text", text=prompt)]
        )
    )
    task_id = send["result"]["id"]
    print(f"[ORCH] {service_name} task id = {task_id}")
    return task_id

async def orchestrate_collaborative_workflow(initial_prompt: str):
    """Orchestrate a workflow where both services collaborate."""
    
    # Initialize clients for both services
    agno_client = A2AClient(base_url=config.AGNO_SERVICE_URL)
    llama_client = A2AClient(base_url=config.LLAMAINDEX_SERVICE_URL)
    
    print(f"[ORCH] Starting collaborative workflow with prompt: '{initial_prompt[:60]}...'")
    
    # Step 1: Send initial task to LlamaIndex (RAG-enhanced analysis)
    print("\n=== Step 1: LlamaIndex RAG Analysis ===")
    llama_prompt = f"""
    Please provide a comprehensive analysis of the following topic using your retrieval-augmented capabilities:
    
    Topic: {initial_prompt}
    
    Focus on providing factual, well-sourced information and identify any areas that might need further clarification or different perspectives.
    """
    
    llama_task_id = await send_task_to_service(llama_client, llama_prompt, "LlamaIndex")
    llama_result = await wait_for_task_completion(llama_client, llama_task_id, "LlamaIndex")
    
    print(f"\n--- LlamaIndex Result ---\n{llama_result}\n")
    
    # Step 2: Send LlamaIndex result to Agno for creative enhancement and synthesis
    print("=== Step 2: Agno Creative Synthesis ===")
    agno_prompt = f"""
    I have received the following analysis from a RAG-enhanced system about "{initial_prompt}":

    {llama_result}

    Please:
    1. Synthesize this information in a more accessible and engaging way
    2. Add creative insights or analogies that might help understanding
    3. Identify any potential counterarguments or alternative perspectives
    4. Provide a final, well-rounded response that combines factual accuracy with clear communication

    Make your response comprehensive but engaging.
    """
    
    agno_task_id = await send_task_to_service(agno_client, agno_prompt, "Agno")
    agno_result = await wait_for_task_completion(agno_client, agno_task_id, "Agno")
    
    print(f"\n--- Agno Enhanced Result ---\n{agno_result}\n")
    
    # Step 3: Send Agno's synthesis back to LlamaIndex for fact-checking and validation
    print("=== Step 3: LlamaIndex Fact-Check & Validation ===")
    validation_prompt = f"""
    Please review the following synthesized response for accuracy and completeness:

    Original topic: {initial_prompt}
    
    Synthesized response to validate:
    {agno_result}

    Please:
    1. Verify the factual accuracy of the claims made
    2. Check if any important information was omitted or misrepresented
    3. Suggest any corrections or additions needed
    4. Provide a final confidence assessment

    If the synthesis is accurate, endorse it. If not, provide corrections.
    """
    
    validation_task_id = await send_task_to_service(llama_client, validation_prompt, "LlamaIndex")
    validation_result = await wait_for_task_completion(llama_client, validation_task_id, "LlamaIndex")
    
    print(f"\n--- LlamaIndex Validation ---\n{validation_result}\n")
    
    # Step 4: Final synthesis by Agno incorporating validation feedback
    print("=== Step 4: Final Collaborative Result ===")
    final_prompt = f"""
    Based on the validation feedback below, please provide the final, most accurate and engaging response to: "{initial_prompt}"

    Validation feedback:
    {validation_result}

    Previous synthesis:
    {agno_result}

    Please incorporate any necessary corrections and provide the definitive answer.
    """
    
    final_task_id = await send_task_to_service(agno_client, final_prompt, "Agno")
    final_result = await wait_for_task_completion(agno_client, final_task_id, "Agno")
    
    return final_result

async def main():
    initial_question = "Explain the Pauli exclusion principle in one paragraph."
    
    try:
        final_answer = await orchestrate_collaborative_workflow(initial_question)
        
        print("\n" + "="*60)
        print("FINAL COLLABORATIVE RESULT")
        print("="*60)
        print(final_answer)
        print("="*60)
        
    except Exception as e:
        print(f"[ORCH] Error in collaborative workflow: {e}")

if __name__ == "__main__":
    anyio.run(main)