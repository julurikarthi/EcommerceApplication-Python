from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 

class UserOperations:
    
    def create_user(self, data, db):
        try:
            name = data.get("name")
            email = data.get("email")
            password = data.get("password")
            mobile_number = data.get("mobileNumber")
            ueserType = data.get("ueserType")
            users_collection = db['users']
        
            # Validate required fields
            if not all([name, email, password, mobile_number, ueserType]):
                response = {"error": "All fields are required."}
                print("Response to API:", response)  # Print the response
                return response

            # Check if the user already exists
            if users_collection.find_one({"email": email}):
                response = {"error": "User with this email already exists."}
                print("Response to API:", response)  # Print the response
                return response

            # Create user document
            user = {
                "name": name,
                "email": email,
                "password": password,  # Store hashed password as string
                "mobileNumber": mobile_number,
                "ueserType": ueserType
            }

            # Insert into MongoDB
            user_id = users_collection.insert_one(user)

            response = {"message": "User created successfully.", "user_id": str(user_id.inserted_id)}
            print("Response to API:", response)  # Print the response
            return response

        except Exception as e:
            response = {"error": str(e)}
            print("Response to API:", response)  # Print the response
            return response
    
    def create_Cart(self, data, db):
        try:
            customer_id = data.get("customer_id")
            store_id = data.get("store_id")
            products = data.get("products", [])  # List of {product_id, quantity}

            # Validate inputs
            if not customer_id or not store_id or not products:
                return JsonResponse({"error": "Customer ID, Store ID, and Products are required."}, status=400)

            # Validate store and customer IDs
            if not customer_id or not store_id:
                return JsonResponse({"error": "Invalid ID format for customer or store."}, status=400)

            # Verify customer existence
            customer = db['users'].find_one({"_id": ObjectId(customer_id)})
            if not customer:
                return JsonResponse({"error": "Customer not found."}, status=400)

            # Verify store existence
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Store not found."}, status=400)

            # Validate and process each product
            processed_products = []
            for item in products:
                product_id = item.get("product_id")
                quantity = item.get("quantity", 1)

                if not product_id:
                    return JsonResponse({"error": f"Invalid product_id: {product_id}"}, status=400)

                # Fetch product details
                product = db['Products'].find_one({"_id": ObjectId(product_id)})
                if not product:
                    return JsonResponse({"error": f"Product not found for ID: {product_id}"}, status=400)

                # Check stock availability
                stock = product.get("stock", 0)
                if stock < quantity:
                    return JsonResponse({"error": f"Insufficient stock for product_id: {product_id}"}, status=400)

                # Deduct stock
                db['Products'].update_one(
                    {"_id": ObjectId(product_id)},
                    {"$set": {"stock": stock - quantity}}
                )

                # Add product to processed list
                processed_products.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "price": product.get("price"),
                    "product_name": product.get("product_name")
                })

            # Create cart entry
            cart_data = {
                "customer_id": customer_id,
                "store_id": store_id,
                "products": processed_products,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = db['Carts'].insert_one(cart_data)

            return JsonResponse({
                "message": "Cart created successfully.",
                "cart_id": str(result.inserted_id),
                "products": processed_products
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def getCartProducts(self, data, db):
        try:
            # Validate customer_id
            customer_id = data["customer_id"]
            if not customer_id:
                return JsonResponse({"error": "Invalid customer_id."}, status=400)

            # Query the 'Carts' collection for the customer's cart
            cart = db['Carts'].find_one({"customer_id": customer_id})

            if not cart:
                return JsonResponse({"error": "Cart not found for the given customer_id."}, status=404)

            # Extract products and cart information
            products = cart.get("products", [])
            cart_id = str(cart["_id"])
            store_id = str(cart["store_id"])
            created_at = cart.get("created_at")
            updated_at = cart.get("updated_at")

            return JsonResponse({
                "cart_id": cart_id,
                "store_id": store_id,
                "products": products,
                "created_at": created_at,
                "updated_at": updated_at
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

