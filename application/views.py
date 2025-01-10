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
    client = MongoClient("mongodb://3.16.168.145:27017/")
    db = client['MarketPlaceDatabase']  

    db.your_collection_name.insert_one({"key": "value"})
    print("Database and collection created successfully!")
