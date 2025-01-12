from pymongo import MongoClient
from django.http import JsonResponse
from pymongo.errors import ConnectionFailure
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import boto3
from botocore.exceptions import NoCredentialsError
from django.core.files.storage import default_storage

MONGODB_CONNECTION_STRING = "mongodb://18.188.42.21:27017/"

def data_view(request):
    return HttpResponse("Hello, world!")

@csrf_exempt
def createStore(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body from the request
            data = json.loads(request.body)
            
            # Validate the required fields
            store_name = data.get('store_name')
            store_type = data.get('store_type')
            image_id = data.get('image_id')
            customer_id = data.get('customer_id')
            
            if not store_name or not store_type or not image_id:
                return JsonResponse({"error": "Both 'store_name' and 'store_type' and 'image_id' are required."}, status=400)
            
            # Optional field: address
            address = data.get('address', None)
            
            # Get the database instance
            db = getDatabase()
            
            # Insert the store data into the 'Stores' collection
            store_data = {
                "store_name": store_name,
                "store_type": store_type,
                "image_id": image_id,
                "customer_id": customer_id,
                "address": address,
            }
            collection = db['Stores']
            result = collection.insert_one(store_data)
            
            return JsonResponse({"message": "Store created successfully!", "store_id": str(result.inserted_id)}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)
    

def getStoreTypes():
    storeType = ["Grocery", "Fashion", "Restaurants"]
    return storeType

def getDatabase():
    """
    Returns the 'MarketPlaceDatabase' database object after ensuring a successful connection.
    
    Raises:
        ConnectionFailure: If unable to connect to MongoDB.
    """
    try:
        # MongoDB client with a timeout setting
        client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
        db = client['MarketPlaceDatabase']
        
        # Attempt to check the connection
        client.server_info()  # This will throw an exception if unable to connect
        
        return db
    except ConnectionFailure as e:
        raise ConnectionFailure(f"Could not connect to MongoDB: {str(e)}")
    
@csrf_exempt
def uploadImage(request):
    if request.method == 'POST':
        try:
            # Check if file is in the request
            if 'image' not in request.FILES:
                return JsonResponse({"error": "No image file found in the request."}, status=400)
            
            # Get the file from the request
            image_file = request.FILES['image']
            
            # Save the file using the default storage backend (S3 in this case)
            file_path = default_storage.save(image_file.name, image_file)
            
            # Get the URL for accessing the uploaded file
            file_url = default_storage.url(file_path)
            
            # Return the URL of the uploaded image
            return JsonResponse({"message": "Image uploaded successfully.", "url": file_url}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)