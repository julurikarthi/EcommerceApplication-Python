from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 


class ProductOperations:

    def create_product(self, data, db):
        """
        Creates a new product in the database after validating the store_id.
        """
        try:
            # Extract required fields from data
            name = data.get("name")
            description = data.get("description")
            price = data.get("price")
            stock = data.get("stock")
            store_id = data.get("store_id")
            
            # Validate required fields
            if not all([name, description, price, stock, store_id]):
                return JsonResponse({"error": "All fields (name, description, price, stock, store_id) are required."}, status=400)
            
            # Validate price and stock
            if not isinstance(price, (int, float)) or price <= 0:
                return JsonResponse({"error": "Price must be a positive number."}, status=400)
            if not isinstance(stock, int) or stock < 0:
                return JsonResponse({"error": "Stock must be a non-negative integer."}, status=400)
            
            # Check if the store_id exists in the Stores collection
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
        
            if not store:
                return JsonResponse({"error": "Invalid store_id. No store found with this ID."}, status=400)
            
            
            # Create product document
            products_collection = db['Products']
            product = {
                "name": name,
                "description": description,
                "price": price,
                "stock": stock,
                "store_id": store_id,
                "created_at": datetime.now(),
            }
            
            # Insert the product into the Products collection
            result = products_collection.insert_one(product)
            
            # Return success response
            return JsonResponse({"message": "Product created successfully.", "product_id": str(result.inserted_id)}, status=201)
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
        


    def updateProduct(self, data, db):
        try:
            # Get necessary fields from the incoming data
            product_id = data.get('product_id')
            store_id = data.get('store_id')
            product_name = data.get('product_name')
            price = data.get('price')
            description = data.get('description', '')

            # Ensure the product_id and store_id are valid ObjectId types
            if not ObjectId.is_valid(store_id):
                return JsonResponse({"error": "Invalid store_id format."}, status=400)
            if not ObjectId.is_valid(product_id):
                return JsonResponse({"error": "Invalid product_id format."}, status=400)

            # Check if the store exists in the 'Stores' collection
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Invalid store_id. No store found with this ID."}, status=400)

            # Check if the product exists in the 'Products' collection for the given store
            product = db['Products'].find_one({"_id": ObjectId(product_id), "store_id": store_id})
            if not product:
                return JsonResponse({"error": "Product not found for the given store."}, status=404)

            # Prepare the data to be updated
            updated_data = {}
            if product_name:
                updated_data["product_name"] = product_name
            if price is not None:  # Ensure price is not None
                updated_data["price"] = price
            if description:
                updated_data["description"] = description

            # Update the product in the 'Products' collection
            result = db['Products'].update_one({"_id": ObjectId(product_id)}, {"$set": updated_data})

            # Check if any document was updated
            if result.modified_count == 0:
                return JsonResponse({"error": "No changes made to the product."}, status=400)

            return JsonResponse({"message": "Product updated successfully!"}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)



        

            # # Check if the product exists
            # product = db['Products'].find_one({"_id": ObjectId(product_id), "store_id": store_id})
            # if not product:
            #     return JsonResponse({"error": "Product not found for the given store."}, status=404)

            # # Prepare the updated product data
            # updated_data = {}
            # if product_name:
            #     updated_data["product_name"] = product_name
            # if price:
            #     updated_data["price"] = price
            # if description:
            #     updated_data["description"] = description

            # # Update the product in the 'Products' collection
            # result = db['Products'].update_one({"_id": ObjectId(product_id)}, {"$set": updated_data})

            # if result.modified_count == 0:
            #     return JsonResponse({"error": "No changes made to the product."}, status=400)

            # return JsonResponse({"message": "Product updated successfully!"}, status=200)


