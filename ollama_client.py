import requests
from flask import current_app
import json

def get_available_models():
    url = current_app.config.get("OLLAMA_TAGS_URL", "http://localhost:11434/api/tags")
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])
    except Exception as e:
        current_app.logger.error("Error retrieving models: %s", e)
        return [{"name": "llama3.2"}, {"name": "llama3:latest"}, {"name": "orca-mini:3b-q4_1"}]

def get_chat_response(message_history, model="llama3.2", context=None):
    url = current_app.config["OLLAMA_API_URL"]
    payload = {
        "model": model,
        "messages": message_history,
        "stream": False
    }
    if context:
        # If context is a JSON string, convert it back to a Python structure.
        try:
            context_data = json.loads(context) if isinstance(context, str) else context
        except Exception:
            context_data = context
        payload["context"] = context_data
    response = requests.post(url, json=payload)
    response.raise_for_status()
    result = response.json()
    reply = result["message"]["content"]
    new_context = result.get("context")
    return reply, new_context
