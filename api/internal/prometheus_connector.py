import requests 
from config import Config
import time
from datetime import datetime


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

        print(f"[{datetime.now().isoformat()}] Prometheus Connector API Request")
        print(f"URL: {url}")
        print(f"Conversation ID: {conversation_id}")
        print(f"Payload: {payload}")

        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=10)
            response_time = time.time() - start_time
            
            response.raise_for_status()
            response_data = response.json()
            
            print(f"[{datetime.now().isoformat()}] Prometheus Connector API Response")
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {response_time:.2f}s")
            print(f"Response Size: {len(str(response_data))} characters")
            print(f"Response Data: {response_data}")
            
            return response_data

        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().isoformat()}] Prometheus Connector API Error")
            print(f"Error: {str(e)}")
            print(f"URL: {url}")
            print(f"Payload: {payload}")
            raise RuntimeError(f"Failed to fetch data from Prometheus connector: {e}")
