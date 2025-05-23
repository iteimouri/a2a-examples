from __future__ import annotations
import os, anyio, traceback
from fasta2a.worker import Worker
from fasta2a.schema import Artifact
from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from config import get_azure_config


def build_model() -> AzureOpenAI:
    """Azure GPT-4o model for Agno."""
    azure_config = get_azure_config()
    return AzureOpenAI( 
        id=azure_config['azure_deployment'],
        azure_deployment=azure_config['azure_deployment'],
        azure_endpoint=azure_config['azure_endpoint'],
        api_key=azure_config['api_key'], 
        api_version=azure_config['api_version'],
        temperature=azure_config['temperature'],
    )


class AgnoWorker(Worker):
    def __init__(self, *, broker, storage):
        super().__init__(broker=broker, storage=storage)
        self.agent = Agent(model=build_model(), markdown=True)

    # ---------- A2A hooks ----------
    async def run_task(self, params):
        task_id = params["id"]
        prompt = next(p["text"] for p in params["message"]["parts"]
                      if p["type"] == "text")

        print(f"[AGNO] run_task → {task_id!s}  prompt='{prompt[:60]}…'")
        await self.storage.update_task(task_id, state="working")

        try:
            response = await self.agent.arun(prompt)
            
            # Extract text from RunResponse object
            if hasattr(response, 'text'):
                answer = response.text
            elif hasattr(response, 'content'):
                answer = response.content
            elif hasattr(response, 'message'):
                answer = str(response.message)
            else:
                answer = str(response)
                
        except Exception as e:
            traceback.print_exc()
            await self.storage.update_task(task_id, state="failed")
            return

        await self.storage.update_task(
            task_id,
            state="completed",
            artifacts=[{
                "index": 0,
                "parts": [{"type": "text", "text": answer}],
                "lastChunk": True,
            }],
        )

    async def cancel_task(self, params):
        await self.storage.update_task(params["id"], state="canceled")

    def build_message_history(self, task_history): return task_history
    def build_artifacts(self, result): return []