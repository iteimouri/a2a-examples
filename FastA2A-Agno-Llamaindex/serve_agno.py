import uvicorn
from contextlib import asynccontextmanager
from fasta2a import FastA2A
from fasta2a.broker import InMemoryBroker
from fasta2a.storage import InMemoryStorage
from agno_worker import AgnoWorker
from config import config

storage = InMemoryStorage()
broker  = InMemoryBroker()
worker  = AgnoWorker(broker=broker, storage=storage)

@asynccontextmanager
async def lifespan(app):
    async with app.task_manager, worker.run():
        print("[AGNO] worker loop started")
        yield

app = FastA2A(
    storage=storage,
    broker=broker,
    name="Agno GPT-4o Agent",
    version="0.2.0",
    skills=[{
        "id": "general-qa",
        "name": "General Q&A",
        "description": "Answers anything with GPT-4o on Azure",
        "tags": ["qa"],
        "input_modes": ["application/json"],
        "output_modes": ["application/json"],
    }],
    lifespan=lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.AGNO_SERVICE_PORT, log_level="info")