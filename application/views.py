from pymongo import MongoClient
from django.http import JsonResponse
from pymongo.errors import ConnectionFailure
def data_view(request):
    # Intentionally raise an error to simulate a crash
    return JsonResponse({
        "message": "start the project newele",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })

def createDatabase(request):
    try:
        # MongoDB client with a timeout setting
        client = MongoClient("mongodb://18.188.42.21:27017/", serverSelectionTimeoutMS=5000)
        
        # Attempt to check the connection
        client.server_info()  # This will throw an exception if unable to connect

        db = client['MarketPlaceDatabase']  

        # Create a collection and insert a document
        collection = db['UsersData']  # Access the collection (it will be created if it doesn't exist)
        collection.insert_one({"one": "value"})

        return JsonResponse({"message": "Database and collection created successfully!"}, status=200)

    except ConnectionFailure as e:
        return JsonResponse({"error": f"Could not connect to MongoDB: {str(e)}"}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    