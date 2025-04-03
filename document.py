from flask import Flask, request, jsonify
import openai
import pymongo
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearchAlgorithmConfiguration,
)
from pymongo import MongoClient
import urllib.parse

app = Flask(__name__)

# Azure Cognitive Search configuration
search_service_endpoint = "AZURE_COGNITIVE_SERVICE_ENDPOINT"
search_service_key = "AZURE_COGNITIVE_SERVICE_ADMIN_KEY"
index_name = "AZURE_SEARCH_SERIVE_CLUSTER_INDEX_NAME"

# Initialize Azure Cognitive Search client
index_client = SearchIndexClient(
    endpoint=search_service_endpoint, credential=AzureKeyCredential(search_service_key)
)

# Initialize OpenAI API
openai.api_key = "AZURE_OPENAI_API_KEY"

# Connect to MongoDB
user = "COSMOSDB_USERNAME"
password = "COSMOSDB_PASSWORD"
host = "MONGO_DB_CLUSTER_HOST_LINK"
user = urllib.parse.quote_plus(user)
password = urllib.parse.quote_plus(password)
cosmosdb_connection_string = f"mongodb+srv://{user}:{password}@{host}/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
client = pymongo.MongoClient(cosmosdb_connection_string)
db = client["huggingface_db"]
collection = db["dataset_collection"]


class VectorField:
    def __init__(self, name, field_type, dimensions, vector_search_configuration):
        self.name = name
        self.type = field_type
        self.dimensions = dimensions
        self.vector_search_configuration = vector_search_configuration

    def _to_generated(self):
        return {
            "name": self.name,
            "type": self.type,
            "dimensions": self.dimensions,
            "vector_search_configuration": {
                "name": self.vector_search_configuration.name
            },
        }


index = SearchIndex(
    name=index_name,
    fields=[
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="content", type="Edm.String"),
        VectorField(
            name="embedding",
            field_type="Collection(Edm.Single)",
            dimensions=1536,
            vector_search_configuration=VectorSearchAlgorithmConfiguration(
                name="my-vector-algorithm"
            ),
        ),
    ],
)


@app.route("/vector_search", methods=["POST"])
def vector_search():
    try:
        query = request.json["query"]
        response = openai.Embedding.create(input=query, engine="text-embedding-ada-002")
        query_embedding = response["data"][0]["embedding"]

        search_client = SearchClient(
            endpoint=search_service_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(search_service_key),
        )
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


if __name__ == "__main__":
    app.run(debug=True)
