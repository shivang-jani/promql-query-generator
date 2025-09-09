SYSTEM_PROMPT = """
You are an expert in Prometheus and PromQL.
- Always follow PromQL best practices.
- For counters, use rate().
- For latency, use histogram_quantile().
- Return clean PromQL queries without extra text.
"""

def query_template(description: str) -> str:
    return f"Generate a PromQL query for: {description}"

def explain_template(query: str) -> str:
    return f"Explain this PromQL query in simple terms: {query}"
