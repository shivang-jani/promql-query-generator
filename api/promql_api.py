from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from config import Config
import prompts.promql_query_prompts as query_prompt

# Initialize router and OpenAI client
router = APIRouter()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Request body schema
class PromQLRequest(BaseModel):
    query: str

# Response schema (optional, but good practice)
class PromQLResponse(BaseModel):
    query_prompt: str
    explanation: str

@router.post("/generate-promql", response_model=PromQLResponse)
def generate_promql_endpoint(request: PromQLRequest):
    """
    Generate a PromQL query from natural language.
    Input: { "query": "95th percentile latency for checkout service in last 1h" }
    Output: { "query_prompt": "...", "explanation": "..." }
    """

    # Step 1: Extract natural language query
    natural_language_query = request.query

    # Step 2: Call OpenAI with system + user prompts
    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL_NAME,
        messages=[
            {"role": "system", "content": query_prompt.SYSTEM_PROMPT},
            {"role": "user", "content": query_prompt.query_template(natural_language_query)}
        ]
    )

    # Step 3: Extract PromQL string from LLM output
    promql_query = response.choices[0].message.content.strip()

    # Step 4: Return structured response
    return PromQLResponse(
        query_prompt=promql_query,
        explanation=f"Generated PromQL for request: {natural_language_query}"
    )
