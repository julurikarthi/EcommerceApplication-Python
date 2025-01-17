from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 
import json

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
