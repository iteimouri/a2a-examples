# 🤖 A2A Protocol Examples Repository

## What is A2A?

**A2A (Agent-to-Agent)** is a communication protocol introduced by Google that enables **autonomous agents to interact with each other** through standardized message passing, goal negotiation, and task coordination. Rather than treating agents as isolated LLM wrappers or task-specific bots, A2A enables them to:

- **Exchange structured messages** (intents, plans, results, etc.)
- **Negotiate roles and responsibilities**
- **Form dynamic workflows** through coordination and planning
- **Collaborate asynchronously** on complex objectives

The protocol is inspired by the need for **multi-agent collaboration at scale**—an essential step for complex use cases like automated research, enterprise automation, and multi-modal AI systems.

---

## 📁 About This Repository

This repository gathers **concrete implementations and usage examples** of the A2A protocol across popular agentic AI frameworks. The goal is to **lower the barrier to entry** for developers and researchers looking to adopt A2A in their own systems.

### ✅ Goals
- Provide **plug-and-play examples** of A2A in action
- Demonstrate how to **adapt A2A** for various frameworks
- Highlight **best practices** for multi-agent messaging, intent resolution, and coordination

---

## 📦 Included Frameworks & Examples
🪄 Agno Agents  
📚 LlamaIndex 
🧠 LangGraph 
🛠️ AutoGen
📊 CrewAI  

---

## 🛠️ How It Works

Each example illustrates the **core A2A flow**:

1. **Agent Registration:** Define agents with roles, goals, capabilities.
2. **Intent Messaging:** Agents send/receive intent messages like `"propose_plan"`, `"evaluate_output"`, `"request_input"`.
3. **Coordination:** Agents negotiate or agree on task boundaries (e.g., `"you validate my output"`).
4. **Execution Loop:** Messages are processed and results are passed to the next agent.
5. **Finalization:** Agents may jointly agree on when a task is considered “done”.

---

## 🚀 Getting Started

Simple go to each folder and follow the instructions and explore the examples
