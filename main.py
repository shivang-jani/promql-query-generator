import uvicorn
from fastapi import FastAPI
from api.promql_api import router as promql_router

# Initialize FastAPI app
app = FastAPI(
    title="PromQL Query Generator API",
    version="0.1.0",
    description="Generate PromQL queries from natural language using OpenAI"
)

# Register routers
app.include_router(promql_router, prefix="/api/promql", tags=["PromQL"])

# Run the server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
