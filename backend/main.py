from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from api.routes import router
from market_context.market_context import get_market_context

app = FastAPI(
    title="AI Trading System",
    description="AI Powered Adaptive Trading System for Indian Markets",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "AI Trading System is live",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# This is the critical part for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Bind to 0.0.0.0 to accept external requests
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)