from pymongo import MongoClient
from django.http import JsonResponse
from pymongo.errors import ConnectionFailure
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage


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
            # Check if an image is included in the request
            image_file = request.FILES.get('image')
            if not image_file:
                return JsonResponse({"error": "No image file provided."}, status=400)

            # Save the image to the server
            fs = FileSystemStorage(location='uploads/')  # Customize the path as needed
            filename = fs.save(image_file.name, image_file)
            image_path = fs.url(filename)

            # Save the image reference to MongoDB
            db = getDatabase()
            collection = db['AllImages']
            image_data = {
                "filename": filename,
                "path": image_path
            }
            result = collection.insert_one(image_data)

            return JsonResponse({
                "message": "Image uploaded successfully!",
                "image_id": str(result.inserted_id),
                "image_url": image_path
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)
