from flask import request, jsonify
import openai
from config import AZURE_OPENAI_API_KEY
from azure_search import get_search_client

# Set OpenAI API Key
openai.api_key = AZURE_OPENAI_API_KEY


def vector_search():
    try:
        query = request.json["query"]
        response = openai.Embedding.create(input=query, engine="text-embedding-ada-002")
        query_embedding = response["data"][0]["embedding"]

        search_client = get_search_client()
        results = search_client.search(
            search_text="",
            vector={
                "field": "embedding",
                "value": query_embedding,
                "k": 5,
            },  # Adjust 'k' as needed
        )

        response_content = [
            result["content"] for result in results if "content" in result
        ]
        return jsonify({"response": response_content})

    except Exception as e:
        return jsonify({"error": str(e)})
