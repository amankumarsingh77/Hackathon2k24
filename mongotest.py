from pymongo import MongoClient
import time

uri = "mongodb+srv://amankumar77:3lS1UV4CTetpHFFZ@hackathon.q7vys.mongodb.net/?retryWrites=true&w=majority&appName=hackathon"
client = MongoClient(uri)


database = client["sample_mflix"]
collection = database["embedded_movies"]


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



















print("Polling to check if the index is ready. This may take up to a minute.")
predicate = lambda index: index.get("status") == "READY"

while True:
    
    indices = list(collection.list_indexes())
    print(indices)
    index_info = next((idx for idx in indices if idx.get("name") == "vector_index"), None)

    if index_info and predicate(index_info):
        print(f"Index 'vector_index' is ready for querying.")
        break

    time.sleep(5)

client.close()
