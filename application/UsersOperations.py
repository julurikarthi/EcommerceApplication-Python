from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.response import Response

secret_key = settings.SECRET_KEY

class UserOperations:
    
    def create_user(self, data, db):
        try:
            mobile_number = data.get("mobileNumber")
            userType = data.get("userType")
            users_collection = db['users']
            # Validate required fields
            if not all([mobile_number, userType]):
                response = {"error": "All fields are required. 'mobile_number', 'userType'"}
                return response

            # Check if the user already exists
            if users_collection.find_one({"mobileNumber": mobile_number}):
                response = {"error": "User with this Mobile number already exists."}
                print("Response to API:", response)  # Print the response
                return response

            # Create user document
            user = {
                "mobileNumber": mobile_number,
                "userType": userType
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
            total_amount = 0  

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

                product_total_price = product.get("price", 0) * quantity
                total_amount += product_total_price

                # Add product to processed list
                processed_products.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "price": product.get("price"),
                    "product_name": product.get("product_name")
                })

            # Tax Calculation
            tax_percentage = store.get("tax_percentage", 0)
            tax_amount = (total_amount * tax_percentage) / 100
            total_amount_with_tax = total_amount + tax_amount

            # Check if cart already exists for the customer & store
            existing_cart = db['Carts'].find_one({"customer_id": customer_id, "store_id": store_id})
            if existing_cart:
                existing_products = existing_cart.get("products", [])
                if not isinstance(existing_products, list):
                    return JsonResponse({"error": "Invalid data format for products in the cart."}, status=500)

                # Convert existing products into a dictionary for quick lookup
                existing_product_map = {p["product_id"]: p for p in existing_products}

                # Update or add products (Replace quantity instead of adding)
                for processed_product in processed_products:
                    product_id = processed_product["product_id"]
                    existing_product_map[product_id] = processed_product  # Replace quantity

                updated_products = list(existing_product_map.values())

                # Persist the update in MongoDB
                db['Carts'].update_one(
                    {"_id": existing_cart["_id"]},
                    {"$set": {"products": updated_products, "updated_at": datetime.utcnow()}}
                )

            else:
                # Create new cart entry
                cart_data = {
                    "customer_id": customer_id,
                    "store_id": store_id,
                    "products": processed_products,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                db['Carts'].insert_one(cart_data)

            # Fetch all cart items for the customer (all stores)
            all_carts = list(db['Carts'].find({"customer_id": customer_id}))

            response_data = []
            for cart in all_carts:
                response_data.append({
                    "cart_id": str(cart["_id"]),
                    "store_id": cart["store_id"],
                    "products": cart["products"]
                })

            return JsonResponse({
                "message": "Cart updated successfully.",
                "total_amount": round(total_amount, 2),
                "tax_amount": round(tax_amount, 2),
                "total_amount_with_tax": round(total_amount_with_tax, 2),
                "all_carts": response_data  # Returning all cart products for the customer
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)


        

    def getCartProducts(self, data, db):
        try:
            # Validate customer_id
            customer_id = data["customer_id"]
            if not customer_id:
                return JsonResponse({"error": "Invalid customer_id."}, status=400)

            # Query the 'Carts' collection for all carts of the customer
            carts = list(db['Carts'].find({"customer_id": customer_id}))
            if not carts:
                return JsonResponse({"error": "No carts found for the given customer_id."}, status=200)

            # Extract cart details and enrich with store information
            cart_list = []
            for cart in carts:
                store_id = cart["store_id"]

                # Query the 'Stores' collection for store details
                store = db['Stores'].find_one({"_id": ObjectId(store_id)})
                store_name = store.get("store_name") if store else "Unknown Store"
                store_image = store.get("image_id") if store else None

                cart_list.append({
                    "cart_id": str(cart["_id"]),
                    "store_id": store_id,
                    "store_name": store_name,
                    "store_image": store_image,
                    "products": cart.get("products", []),
                    "created_at": cart.get("created_at"),
                    "updated_at": cart.get("updated_at")
                })

            return JsonResponse({"carts": cart_list}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)


    
    def getCartByStore(self, data, db):
        try:
            # Validate inputs
            customer_id = data.get("customer_id")
            store_id = data.get("store_id")

            if not customer_id or not store_id:
                return JsonResponse({"error": "Customer ID and Store ID are required."}, status=400)

            # Query the 'Carts' collection for the specific cart
            cart = db['Carts'].find_one({"customer_id": customer_id, "store_id": store_id})
            if not cart:
                return JsonResponse({"error": "Cart not found for the given customer_id and store_id."}, status=200)

            # Fetch store details
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            store_name = store.get("store_name") if store else "Unknown Store"
            store_image = store.get("image_id") if store else None

            # Prepare response
            return JsonResponse({
                "cart_id": str(cart["_id"]),
                "store_id": store_id,
                "store_name": store_name,
                "store_image": store_image,
                "products": cart.get("products", []),
                "created_at": cart.get("created_at"),
                "updated_at": cart.get("updated_at")
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)


    def updateCart(self, data, db):
            try:
                customer_id = data.get("customer_id")
                store_id = data.get("store_id")
                product = data.get("products")  # List of products with details like product_id, quantity, etc.

                # Validate required fields
                if not all([customer_id, store_id, product]):
                    return JsonResponse({"error": "customer_id, store_id, and products are required."}, status=400)

                # Validate customer_id and store_id
                if not customer_id or not store_id:
                    return JsonResponse({"error": "Invalid customer_id or store_id."}, status=400)
                
                product_id = product["product_id"]
                products = db['Products'].find_one({"_id": ObjectId(product_id)})
                if not products:
                    return JsonResponse({"error": f"Product not found for ID: {product_id}"}, status=400)
                quantity = product.get("quantity")
                # Check stock availability
                stock = products.get("stock", 0)
                if stock < quantity:
                    return JsonResponse({"error": f"Insufficient stock for product_id: {product_id}"}, status=400)

                # Check if the cart exists
                cart = db['Carts'].find_one({"customer_id": customer_id, "store_id": store_id})

                if not cart:
                    return JsonResponse({"error": "Cart not found for the given customer_id and store_id."}, status=404)

                # Update the cart with new products
                db['Carts'].update_one(
                    {"_id": cart["_id"]},
                    {"$set": {"products": product, "updated_at": datetime.now()}}
                )

                return JsonResponse({"message": "Cart updated successfully."}, status=200)

            except Exception as e:
                return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
            
    def deleteCartProduct(self, data, db):
        try:
            customer_id = data.get("customer_id")
            store_id = data.get("store_id")
            product_id = data.get("product_id")

            # Validate required fields
            if not all([customer_id, store_id, product_id]):
                return JsonResponse({"error": "customer_id, store_id, and product_id are required."}, status=400)

            # Validate customer_id, store_id, and product_id
            if not customer_id or not store_id or not product_id:
                return JsonResponse({"error": "Invalid customer_id, store_id, or product_id."}, status=400)

            # Check if the cart exists
            cart = db['Carts'].find_one({"customer_id": customer_id, "store_id": store_id})

            if not cart:
                return JsonResponse({"error": "Cart not found for the given customer_id and store_id."}, status=404)

            # Remove the product from the cart
            updated_products = [product for product in cart["products"] if product["product_id"] != product_id]

            db['Carts'].update_one(
                {"_id": cart["_id"]},
                {"$set": {"products": updated_products, "updated_at": datetime.now()}}
            )

            return JsonResponse({"message": "Product removed from cart successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def delete_all_carts(self, db):
        try:
            # Remove all documents from the 'Carts' collection
            delete_result = db['Carts'].delete_many({})

            # Return the number of deleted carts
            return JsonResponse({
                "message": f"All carts deleted successfully.",
                "deleted_count": delete_result.deleted_count
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def login_user(self, data, db):
        try:
            # Validate input
            mobileNumber = data.get("mobileNumber")
            user_type = data.get("userType")  # Fetch userType from request

            if not mobileNumber or not user_type:
                return JsonResponse({"error": "mobileNumber, and userType are required."}, status=400)

            # Validate userType
            if user_type not in ["customer", "storeOwner"]:
                return JsonResponse({"error": "Invalid userType. Must be 'customer' or 'storeOwner'."}, status=400)

            # Fetch the user from the database
            user = db['users'].find_one({"mobileNumber": mobileNumber, "userType": user_type})
            if not user:
                responce = self.create_user(data=data, db=db)
                user = db['users'].find_one({"mobileNumber": mobileNumber, "userType": user_type})

               

            # Check the password
            #check_password_hash(user["password"], password) TODO
            store_id = None
            store_type = None
            store = db['Stores'].find_one({"user_id": str(user["_id"])})
            print("Store found:", store)  # Debug line to check if store exists
            if store:
                store_id = str(store["_id"])
                store_type = store["store_type"]


            # Generate JWT token
            token = jwt.encode({
                "user_id": str(user["_id"]),
                "mobileNumber": user["mobileNumber"],
                "userType": user["userType"],
                "exp": datetime.utcnow() + timedelta(hours=36)  # Token valid for 24 hours
            }, secret_key, algorithm="HS256")

            # Prepare and return the response
            return JsonResponse({
                "message": "Login successful.",
                "token": token,
                "user": {
                    "user_id": str(user["_id"]),
                    "userType": user["userType"],
                    "mobileNumber": user["mobileNumber"],
                    "store_id": store_id,
                    "store_type":store_type
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        
    
    def delete_all_collections(self, db):
        try:
            collections = db.list_collection_names()  # Get all collection names
            for collection in collections:
                db[collection].drop()  # Drop each collection

            return JsonResponse({"message": "All collections deleted successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

        
    
    def login_storeOwner(self, data, db):
        try:
            # Validate input
            mobileNumber = data.get("mobileNumber")
            user_type = data.get("userType")  # Fetch userType from request

            if not mobileNumber or not user_type:
                return JsonResponse({"error": "mobileNumber and userType are required."}, status=400)

            # Validate userType
            if user_type not in ["customer", "storeOwner"]:
                return JsonResponse({"error": "Invalid userType. Must be 'customer' or 'storeOwner'."}, status=400)

            # Fetch the user from the database
            user = db['users'].find_one({"mobileNumber": mobileNumber, "userType": user_type})
            if not user:
                response = self.create_user(data=data, db=db)
                user = db['users'].find_one({"mobileNumber": mobileNumber, "userType": user_type})

            # Check if the user is a store owner but has no store
            store_id = None
            store_type = None
            store = db['Stores'].find_one({"user_id": str(user["_id"])})

            if user_type == "storeOwner" and not store:
                return JsonResponse({"error": "You are not a store owner."}, status=403)

            if store:
                store_id = str(store["_id"])
                store_type = store["store_type"]

            # Generate JWT token
            token = jwt.encode({
                "user_id": str(user["_id"]),
                "mobileNumber": user["mobileNumber"],
                "userType": user["userType"],
                "exp": datetime.utcnow() + timedelta(hours=36)  # Token valid for 36 hours
            }, secret_key, algorithm="HS256")

            # Prepare and return the response
            return JsonResponse({
                "message": "Login successful.",
                "token": token,
                "user": {
                    "user_id": str(user["_id"]),
                    "userType": user["userType"],
                    "mobileNumber": user["mobileNumber"],
                    "store_id": store_id,
                    "store_type": store_type
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

        
    def verify_token(self, request):
        try:
            # Extract token from the Authorization header
            token = request.headers.get('Authorization')
            if not token:
                return JsonResponse({"error": "Token is required"}, status=400)

            # Extract the token part (after "Bearer")
            token = token.split(' ')[1]
            
            # Decode the token (this step validates the token and extracts the payload)
            decoded_data = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = decoded_data.get("user_id")  # Assuming user_id is stored in the token

            # Check if the user type is valid (can be 'storeOwner' or 'customer' or other roles)
           
            user_type = decoded_data.get("userType")
            if user_type not in ["storeOwner", "customer"]:
                return JsonResponse({"error": "Unauthorized: Invalid user type."}, status=403)
            # If everything is valid, return the decoded data
            return decoded_data

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def refresh_token(self, request):
        # Verify the access token
        payload = self.verify_token(request=request)

        # Check if the result of verify_token is an error response (JsonResponse)
        # if isinstance(payload, JsonResponse):
        #     return payload  # Return the error response from verify_token
       
        try:
            print(payload)
            # Generate a new access token if the verification is successful
            new_access_token = jwt.encode({
                    "user_id": payload["user_id"],
                    "email": payload["mobileNumber"],
                    "userType": payload["userType"],
                    "exp": datetime.utcnow() + timedelta(hours=36)  # Token valid for 36 hours
                }, secret_key, algorithm="HS256")
            return JsonResponse({
                "token": new_access_token,
                
            }, status=200)
        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)




