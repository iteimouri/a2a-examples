import anyio
from fasta2a.client import A2AClient
from fasta2a.schema import Message, TextPart
from config import config

async def wait_for_task_completion(client: A2AClient, task_id: str, service_name: str):
    """Wait for a task to complete and return the result."""
    while True:
        reply = await client.get_task(task_id)
        state = reply["result"]["status"]["state"]
        print(f"[ORCH] {service_name} task {task_id} state = {state}")
        
        if state == "completed":
            return reply["result"]["artifacts"][0]["parts"][0]["text"]
        elif state == "failed":
            raise Exception(f"{service_name} task failed")
        elif state == "canceled":
            raise Exception(f"{service_name} task was canceled")
        
        await anyio.sleep(2)

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

async def parallel_processing_workflow(initial_prompt: str):
    """Process the same prompt through both services in parallel, then synthesize."""
    
    # Initialize clients for both services
    agno_client = A2AClient(base_url=config.AGNO_SERVICE_URL)
    llama_client = A2AClient(base_url=config.LLAMAINDEX_SERVICE_URL)
    
    print(f"[ORCH] Starting parallel workflow with prompt: '{initial_prompt[:60]}...'")
    
    # Send the same prompt to both services simultaneously
    print("\n=== Parallel Processing Phase ===")
    
    async def process_with_agno():
        agno_prompt = f"""
        Please provide a comprehensive and engaging explanation of:
        {initial_prompt}
        
        Focus on clarity, creativity, and making the concept accessible.
        """
        task_id = await send_task_to_service(agno_client, agno_prompt, "Agno")
        return await wait_for_task_completion(agno_client, task_id, "Agno")
    
    async def process_with_llama():
        llama_prompt = f"""
        Please provide a detailed, factual analysis of:
        {initial_prompt}
        
        Focus on accuracy, technical depth, and comprehensive coverage.
        """
        task_id = await send_task_to_service(llama_client, llama_prompt, "LlamaIndex")
        return await wait_for_task_completion(llama_client, task_id, "LlamaIndex")
    
    # Run both tasks in parallel using anyio task group
    async with anyio.create_task_group() as tg:
        tg.start_soon(process_with_agno)
        tg.start_soon(process_with_llama)
    
    # Since we can't capture results from start_soon, let's use a different approach
    # Run them sequentially but track timing
    print("Processing with both services...")
    
    # Use anyio.gather equivalent with create_task_group
    results = []
    async def collect_agno():
        result = await process_with_agno()
        results.append(('agno', result))
    
    async def collect_llama():
        result = await process_with_llama()
        results.append(('llama', result))
    
    async with anyio.create_task_group() as tg:
        tg.start_soon(collect_agno)
        tg.start_soon(collect_llama)
    
    # Extract results
    agno_result = None
    llama_result = None
    for service, result in results:
        if service == 'agno':
            agno_result = result
        elif service == 'llama':
            llama_result = result
    
    print(f"\n--- Agno Result ---\n{agno_result}\n")
    print(f"\n--- LlamaIndex Result ---\n{llama_result}\n")
    
    # Synthesis phase: Have Agno combine both perspectives
    print("=== Synthesis Phase ===")
    synthesis_prompt = f"""
    I have two different responses to the question: "{initial_prompt}"

    Response 1 (Creative/Accessible):
    {agno_result}

    Response 2 (Technical/Factual):
    {llama_result}

    Please synthesize these two responses into a single, comprehensive answer that:
    1. Combines the best aspects of both responses
    2. Resolves any contradictions by favoring factual accuracy
    3. Maintains accessibility while preserving technical precision
    4. Provides a well-rounded, complete answer

    Create the definitive response that leverages both perspectives.
    """
    
    synthesis_task_id = await send_task_to_service(agno_client, synthesis_prompt, "Agno")
    final_result = await wait_for_task_completion(agno_client, synthesis_task_id, "Agno")
    
    return final_result, agno_result, llama_result

