"""
BlueBubbles Server Main Application
Entry point for the BlueBubbles messaging server.
"""
import asyncio
from fastapi import FastAPI
from loguru import logger
from .application import create_application

# Create and configure the application
app = create_application()

@app.get("/")
async def root():
    return {"message": "BlueBubbles Server is running"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting BlueBubbles server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)