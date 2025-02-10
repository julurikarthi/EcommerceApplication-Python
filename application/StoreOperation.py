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
from django.http import FileResponse, HttpResponseRedirect
from PIL import Image
import io

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
    

    def delete_Store(self, data, db):
        try:
            # Validate store_id
            store_id = data.get('store_id')
            if not store_id:
                return JsonResponse({"error": "'store_id' is required."}, status=400)

            # Convert store_id to ObjectId
            try:
                store_id_obj = ObjectId(store_id)
            except Exception:
                return JsonResponse({"error": "Invalid 'store_id' format."}, status=400)

            # Fetch store details
            store = db['Stores'].find_one({"_id": store_id_obj})
            if not store:
                return JsonResponse({"error": "Store not found."}, status=404)

            # Delete all products linked to this store
            product_delete_result = db['Products'].delete_many({"store_id": str(store_id_obj)})

            # Delete the store
            store_delete_result = db['Stores'].delete_one({"_id": store_id_obj})

            if store_delete_result.deleted_count > 0:
                return JsonResponse({
                    "message": "Store and its products deleted successfully!",
                    "deleted_products": product_delete_result.deleted_count
                }, status=200)
            else:
                return JsonResponse({"error": "Failed to delete store."}, status=500)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

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
        

    @action(detail=False, methods=['post'], url_path='uploadImage')
    def uploadImage(self, request):
        try:
            image_file = request.FILES.get("image")  # Get uploaded image
            
            if not image_file:
                return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Open image
            img = Image.open(image_file)

            # Convert RGBA to RGB (Fix transparency issue)
            if img.mode == "RGBA":
                img = img.convert("RGB")

            # Resize image
            max_width = 500
            aspect_ratio = img.height / img.width
            new_height = int(max_width * aspect_ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

            # Save to memory
            img_io = io.BytesIO()
            img.save(img_io, format="JPEG", quality=85)  # Ensure JPEG format
            img_io.seek(0)

            # Generate unique image ID
            unique_id = str(uuid.uuid4())

            # Clean filename and create unique file name
            clean_name = image_file.name.replace(" ", "_")
            clean_name = "".join(c for c in clean_name if c.isalnum() or c in ['_', '.'])
            file_extension = "jpg"
            file_name = f"{unique_id}_{clean_name}.{file_extension}"

            # Save to S3
            default_storage.save(file_name, ContentFile(img_io.read()))

            return Response({"file_name": file_name}, status=status.HTTP_201_CREATED)  # Return only image ID

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

            print("Fetching stores...")

            # Query by pincode or state
            if pincode:
                query["pincode"] = pincode
                stores = list(db['Stores'].find(query))
                print("Stores by pincode:", len(stores))

                # If no stores found in pincode, search by state
                if not stores and state:
                    query = {"state": state}
                    stores = list(db['Stores'].find(query))
                    print("Stores by state:", len(stores))
            else:
                query = {"state": state} if state else {}
                stores = list(db['Stores'].find(query))

            formatted_stores = []
            user_id = data.get("user_id")
            total_cart_products = 0 
            for store in stores:
                store_id = str(store["_id"])
                print("Checking store ID:", store_id)

                # Get only published products for this store
                products = list(db['Products'].find({"store_id": store_id, "isPublish": True}))

                cart_products = {}
               
                if user_id:
                    cart = db['Carts'].find_one({"customer_id": user_id, "store_id": store_id})
                    if cart:
                        total_cart_products = total_cart_products + len(cart.get("products", []))
                        for item in cart.get("products", []):
                            cart_products[item["product_id"]] = {
                                "isAddToCart": True,
                                "quantity": item.get("quantity", 1)
                            }
                for product in products:
                    product_id = str(product["_id"])
                    if product_id in cart_products:
                        product["isAddToCart"] = cart_products[product_id]["isAddToCart"]
                        product["quantity"] = cart_products[product_id]["quantity"]
                    else:
                        product["isAddToCart"] = False
                        product["quantity"] = 0

                # Only include stores that have published products
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

                # Stop once we reach 20 stores
                if len(formatted_stores) >= limit:
                    break

            return JsonResponse({
                "stores": formatted_stores[:limit],  # Ensure only 20 stores are returned
                "page": page,
                "total_stores": len(formatted_stores),
                "total_cart_products": total_cart_products,

            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

    
    def convert_objectid_to_str(self,products):
        return [{**product, "_id": str(product["_id"])} for product in products]

    def get_StoreDetails(self, data, db):
        try:
            # Validate store_id
            store_id = data.get("store_id")
            if not store_id:
                return JsonResponse({"error": "'store_id' is required."}, status=400)

            # Convert store_id to ObjectId
            try:
                store_id_obj = ObjectId(store_id)
            except Exception:
                return JsonResponse({"error": "Invalid 'store_id' format."}, status=400)

            # Fetch store details
            store = db['Stores'].find_one({"_id": store_id_obj}, {"_id": 0})  # Exclude MongoDB _id from response
            if not store:
                return JsonResponse({"error": "Store not found."}, status=404)

            return JsonResponse({"store": store}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
        
    def update_StoreDetails(self, data, db):
        try:
            # Extract store_id
            store_id = data.get('store_id')
            if not store_id:
                return JsonResponse({"error": "'store_id' is required."}, status=400)

            # Convert store_id to ObjectId
            try:
                store_id_obj = ObjectId(store_id)
            except Exception:
                return JsonResponse({"error": "Invalid 'store_id' format."}, status=400)

            # Check if the store exists
            store = db['Stores'].find_one({"_id": store_id_obj})
            if not store:
                return JsonResponse({"error": "Store not found."}, status=404)

            # Allowed fields for updating
            allowed_fields = {
                "store_name", "store_type", "image_id", "tax_percentage",
                "street", "city", "pincode", "state", "currencycode", "serviceType", "address"
            }

            # Prepare update data
            update_data = {key: data[key] for key in allowed_fields if key in data}

            if not update_data:
                return JsonResponse({"error": "No valid fields provided for update."}, status=400)

            # Perform update operation
            update_result = db['Stores'].update_one({"_id": store_id_obj}, {"$set": update_data})

            if update_result.modified_count > 0:
                return JsonResponse({"message": "Store details updated successfully!"}, status=200)
            else:
                return JsonResponse({"message": "No changes were made to the store."}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)








