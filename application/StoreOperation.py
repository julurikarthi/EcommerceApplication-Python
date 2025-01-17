from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 
import json

import uuid
import os
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.http import JsonResponse

class StoreOperation:


    def getStoreTypes(self):
        storeType = ["Grocery", "Fashion", "Restaurants"]
        return storeType
    
    def serviceType(self):
        serviceType = ["Pickup", "Pickup at Pay", "Delivery"]
        return serviceType
    
    def storeDetails(self):
        # Combine the results from getStoreTypes and serviceType
        store_types = self.getStoreTypes()
        service_types = self.serviceType()

        # Return both store types and service types in the response
        return {
            "storeTypes": store_types,
            "serviceTypes": service_types
        }


    def create_Store(self, data, db):
        try: 
            store_name = data.get('store_name')
            store_type = data.get('store_type')
            image_id = data.get('image_id')
            customer_id = data.get('customer_id')
            tax_percentage = data.get('tax_percentage')
            pincode = data.get('pincode')
            serviceType = data.get('serviceType', [])

            # Validate required fields
            if not store_name or not store_type or not image_id or not customer_id or not pincode or not tax_percentage or not serviceType:
                return JsonResponse({"error": "All fields ('store_name', 'store_type', 'image_id', 'customer_id', 'pincode', 'serviceType', 'tax_percentage') are required."}, status=400)

            # Check if the user has storeOwner ueserType
            user = db['users'].find_one({"_id": ObjectId(customer_id)})
            if not user or user.get('ueserType') != 'storeOwner':
                return JsonResponse({"error": "User must have 'storeOwner' ueserType to create a store."}, status=400)      
            
            
            # Validate that store_type is one of the valid types
            valid_store_types = self.getStore_Types()  # Call the getStoreTypes method
            if store_type not in valid_store_types:
                return JsonResponse({"error": f"Invalid store type. Valid types are: {', '.join(valid_store_types)}"}, status=400)
            print(data)
            
            # Validate serviceType to ensure all values are valid
            valid_service_types = self.serviceType()  # Call the serviceType method
            print(valid_service_types)
            for st in serviceType:
                if st not in valid_service_types:
                    return JsonResponse({"error": f"Invalid service type '{st}'. Valid types are: {', '.join(valid_service_types)}"}, status=400)
            # Optional field: address
            address = data.get('address', None)
            
            # Insert the store data into the 'Stores' collection
            store_data = {
                "store_name": store_name,
                "store_type": store_type,
                "image_id": image_id,
                "customer_id": customer_id,
                "address": address,
                "pincode": pincode,
                "tax_percentage": tax_percentage,
                "serviceType": serviceType
            }
            
            collection = db['Stores']
            result = collection.insert_one(store_data)
            
            return JsonResponse({"message": "Store created successfully!", "store_id": str(result.inserted_id)}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


    def createCategory(self, data, db):
        try:
            # Validate inputs
            store_id = data.get("store_id")
            category_name = data.get("category_name")

            if not store_id or not category_name:
                return JsonResponse({"error": "Store ID and Category Name are required."}, status=400)

            # Validate the store existence
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Store not found."}, status=404)

            # Check for duplicate category in the store
            existing_category = db['Categories'].find_one({"store_id": store_id, "category_name": category_name})
            if existing_category:
                return JsonResponse({"error": "Category already exists in this store."}, status=409)

            # Create the category
            category_data = {
                "store_id": store_id,
                "category_name": category_name,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = db['Categories'].insert_one(category_data)

            return JsonResponse({
                "message": "Category created successfully.",
                "category_id": str(result.inserted_id),
                "store_id": store_id,
                "category_name": category_name
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

    def getCategoriesByStore(self, data, db):
        try:
            store_id = data["store_id"]
            # Validate store_id
            if not store_id:
                return JsonResponse({"error": "Store ID is required."}, status=400)

            # Validate store existence
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Store not found."}, status=404)

            # Fetch categories for the store
            categories = db['Categories'].find({"store_id": store_id})

            # Check if categories exist
            if not categories:
                return JsonResponse({"error": "No categories found for this store."}, status=404)

            # Format the categories data
            category_list = []
            for category in categories:
                category_list.append({
                    "category_id": str(category["_id"]),
                    "category_name": category["category_name"],
                    "created_at": category["created_at"],
                    "updated_at": category["updated_at"]
                })

            return JsonResponse({"categories": category_list}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def uploadImage(self, request):
        """
        Custom action to handle image upload via POST request, compressing the image to a maximum of 3MB.
        """
        if 'image' not in request.FILES:
            return Response({"error": "No image file found in the request."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the uploaded image file
            image_file = request.FILES['image']
            
            # Open the image using Pillow
            image = Image.open(image_file)
            
            # Check if the image is not already in RGB mode (PNG images are typically in RGBA)
            if image.mode in ("RGBA", "P"):  # If the image has an alpha channel or palette
                image = image.convert("RGB")  # Convert to RGB for saving as JPEG
            
            # Resize the image (e.g., max width of 800px while maintaining aspect ratio)
            max_width = 800
            if image.width > max_width:
                new_height = int((max_width / image.width) * image.height)
                image = image.resize((max_width, new_height), Image.ANTIALIAS)
            
            # Compress the image (convert to JPEG for better compression)
            compressed_image_io = BytesIO()

            # Check for original image size and compress to meet the 3MB limit
            quality = 85  # Start with a quality of 85% for JPEG
            while True:
                # Save the image as JPEG and check the file size
                image.save(compressed_image_io, format='JPEG', quality=quality)
                compressed_image_io.seek(0)
                
                # Check the size of the compressed image
                if compressed_image_io.getbuffer().nbytes <= 3 * 1024 * 1024:  # 3MB in bytes
                    break
                
                # If the image is still too large, reduce quality by 5%
                quality -= 5
                if quality < 50:  # Prevent the quality from going too low
                    break

            # Save the compressed image to Django's storage backend
            compressed_image_io.seek(0)  # Reset the IO pointer

            # Generate a unique file name for the image
            clean_name = image_file.name.replace(" ", "_")
            clean_name = "".join(c for c in clean_name if c.isalnum() or c in ['_', '.'])
            
            # Use a unique identifier for the file name to ensure uniqueness
            file_extension = "jpg"  # Ensure the extension is 'jpg' after compression
            unique_id = str(uuid.uuid4())
            file_name = f"{unique_id}_{clean_name}.{file_extension}"

            # Save to storage
            file_path = default_storage.save(file_name, ContentFile(compressed_image_io.read()))

            # Get the URL for accessing the uploaded file
            file_url = default_storage.url(file_path)
            
            return Response({"message": "Image uploaded successfully.", "file_name": file_name}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
