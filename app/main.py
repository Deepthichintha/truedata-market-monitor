from fastapi import FastAPI

app = FastAPI(
    title="TrueData Market Monitor",
    description="Real-time stock monitoring POC using TrueData APIs",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "truedata-market-monitor",
    }
