from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from config import Config
import prompts.promql_query_prompts as query_prompt
from api.internal.prometheus_connector import PrometheusClient
import json

# Initialize router, OpenAI client, and Prometheus client
router = APIRouter()
client = OpenAI(api_key=Config.OPENAI_API_KEY)
prometheus_client = PrometheusClient()

# Request body schema
class PromQLRequest(BaseModel):
    query: str

# Response schema (optional, but good practice)
class PromQLResponse(BaseModel):
    query_prompt: str
    explanation: str

# New response schema for integrated endpoint
class PrometheusDataResponse(BaseModel):
    generated_payload: dict
    prometheus_data: dict
    success: bool
    message: str

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

@router.post("/execute-with-data", response_model=PrometheusDataResponse)
def execute_promql_with_data(request: PromQLRequest):
    """
    Generate a PromQL query from natural language and execute it against Prometheus.
    Input: { "query": "network packets received rate by instance in last 5 minutes" }
    Output: { "generated_payload": {...}, "prometheus_data": {...}, "success": true, "message": "..." }
    """
    
    try:
        # Step 1: Extract natural language query
        natural_language_query = request.query

        # Step 2: Call OpenAI to generate complete JSON payload
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": query_prompt.SYSTEM_PROMPT},
                {"role": "user", "content": query_prompt.query_template(natural_language_query)}
            ]
        )

        # Step 3: Parse OpenAI response as JSON
        openai_response = response.choices[0].message.content.strip()
        
        try:
            payload = json.loads(openai_response)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, 
                detail=f"OpenAI returned invalid JSON: {str(e)}"
            )

        # Step 4: Validate payload structure
        required_fields = ["prometheusQuery", "start", "end", "step"]
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Generated payload missing required fields: {missing_fields}"
            )

        # Step 5: Call Prometheus connector with generated payload
        prometheus_data = prometheus_client.fetch_prometheus_data(payload)

        # Step 6: Return combined response
        return PrometheusDataResponse(
            generated_payload=payload,
            prometheus_data=prometheus_data,
            success=True,
            message=f"Successfully executed query for: {natural_language_query}"
        )

    except RuntimeError as e:
        # Prometheus connector error
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        # General error
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
