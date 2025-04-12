import requests
from flask import current_app

def get_available_models():
    # Use the configured tags endpoint; default to localhost if not set.
    url = current_app.config.get("OLLAMA_TAGS_URL", "http://localhost:11434/api/tags")
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        # Return the list found under the "models" key
        return data.get("models", [])
    except Exception as e:
        current_app.logger.error("Error retrieving models: %s", e)
        # Fallback default model list
        return [{"name": "llama3.2"}, {"name": "llama3:latest"}, {"name": "orca-mini:3b-q4_1"}]

def get_chat_response(message_history, model="llama3.2"):
    """
    Get a chat response by sending the conversation history to the Ollama chat API.
    `message_history` should be a list of dictionaries with keys 'role' and 'content'.
    """
    url = current_app.config["OLLAMA_API_URL"]
    payload = {
        "model": model,
        "messages": message_history,
        "stream": False  # Change this to True if you want to process a streaming response.
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    # The expected response contains a "message" field with the assistant's reply.
    result = response.json()
    return result["message"]["content"]
