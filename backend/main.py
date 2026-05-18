import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import jobs, notion_routes

app = FastAPI(title="Job Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api")
app.include_router(notion_routes.router, prefix="/api")


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
