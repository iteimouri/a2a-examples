from __future__ import annotations

import os
import anyio
import traceback

from fasta2a.worker import Worker
from llama_index.llms.azure_openai import AzureOpenAI
from config import get_llamaindex_config


def build_llm() -> AzureOpenAI:
    """Return an Azure GPT-4o LLM configured for LlamaIndex."""
    config = get_llamaindex_config()
    return AzureOpenAI(
        deployment_name=config['deployment_name'],
        model=config['model'],
        azure_endpoint=config['azure_endpoint'],
        api_key=config['api_key'],
        api_version=config['api_version'],
    )


class LlamaIndexWorker(Worker):
    def __init__(self, *, broker, storage):
        super().__init__(broker=broker, storage=storage)
        self.llm = build_llm()

    # ---------- A2A hooks ----------
    async def run_task(self, params):
        task_id = params["id"]
        prompt = next(
            p["text"] for p in params["message"]["parts"] if p["type"] == "text"
        )

        print(f"[LLI]  run_task → {task_id}  prompt='{prompt[:60]}…'")
        await self.storage.update_task(task_id, state="working")

        try:
            # AzureOpenAI.complete is synchronous → run it in a thread
            completion = await anyio.to_thread.run_sync(self.llm.complete, prompt)

            # Llama-Index returns a CompletionResponse object — extract the string
            answer = getattr(completion, "text", completion)

        except Exception:
            traceback.print_exc()
            await self.storage.update_task(task_id, state="failed")
            return

        await self.storage.update_task(
            task_id,
            state="completed",
            artifacts=[
                {
                    "index": 0,
                    "parts": [{"type": "text", "text": answer}],
                    "lastChunk": True,
                }
            ],
        )

    async def cancel_task(self, params):
        await self.storage.update_task(params["id"], state="canceled")

    def build_message_history(self, task_history):
        return task_history

    def build_artifacts(self, result):
        return []