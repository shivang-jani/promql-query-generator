import requests 
from config import Config


class PrometheusClient:
    def __init__(self):
        self.base_url = Config.PROMETHEUS_CONNECTOR_URL

    def fetch_prometheus_data(self, payload: dict, conversation_id: str = None):
        """
        Calls the internal Prometheus connector API with the given payload.

        Args:
            payload (dict): Dictionary containing at least:
                            - prometheusQuery
                            - start
                            - end
                            - step
            conversation_id (str): Optional conversation ID to include in the payload

        Returns:
            dict: Response JSON from Prometheus connector API

        Raises:
            RuntimeError: If request fails or returns non-2xx response
        """
        url = f"{self.base_url}/prometheusData"

        # Add conversationId to payload if provided
        if conversation_id:
            payload["conversationId"] = conversation_id

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch data from Prometheus connector: {e}")
