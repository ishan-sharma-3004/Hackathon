from flask import Flask
from vector_search import vector_search

app = Flask(__name__)

# Register route
app.route("/vector_search", methods=["POST"])(vector_search)

if __name__ == "__main__":
    app.run(debug=True)