async def debate_workflow(initial_prompt: str):
    """Create a debate between the two services."""
    
    agno_client = A2AClient(base_url=config.AGNO_SERVICE_URL)
    llama_client = A2AClient(base_url=config.LLAMAINDEX_SERVICE_URL)
    
    print(f"[ORCH] Starting debate workflow with prompt: '{initial_prompt[:60]}...'")
    
    # Round 1: Initial positions
    print("\n=== Round 1: Initial Positions ===")
    
    agno_prompt1 = f"""
    You are participating in a collaborative discussion about: "{initial_prompt}"
    
    Please provide your initial perspective, focusing on creative insights and accessible explanations.
    After this, you'll see another perspective and can build upon or refine your response.
    """
    
    llama_prompt1 = f"""
    You are participating in a collaborative discussion about: "{initial_prompt}"
    
    Please provide your initial perspective, focusing on factual accuracy and comprehensive technical details.
    After this, you'll see another perspective and can build upon or refine your response.
    """
    
    # Get initial responses in parallel
    agno_task1 = await send_task_to_service(agno_client, agno_prompt1, "Agno")
    llama_task1 = await send_task_to_service(llama_client, llama_prompt1, "LlamaIndex")
    
    # Wait for both to complete in parallel using anyio task group
    round1_results = []
    
    async def collect_agno1():
        result = await wait_for_task_completion(agno_client, agno_task1, "Agno")
        round1_results.append(('agno', result))
    
    async def collect_llama1():
        result = await wait_for_task_completion(llama_client, llama_task1, "LlamaIndex")
        round1_results.append(('llama', result))
    
    async with anyio.create_task_group() as tg:
        tg.start_soon(collect_agno1)
        tg.start_soon(collect_llama1)
    
    # Extract results
    agno_round1 = None
    llama_round1 = None
    for service, result in round1_results:
        if service == 'agno':
            agno_round1 = result
        elif service == 'llama':
            llama_round1 = result
    
    print(f"\n--- Agno Round 1 ---\n{agno_round1}\n")
    print(f"\n--- LlamaIndex Round 1 ---\n{llama_round1}\n")
    
    # Round 2: Response to each other
    print("=== Round 2: Cross-Pollination ===")
    
    agno_prompt2 = f"""
    Here's your previous response about "{initial_prompt}":
    {agno_round1}

    Now, here's a technical perspective from another system:
    {llama_round1}

    Please refine your response by:
    1. Incorporating any valuable technical insights you missed
    2. Correcting any inaccuracies in your original response
    3. Maintaining your accessible, creative approach while improving accuracy
    """
    
    llama_prompt2 = f"""
    Here's your previous response about "{initial_prompt}":
    {llama_round1}

    Now, here's a creative perspective from another system:
    {agno_round1}

    Please refine your response by:
    1. Incorporating any valuable insights about clarity and accessibility
    2. Adding any missing nuances or perspectives
    3. Maintaining technical accuracy while improving readability
    """
    
    # Get refined responses in parallel
    agno_task2 = await send_task_to_service(agno_client, agno_prompt2, "Agno")
    llama_task2 = await send_task_to_service(llama_client, llama_prompt2, "LlamaIndex")
    
    # Wait for both to complete in parallel using anyio task group
    round2_results = []
    
    async def collect_agno2():
        result = await wait_for_task_completion(agno_client, agno_task2, "Agno")
        round2_results.append(('agno', result))
    
    async def collect_llama2():
        result = await wait_for_task_completion(llama_client, llama_task2, "LlamaIndex")
        round2_results.append(('llama', result))
    
    async with anyio.create_task_group() as tg:
        tg.start_soon(collect_agno2)
        tg.start_soon(collect_llama2)
    
    # Extract results
    agno_round2 = None
    llama_round2 = None
    for service, result in round2_results:
        if service == 'agno':
            agno_round2 = result
        elif service == 'llama':
            llama_round2 = result
    
    print(f"\n--- Agno Round 2 ---\n{agno_round2}\n")
    print(f"\n--- LlamaIndex Round 2 ---\n{llama_round2}\n")
    
    return agno_round2, llama_round2

async def main():
    initial_question = "Explain the Pauli exclusion principle in one paragraph."
    
    print("Choose workflow type:")
    print("1. Parallel processing with synthesis")
    print("2. Debate/discussion workflow")
    
    # For demo purposes, let's run the parallel workflow
    # In a real scenario, you could add input() here to choose
    workflow_choice = 1
    
    try:
        if workflow_choice == 1:
            final_answer, agno_result, llama_result = await parallel_processing_workflow(initial_question)
            
            print("\n" + "="*60)
            print("PARALLEL WORKFLOW RESULTS")
            print("="*60)
            print("FINAL SYNTHESIZED ANSWER:")
            print(final_answer)
            print("="*60)
            
        elif workflow_choice == 2:
            agno_final, llama_final = await debate_workflow(initial_question)
            
            print("\n" + "="*60)
            print("DEBATE WORKFLOW RESULTS")
            print("="*60)
            print("FINAL AGNO POSITION:")
            print(agno_final)
            print("\nFINAL LLAMAINDEX POSITION:")
            print(llama_final)
            print("="*60)
        
    except Exception as e:
        print(f"[ORCH] Error in workflow: {e}")

if __name__ == "__main__":
    anyio.run(main)
