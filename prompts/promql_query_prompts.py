SYSTEM_PROMPT = """
You are an expert in Prometheus and PromQL.
- Always follow PromQL best practices.
- For counters, use rate().
- For latency, use histogram_quantile().
- Return ONLY a valid JSON object with the following structure:
{
  "prometheusQuery": "your_promql_query_here",
  "start": "unix_timestamp_string",
  "end": "unix_timestamp_string", 
  "step": "time_interval_like_60s"
}
- Use reasonable default time ranges (e.g., last 1 hour) unless specified.
- Use appropriate step intervals (e.g., 60s for short ranges, 5m for longer ranges).
- Do not include any text outside the JSON object.
"""

def query_template(description: str) -> str:
    return f"Generate a complete Prometheus query payload for: {description}"

def explain_template(query: str) -> str:
    return f"Explain this PromQL query in simple terms: {query}"
