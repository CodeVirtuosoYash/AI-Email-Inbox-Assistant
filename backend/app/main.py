from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.routers import dashboard, messages, replies, summarize, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inbox Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summarize.router)
app.include_router(dashboard.router)
app.include_router(tasks.router)
app.include_router(messages.router)
app.include_router(replies.router)


@app.get("/health")
def health():
    return {"status": "ok"}
