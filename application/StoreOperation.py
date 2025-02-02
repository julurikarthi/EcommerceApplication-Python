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
            print(data)
            store_name = data.get('store_name')
            store_type = data.get('store_type')
            image_id = data.get('image_id')
            user_id = data.get('user_id')
            tax_percentage = data.get('tax_percentage')
            street = data.get('street')
            city = data.get('city')
            pincode = data.get('pincode')
            state = data.get("state")
            currencycode = data.get("currencycode", None)
            serviceType = data.get('serviceType', [])

            # Validate required fields
            if not city or not store_name or not store_type or not image_id or not user_id or not pincode or not tax_percentage or not serviceType or not state or not currencycode or not street:
                return JsonResponse({
                    "error": "All fields ('store_name', 'store_type', 'image_id', 'user_id', 'pincode', 'serviceType', 'tax_percentage', 'state', 'currencycode', 'street', 'city') are required."
                }, status=400)
            # Check if the user has storeOwner userType
            user = db['users'].find_one({"_id": ObjectId(user_id)})
            print(user)
            if not user or user.get('userType') != 'storeOwner':
                return JsonResponse({"error": "User must have 'storeOwner' userType to create a store."}, status=400)      

            # Ensure the user does not already have a store
            existing_store = db['Stores'].find_one({"user_id": user_id})
            if existing_store:
                return JsonResponse({"error": "User already has an existing store. One user can only have one store."}, status=400)
            
            # Validate that store_type is one of the valid types
            valid_store_types = self.getStoreTypes()  # Call the getStoreTypes method
            if store_type not in valid_store_types:
                return JsonResponse({"error": f"Invalid store type. Valid types are: {', '.join(valid_store_types)}"}, status=400)
            
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
                "user_id": user_id,
                "address": address,
                "pincode": pincode,
                "state": state,
                "tax_percentage": tax_percentage,
                "serviceType": serviceType,
                "currencycode": currencycode,
                "street": street,
                "city": city
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
            
            return Response({"message": "Image uploaded successfully.", "file_name": file_name}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete_image(self, data):
        """
        Delete a single image from the Amazon S3 bucket.
        """
        try:
            file_name = data["file_name"]
            if not file_name:
                return Response({"error": "File name is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete the image from S3
            file_path = file_name.strip()
            default_storage.delete(file_path)
            return Response({"message": "Image deleted successfully."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete_all_images(self):
        """
        Delete all images stored in the S3 bucket using default_storage.
        """
        try:
            # List all files from storage
            files = default_storage.listdir("")  # Returns (directories, files)
            file_list = files[1]  # files[1] contains the list of file names

            if not file_list:
                return Response({"message": "No images found."}, status=status.HTTP_200_OK)

            # Delete each file
            for file_name in file_list:
                default_storage.delete(file_name)

            return Response({"message": "All images deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

    def createOffer(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Extract required fields
            offer_description = data.get("offerDescription")
            store_id = data.get("store_id")
            image_id = data.get("image_id")

            # Validate inputs
            if not all([offer_description, store_id, image_id]):
                return JsonResponse({"error": "All fields ('offerDescription', 'store_id', 'image_id') are required."}, status=400)

            if not ObjectId.is_valid(store_id):
                return JsonResponse({"error": "Invalid store_id format."}, status=400)

            # Validate store existence
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Store not found."}, status=404)

            # Create the offer document
            offer_data = {
                "store_id": store_id,
                "offerDescription": offer_description,
                "image_id": image_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Insert into database
            result = db['Offers'].insert_one(offer_data)

            return JsonResponse({
                "message": "Offer created successfully.",
                "offer_id": str(result.inserted_id),
                "store_id": store_id,
                "offerDescription": offer_description,
                "image_id": image_id
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
    
    def getStoreOffers(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Query to filter offers by store_id if provided
            query = {}
            store_id = data.get("store_id")
            if store_id:
                if not ObjectId.is_valid(store_id):
                    return JsonResponse({"error": "Invalid store_id format."}, status=400)
                query["store_id"] = store_id

            # Pagination logic
            page = int(data.get("page", 1))  # Default to page 1 if not provided
            limit = 30
            skip = (page - 1) * limit

            # Fetch paginated offers from the database
            offers = list(db['Offers'].find(query).skip(skip).limit(limit))

            # Format the offers for JSON serialization
            formatted_offers = []
            for offer in offers:
                formatted_offers.append({
                    "offer_id": str(offer["_id"]),
                    "store_id": str(offer["store_id"]),
                    "offerDescription": offer.get("offerDescription"),
                    "image_id": str(offer["image_id"]),
                    "created_at": offer.get("created_at", None),
                    "updated_at": offer.get("updated_at", None),
                })

            # Return the list of offers
            return JsonResponse({"offers": formatted_offers}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def getAllOffers(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Pagination logic
            page = int(data.get("page", 1))  # Default to page 1 if not provided
            limit = 30  # Default limit of 30 offers per page
            skip = (page - 1) * limit

            # Fetch paginated offers from the database
            offers = list(db['Offers'].find().skip(skip).limit(limit))

            # Format the offers for JSON serialization
            formatted_offers = []
            for offer in offers:
                formatted_offers.append({
                    "offer_id": str(offer["_id"]),
                    "store_id": str(offer["store_id"]),
                    "offerDescription": offer.get("offerDescription"),
                    "image_id": str(offer["image_id"]),
                    "created_at": offer.get("created_at", None),
                    "updated_at": offer.get("updated_at", None),
                })

            # Return the list of offers
            return JsonResponse({"offers": formatted_offers}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        
    
    def getOffersByStore(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Get the store_id from the request data
            store_id = data.get("store_id")
            if not store_id:
                return JsonResponse({"error": "store_id is required."}, status=400)

            # Pagination logic
            page = int(data.get("page", 1))  # Default to page 1 if not provided
            limit = 30  # Default limit of 30 offers per page
            skip = (page - 1) * limit

            # Fetch paginated offers from the database filtered by store_id
            offers = list(db['Offers'].find({"store_id": store_id}).skip(skip).limit(limit))

            # Format the offers for JSON serialization
            formatted_offers = []
            for offer in offers:
                formatted_offers.append({
                    "offer_id": str(offer["_id"]),
                    "store_id": str(offer["store_id"]),
                    "offerDescription": offer.get("offerDescription"),
                    "image_id": str(offer["image_id"]),
                    "created_at": offer.get("created_at", None),
                    "updated_at": offer.get("updated_at", None),
                })

            # Return the list of offers
            return JsonResponse({"offers": formatted_offers}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

        

    def deleteOffer(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Extract offer_id from the request data
            offer_id = data.get("offer_id")
            if not offer_id:
                return JsonResponse({"error": "Offer ID is required."}, status=400)

            # Validate the format of offer_id
            if not ObjectId.is_valid(offer_id):
                return JsonResponse({"error": "Invalid Offer ID format."}, status=400)

            # Check if the offer exists
            offer = db['Offers'].find_one({"_id": ObjectId(offer_id)})
            if not offer:
                return JsonResponse({"error": "Offer not found."}, status=404)

            # Delete the offer
            db['Offers'].delete_one({"_id": ObjectId(offer_id)})

            # Return a success response
            return JsonResponse({"message": "Offer deleted successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def getDashboardData(self, data, db=None):

        return self.getAllStoresWithProducts(data=data, db=db)

    def getAllStoresWithProducts(self, data, db=None):
        try:
            if db is None:
                raise ValueError("Database connection is required.")

            pincode = data.get("pincode")
            state = data.get("state")
            page = int(data.get("page", 1))
            limit = 20
            skip = (page - 1) * limit

            query = {}

            if pincode:
                query["pincode"] = pincode
                stores = list(db['Stores'].find(query).skip(skip).limit(limit))
                if not stores and state:
                    query = {"state": state}
                    stores = list(db['Stores'].find(query).skip(skip).limit(limit))
            else:
                query = {"state": state}
                stores = list(db['Stores'].find(query).skip(skip).limit(limit))

            formatted_stores = []
            
            for store in stores:
                store_id = str(store["_id"])
                products = list(db['Products'].find({"store_id": store_id}))
                print("products", products)
                # Only include stores that have products
                if products:
                    formatted_stores.append({
                        "store_id": store_id,
                        "store_name": store.get("store_name"),
                        "store_type": store.get("store_type"),
                        "pincode": store.get("pincode"),
                        "state": store.get("state"),
                        "image_id": store.get("image_id"),
                        "customer_id": store.get("customer_id"),
                        "tax_percentage": store.get("tax_percentage"),
                        "service_type": store.get("serviceType"),
                        "address": store.get("address"),
                        "street": store.get("street"),
                        "city": store.get("city"),
                        "created_at": store.get("created_at"),
                        "updated_at": store.get("updated_at"),
                        "products": self.convert_objectid_to_str(products)
                    })

            return JsonResponse({
                "stores": formatted_stores,
                "page": page,
                "total_stores": len(formatted_stores)
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
    
    def convert_objectid_to_str(self,products):
        return [{**product, "_id": str(product["_id"])} for product in products]








