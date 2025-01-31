from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 


class ProductOperations:

    def create_product(self, data, db):
        """
        Creates a new product in the database after validating the store_id and category_id.
        """
        try:
            # Extract required fields from data
            name = data.get("product_name")
            description = data.get("description")
            price = data.get("price")
            stock = data.get("stock")
            imageIds = data.get("imageids",[])
            store_id = data.get("store_id")
            category_id = data.get("category_id")
            store_type = data.get("store_type")
            isPublish = data.get("isPublish", True)  # New field for category association
            
            # Validate required fields
            if not all([name, description, price, stock, store_id, category_id, imageIds, store_type]):
                return JsonResponse({"error": "All fields (product_name, description, price, stock, store_id, category_id, imageIds, store_type) are required."}, status=400)
            
            # Validate price and stock
            if not isinstance(price, (int, float)) or price <= 0:
                return JsonResponse({"error": "Price must be a positive number."}, status=400)
            if not isinstance(stock, int) or stock < 0:
                return JsonResponse({"error": "Stock must be a non-negative integer."}, status=400)
            
            # Check if the store_id exists in the Stores collection
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Invalid store_id. No store found with this ID."}, status=400)
            
            # Check if the category_id exists in the Categories collection and belongs to the specified store
            category = db['Categories'].find_one({"_id": ObjectId(category_id), "store_id": store_id})
            if not category:
                return JsonResponse({"error": "Invalid category_id. The category does not exist or does not belong to the specified store."}, status=400)
            
            # Create product document
            product = {
                "product_name": name,
                "description": description,
                "price": price,
                "stock": stock,
                "store_id": store_id,
                "category_id": category_id,
                "created_at": datetime.utcnow(),
                "imageids": imageIds,
                "isPublish": isPublish,
                "store_type": store_type
            }
            
            # Insert the product into the Products collection
            result = db['Products'].insert_one(product)
            
            # Return success response
            return JsonResponse({
                "message": "Product created successfully.",
                "product_id": str(result.inserted_id),
                "store_id": store_id,
                "category_id": category_id,
                "category_name": category.get("category_name")  # Include category name for confirmation
            }, status=201)
        
        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
   


    def updateProduct(self, data, db):
        try:
            # Get necessary fields from the incoming data
            product_id = data.get('product_id')
            store_id = data.get('store_id')
            product_name = data.get('product_name')
            price = data.get('price')
            stock = data.get('stock')
            description = data.get('description', '')
            isPublish = data.get("isPublish", True)
            imageIds = data.get("imageids")
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
            if stock:
                updated_data["stock"] = stock
            if isPublish:
                updated_data["isPublish"] = isPublish
            if imageIds:
                updated_data["imageIds"] = imageIds

            # Update the product in the 'Products' collection
            result = db['Products'].update_one({"_id": ObjectId(product_id)}, {"$set": updated_data})

            # Check if any document was updated
            if result.modified_count == 0:
                return JsonResponse({"error": "No changes made to the product."}, status=400)

            return JsonResponse({"message": "Product updated successfully! "}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
    

    def getAllProducts(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Query to filter products by store_id if provided
            query = {}

            store_id = data["store_id"]
            if store_id:
                if not ObjectId.is_valid(store_id):
                    return JsonResponse({"error": "Invalid store_id format."}, status=400)
                query["store_id"] = store_id

            category_id = data.get("category_id")
            if category_id:
                 query["category_id"] = category_id

            isPublish = data.get("isPublish")
            if isPublish:
                 query["isPublish"] = isPublish

               # Pagination logic
            page = int(data.get("page", 1))  # Default to page 1 if not provided
            limit = 30
            skip = (page - 1) * limit
            # Fetch paginated products from the database
            products = list(db['Products'].find(query).skip(skip).limit(limit))

        
            # Format the products for JSON serialization
            formatted_products = []
            for product in products:
                formatted_products.append({
                    "product_id": str(product["_id"]),
                    "store_id": str(product["store_id"]),
                    "product_name": product.get("product_name"),
                    "price": product.get("price"),
                    "stock": product.get("stock"),
                    "imageids": product.get("imageIds"),
                    "isPublish": product.get("isPublish"),
                    "category_id": product.get("category_id"),
                    "description": product.get("description", ""),
                    "created_at": product.get("created_at", None),
                    "updated_at": product.get("updated_at", None),
                })

            # Return the list of products
            return JsonResponse({"products": formatted_products}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def getAllPublishedProducts(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Query to filter products by store_id and isPublish
            query = {"isPublish": True}  # Only fetch published products
            store_id = data.get("store_id")
            
            if store_id:
                if not ObjectId.is_valid(store_id):
                    return JsonResponse({"error": "Invalid store_id format."}, status=400)
                query["store_id"] = store_id

            category_id = data.get("category_id")
            print(category_id)
            if category_id:
                 query["category_id"] = category_id

            # Pagination logic
            page = int(data.get("page", 1))  # Default to page 1 if not provided
            limit = 30
            skip = (page - 1) * limit

            # Fetch paginated products from the database
            products = list(db['Products'].find(query).skip(skip).limit(limit))

            # Format the products for JSON serialization
            formatted_products = []
            for product in products:
                formatted_products.append({
                    "product_id": str(product["_id"]),
                    "store_id": str(product["store_id"]),
                    "product_name": product.get("product_name"),
                    "price": product.get("price"),
                    "stock": product.get("stock"),
                    "description": product.get("description", ""),
                    "created_at": product.get("created_at", None),
                    "updated_at": product.get("updated_at", None),
                    "isPublish": product.get("isPublish", True)  # Ensure this is included
                })

            # Return the list of published products
            return JsonResponse({"products": formatted_products}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def deleteProduct(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Extract product_id from data
            product_id = data.get("product_id")
            if not product_id:
                return JsonResponse({"error": "Product ID is required."}, status=400)

            # Validate the product_id format
            if not ObjectId.is_valid(product_id):
                return JsonResponse({"error": "Invalid product_id format."}, status=400)

            # Attempt to delete the product
            result = db['Products'].delete_one({"_id": ObjectId(product_id)})

            # Check if the product was found and deleted
            if result.deleted_count == 0:
                return JsonResponse({"error": "Product not found."}, status=404)

            # Return success message
            return JsonResponse({"message": "Product deleted successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)




