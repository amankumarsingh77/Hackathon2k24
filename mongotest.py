from pymongo import MongoClient
import time

# Connect to your MongoDB Atlas deployment
uri = "mongodb+srv://amankumar77:3lS1UV4CTetpHFFZ@hackathon.q7vys.mongodb.net/?retryWrites=true&w=majority&appName=hackathon"
client = MongoClient(uri)

# Access your database and collection
database = client["sample_mflix"]
collection = database["embedded_movies"]

# Define the search index model for Atlas Search
search_index_model = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "plot_embedding": {
                "type": "knnVector",
                "dimensions": 1536,
                "similarity": "euclidean"
            }
        }
    }
}

# Create the Atlas Search index
# try:
#     result = database.command({
#         "createSearchIndexes": "embedded_movies",
#         "indexes": [
#             {
#                 "name": "vector_index",
#                 "definition": search_index_model
#             }
#         ]
#     })
#     print("New search index named 'vector_index' is building.")
# except Exception as e:
#     print(f"Failed to create search index: {e}")
#     client.close()
#     exit(1)

# Polling to check if the index is ready
print("Polling to check if the index is ready. This may take up to a minute.")
predicate = lambda index: index.get("status") == "READY"

while True:
    # Check the status of search indexes by name
    indices = list(collection.list_indexes())
    print(indices)
    index_info = next((idx for idx in indices if idx.get("name") == "vector_index"), None)

    if index_info and predicate(index_info):
        print(f"Index 'vector_index' is ready for querying.")
        break

    time.sleep(5)

client.close()
