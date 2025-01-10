from django.http import JsonResponse, HttpResponseForbidden
from pymongo import MongoClient
def data_view(request):
    # Intentionally raise an error to simulate a crash
    return JsonResponse({
        "message": "start the project newele",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })

def createDatabase(request):
    try:
        client = MongoClient("mongodb://3.16.168.145:27017/")
        db = client['MarketPlaceDatabase']  

        # Create a collection and insert a document
        db.your_collection_name.insert_one({"key": "value"})

        return JsonResponse({"message": "Database and collection created successfully!"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)