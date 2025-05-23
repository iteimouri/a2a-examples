# Overview

This repository demonstrates a multi-agent architecture built with the FastA2A framework. The design consists of different worker implementations and service servers that handle tasks asynchronously. There are also several orchestrator examples which coordinate the work of different agents (or services) to produce a final result.

## Workers and Servers

### Workers

Workers are Python classes that inherit from a shared `Worker` base class (from the `fasta2a` package). They are responsible for:

- **Task Execution**:  
  Each worker implements a `run_task` method. This method:
  - Retrieves a prompt from incoming task parameters.
  - Updates the task state (e.g., setting it to "working" and later to "completed", "failed", or "canceled").
  - Uses an underlying AI model (in our examples based on an Azure GPT-4o model) to process the incoming prompt and generate a response.
  - Extracts the response text from the model’s output and writes the result back as an artifact.

There are two main worker implementations in this repository:
- **AgnoWorker (`agno_worker.py`)**:  
  Uses an `Agent` from the Agno package to produce a creative synthesis. It is intended for tasks where a more engaging or creative response is required.
  
- **LlamaIndexWorker (`llamaindex_worker.py`)**:  
  Uses LlamaIndex with a dedicated AzureOpenAI model to provide factual and detailed responses. This worker is optimized for retrieval-augmented generation (RAG) and fact-based analysis.

### Servers

The workers are hosted as service endpoints. For example, in `serve_agno.py`:
- A FastA2A application is created which integrates the AgnoWorker.  
- The server is run using Uvicorn, making the Agno service available via HTTP.
- The underlying components such as the in-memory broker and storage are used to simulate task distribution and status updates in a lightweight fashion.

In a typical deployment, multiple services (each hosting different workers) can interact via HTTP endpoints. Clients (or orchestrators) can send tasks to these endpoints, and workers will run them asynchronously, update their status, and eventually return the results via the FastA2A framework.

## Orchestrator Examples

Several orchestration scripts in the repository demonstrate different workflow patterns where multiple services cooperate to solve a single task. Here’s a brief description of each:

### 1. `orchestrate.py`

- **Purpose**:  
  This script demonstrates a sequential, multi-phase workflow:
  - **Step 1**: It sends an initial analysis request to the LlamaIndex service (RAG-enhanced factual analysis).
  - **Step 2**: It passes the analysis to the Agno service for creative synthesis.
  - **Step 3**: The output from Agno is then re-checked by LlamaIndex for validation.
  - **Step 4**: Finally, Agno produces the definitive answer by incorporating validation feedback.

- **Key Idea**:  
  The orchestration shows how the two services (creative synthesis and factual validation) can be combined to produce an answer that is both engaging and factually accurate.

### 2. `orchestrate_expert.py`

- **Purpose**:  
  This example guides a more sophisticated multi-round interaction:
  - **Phase 1 (Research)**: LlamaIndex acts as a research specialist to provide a comprehensive technical analysis.
  - **Phase 2 (Communication Strategy)**: The Agno service develops a communication strategy based on the research.
  - **Phase 3 (Review)**: LlamaIndex reviews the proposed strategy, checking for technical accuracy.
  - **Phase 4 (Final Explanation)**: Agno synthesizes the final explanation, incorporating feedback.
  - **Phase 5 (Fact-Check)**: A final validation round is executed using LlamaIndex.

- **Key Idea**:  
  This example simulates a collaborative workflow where expert consultation is modeled through several rounds of discussion between a "research specialist" and a "communication expert".

### 3. `orchestrate_parallel.py`

- **Purpose**:  
  This script shows how to process the same prompt in parallel using both services:
  - Tasks are sent in parallel to both Agno and LlamaIndex.
  - After both responses are received, the Agno service is used to synthesize a final unified answer.
  - An alternate debate workflow is also available where the two services exchange perspectives and refine their responses in rounds.

- **Key Idea**:  
  The parallel workflow demonstrates efficient concurrent processing and synthesis, as well as a debate scenario that leverages the strengths of each system.

## How to Run

Below are example commands to run the various components on the command line. Make sure you are in the repository root directory and have all required dependencies installed.

### Running the Agno Service (Server)

Use the following command to start the Agno server:

```bash
python FastA2A-Agno-Llamaindex/serve_agno.py
```

This command starts the FastA2A application with the AgnoWorker running on the configured port.

### Running the Orchestrator Examples

Each orchestrator script is self-contained. You can run them directly:

1. **Sequential Orchestration Example:**

   ```bash
   python FastA2A-Agno-Llamaindex/orchestrate.py
   ```

2. **Expert Consultation Workflow:**

   ```bash
   python FastA2A-Agno-Llamaindex/orchestrate_expert.py
   ```

3. **Parallel Processing and Debate Workflow:**

   ```bash
   python FastA2A-Agno-Llamaindex/orchestrate_parallel.py
   ```

Each orchestrator script will interact with the running worker services (or use in-memory simulated brokers and storage) to send tasks, wait for results, and print out the final synthesized answer.

----

This architecture shows how individual workers with distinct strengths can be combined using orchestrators to produce collaborative and robust responses, blending creative synthesis with factual validation.
