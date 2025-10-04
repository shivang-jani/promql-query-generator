from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from config import Config
import prompts.promql_query_prompts as query_prompt
from api.internal.prometheus_connector import PrometheusClient
from dashboard.mongo_client import mongo_client
import json
import time
from datetime import datetime

# Initialize router, OpenAI client, and Prometheus client
router = APIRouter()
client = OpenAI(api_key=Config.OPENAI_API_KEY)
prometheus_client = PrometheusClient()

# Request body schema
class PromQLRequest(BaseModel):
    query: str

# Request schema for getChartConfig endpoint
class ChartConfigRequest(BaseModel):
    conversationId: str

# Response schema (optional, but good practice)
class PromQLResponse(BaseModel):
    query_prompt: str
    explanation: str

# New response schema for integrated endpoint
class PrometheusDataResponse(BaseModel):
    conversation_id: str
    generated_payload: dict
    prometheus_data: dict
    success: bool
    message: str

# Response schema for getChartConfig endpoint
class ChartConfigResponse(BaseModel):
    conversationId: str
    naturalLanguageQuery: str
    chartConfig: dict
    prometheusData: dict
    timestamp: str

@router.post("/generate-promql", response_model=PromQLResponse)
def generate_promql_endpoint(request: PromQLRequest):
    """
    Generate a PromQL query from natural language.
    Input: { "query": "95th percentile latency for checkout service in last 1h" }
    Output: { "query_prompt": "...", "explanation": "..." }
    """

    # Step 1: Extract natural language query
    natural_language_query = request.query
    
    print(f"[{datetime.now().isoformat()}] OpenAI API Request - generate-promql endpoint")
    print(f"Model: {Config.OPENAI_MODEL_NAME}")
    print(f"User Query: {natural_language_query}")

    # Step 2: Call OpenAI with system + user prompts
    start_time = time.time()
    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL_NAME,
        messages=[
            {"role": "system", "content": query_prompt.SYSTEM_PROMPT},
            {"role": "user", "content": query_prompt.query_template(natural_language_query)}
        ]
    )
    response_time = time.time() - start_time

    # Step 3: Extract PromQL string from LLM output
    promql_query = response.choices[0].message.content.strip()
    
    print(f"[{datetime.now().isoformat()}] OpenAI API Response - generate-promql endpoint")
    print(f"Response Time: {response_time:.2f}s")
    print(f"Tokens Used - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
    print(f"Generated PromQL: {promql_query}")

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
    Output: { "conversation_id": "uuid", "generated_payload": {...}, "prometheus_data": {...}, "success": true, "message": "..." }
    """
    
    # Generate conversation ID
    conversation_id = mongo_client.generate_conversation_id()
    
    try:
        # Step 1: Extract natural language query
        natural_language_query = request.query
        
        print(f"[{datetime.now().isoformat()}] OpenAI API Request - execute-with-data endpoint")
        print(f"Conversation ID: {conversation_id}")
        print(f"Model: {Config.OPENAI_MODEL_NAME}")
        print(f"User Query: {natural_language_query}")

        # Step 2: Call OpenAI to generate complete JSON payload
        start_time = time.time()
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": query_prompt.SYSTEM_PROMPT},
                {"role": "user", "content": query_prompt.query_template(natural_language_query)}
            ]
        )
        response_time = time.time() - start_time

        # Step 3: Parse OpenAI response as JSON
        openai_response = response.choices[0].message.content.strip()
        
        print(f"[{datetime.now().isoformat()}] OpenAI API Response - execute-with-data endpoint")
        print(f"Response Time: {response_time:.2f}s")
        print(f"Tokens Used - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
        print(f"Raw OpenAI Response: {openai_response}")
        
        try:
            payload = json.loads(openai_response)
        except json.JSONDecodeError as e:
            # Store failed interaction in MongoDB
            mongo_client.store_conversation(
                conversation_id=conversation_id,
                natural_language_query=natural_language_query,
                generated_payload={},
                prometheus_data={},
                success_status=400,
                chart_config={}
            )
            raise HTTPException(
                status_code=400, 
                detail=f"OpenAI returned invalid JSON: {str(e)}"
            )

        # Step 4: Validate payload structure
        required_fields = ["prometheusQuery", "start", "end", "step", "chartConfig"]
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            # Store failed interaction in MongoDB
            mongo_client.store_conversation(
                conversation_id=conversation_id,
                natural_language_query=natural_language_query,
                generated_payload=payload,
                chart_config={},
                prometheus_data={},
                success_status=400
            )
            raise HTTPException(
                status_code=400,
                detail=f"Generated payload missing required fields: {missing_fields}"
            )

        # Step 4.5: Extract chartConfig and prometheus payload
        chart_config = payload.pop("chartConfig", {})
        prometheus_payload = {
            "prometheusQuery": payload["prometheusQuery"],
            "start": payload["start"],
            "end": payload["end"],
            "step": payload["step"]
        }

        # Step 5: Call Prometheus connector with prometheus payload only
        prometheus_data = prometheus_client.fetch_prometheus_data(prometheus_payload, conversation_id)

        # Step 6: Store successful interaction in MongoDB
        mongo_client.store_conversation(
            conversation_id=conversation_id,
            natural_language_query=natural_language_query,
            generated_payload=prometheus_payload,
            chart_config=chart_config,
            prometheus_data=prometheus_data,
            success_status=200
        )

        # Step 7: Return combined response
        return PrometheusDataResponse(
            conversation_id=conversation_id,
            generated_payload=payload,
            prometheus_data=prometheus_data,
            success=True,
            message=f"Successfully executed query for: {natural_language_query}"
        )

    except RuntimeError as e:
        # Store failed interaction in MongoDB
        mongo_client.store_conversation(
            conversation_id=conversation_id,
            natural_language_query=natural_language_query,
            generated_payload=payload if 'payload' in locals() else {},
            prometheus_data={},
            success_status=502,
            chart_config={}
        )
        # Prometheus connector error
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        # Store failed interaction in MongoDB
        mongo_client.store_conversation(
            conversation_id=conversation_id,
            natural_language_query=natural_language_query,
            generated_payload=payload if 'payload' in locals() else {},
            prometheus_data={},
            success_status=500,
            chart_config={}
        )
        # General error
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/promQL-query-generator/v1/getChartConfig", response_model=ChartConfigResponse)
def get_chart_config(request: ChartConfigRequest):
    """
    Retrieve stored conversation data by conversation ID.
    Input: { "conversationId": "uuid-string" }
    Output: Complete stored conversation data from MongoDB
    """
    
    try:
        # Validate UUID format
        conversation_id = request.conversationId.strip()
        if not conversation_id:
            raise HTTPException(
                status_code=400,
                detail="conversationId cannot be empty"
            )
        
        # Retrieve conversation data from MongoDB
        conversation_data = mongo_client.get_conversation(conversation_id)
        
        if conversation_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        
        # Return the stored conversation data
        return ChartConfigResponse(
            conversationId=conversation_data["conversationId"],
            naturalLanguageQuery=conversation_data["naturalLanguageQuery"],
            chartConfig=conversation_data.get("chartConfig", {}),
            prometheusData=conversation_data["prometheusData"],
            timestamp=conversation_data["timestamp"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving conversation: {str(e)}"
        )
