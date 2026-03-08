# app/main.py
from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routes import auth

app = FastAPI(
    title="Personal Finance Tracker",
    description="Track income, expenses, and financial summaries",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}