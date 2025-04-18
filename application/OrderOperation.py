from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 


class OrdersOperations:

    def createOrder(self, data, db):
        try:
            # Extract order details
            customer_id = data.get("customer_id")
            store_id = data.get("store_id")
            payment_type = data.get("payment_type")  # e.g., "Pickup", "Pay at Pickup", "Delivery"
            payment_confirmation = data.get("payment_confirmation")  # Payment reference or confirmation number
            delivery_address = data.get("delivery_address")  # Delivery address for "Delivery" type orders

            # Validate required fields
            if not customer_id or not store_id or not payment_type:
                return JsonResponse(
                    {"error": "Customer ID, Store ID, and Payment Type are required."},
                    status=400,
                )

            # Validate payment type
            valid_payment_types = ["Pickup", "Pay at Pickup", "Delivery"]
            if payment_type not in valid_payment_types:
                return JsonResponse(
                    {"error": f"Invalid payment_type. Valid options are: {', '.join(valid_payment_types)}."},
                    status=400,
                )

            # For pickup/delivery, ensure a payment confirmation number is provided
            if payment_type in ["Pickup", "Delivery"] and not payment_confirmation:
                return JsonResponse(
                    {"error": "Payment confirmation number is required for 'Pickup' and 'Delivery'."},
                    status=400,
                )

            # If payment type is 'Delivery', ensure a delivery address is provided
            if payment_type == "Delivery" and not delivery_address:
                return JsonResponse(
                    {"error": "Delivery address is required for 'Delivery' payment type."},
                    status=400,
                )

            # Validate customer and store existence
            customer = db['users'].find_one({"_id": ObjectId(customer_id)})
            if not customer:
                return JsonResponse({"error": "Customer not found."}, status=400)

            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Store not found."}, status=400)
            store_address = f"{store.get('street', '')}, {store.get('city', '')}, {store.get('state', '')} {store.get('pincode', '')}"

            # Fetch the cart for the customer
            cart = db['Carts'].find_one({"customer_id": customer_id, "store_id": store_id})
            if not cart:
                return JsonResponse({"error": "Cart not found for the customer in this store."}, status=400)

            # Calculate total price, taxes, and create the order items
            total_price = 0
            order_items = []
            for item in cart['products']:
                product_id = item['product_id']
                quantity = item['quantity']

                # Fetch product details
                product = db['Products'].find_one({"_id": ObjectId(product_id)})
                if not product:
                    return JsonResponse({"error": f"Product not found for ID: {product_id}"}, status=400)

                item_price = product.get("price") * quantity
                total_price += item_price
                order_items.append({
                    "product_id": str(product["_id"]),
                    "product_name": product.get("product_name"),
                    "price": product.get("price"),
                    "quantity": quantity
                })

            # Apply tax
            tax_percentage = store.get("tax_percentage", 0)
            tax_amount = round((total_price * tax_percentage) / 100, 2)
            total_price_with_tax = round(total_price + tax_amount, 2)

            # Deduct stock for all products in the cart
            stock_update_status = self.update_stock(cart['products'], db)
            if not stock_update_status["success"]:
                return JsonResponse({"error": stock_update_status["message"]}, status=400)

            # Create order entry
            order_data = {
                "customer_id": customer_id,
                "customer_name": customer.get("name"),
                "customer_email": customer.get("email"),
                "store_id": store_id,
                "store_name": store.get("store_name"),
                "products": order_items,
                "total_price": total_price,
                "tax_amount": tax_amount,
                "total_price_with_tax": total_price_with_tax,
                "payment_type": payment_type,
                "store_address": store_address,
                "payment_confirmation": payment_confirmation if payment_type in ["Pickup", "Delivery"] else None,
                "delivery_address": delivery_address if payment_type == "Delivery" else None,
                "status": "Pending",  # Initial status
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            result = db['Orders'].insert_one(order_data)

            # Clear cart after creating the order
            db['Carts'].delete_one({"customer_id": customer_id, "store_id": store_id})

            # Return success response
            return JsonResponse(
                {
                    "message": "Order created successfully.",
                    "order_id": str(result.inserted_id),
                    "total_price": total_price,
                    "tax_amount": tax_amount,
                    "total_price_with_tax": total_price_with_tax,
                    "products": order_items,
                    "store_address": store_address,
                    "payment_confirmation": payment_confirmation if payment_type in ["Pickup", "Delivery"] else None,
                    "delivery_address": delivery_address if payment_type == "Delivery" else None,
                    "status": "Pending"
                },
                status=201,
            )

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

    def update_stock(self, products, db):   
        try:
            for item in products:
                product_id = item['product_id']
                quantity = item['quantity']

                # Fetch product details
                product = db['Products'].find_one({"_id": ObjectId(product_id)})
                if not product:
                    return {"success": False, "message": f"Product not found for ID: {product_id}"}

                stock = product.get("stock", 0)
                if stock < quantity:
                    return {"success": False, "message": f"Insufficient stock for product_id: {product_id}"}

                # Deduct stock
                db['Products'].update_one(
                    {"_id": ObjectId(product_id)},
                    {"$inc": {"stock": -quantity}}
                )

            return {"success": True}
        except Exception as e:
            return {"success": False, "message": f"Error updating stock: {str(e)}"}
        

    def checkStock(self, data, db):
        try:
            customer_id = data.get("customer_id")

            # Validate customer ID
            if not customer_id:
                return JsonResponse({"error": "Customer ID is required."}, status=400)

            # Fetch the cart for the customer
            cart = db['Carts'].find_one({"customer_id": customer_id})
            if not cart:
                return JsonResponse(
                    {"error": f"No cart found for customer_id: {customer_id}"},
                    status=404
                )

            # Retrieve and validate products in the cart
            products = cart.get("products", [])
            if not products or not isinstance(products, list):
                return JsonResponse(
                    {"error": "No valid products found in the cart."},
                    status=400
                )

            insufficient_stock = []

            for item in products:
                product_id = item.get("product_id")
                requested_quantity = item.get("quantity", 0)

                # Validate product_id and quantity
                if not product_id:
                    return JsonResponse(
                        {"error": f"Invalid product data in cart: {item}"},
                        status=400
                    )

                # Fetch product details
                try:
                    product = db['Products'].find_one({"_id": ObjectId(product_id)})
                except Exception:
                    return JsonResponse(
                        {"error": f"Invalid product_id format: {product_id}"},
                        status=400
                    )

                if not product:
                    return JsonResponse(
                        {"error": f"Product not found for ID: {product_id}"},
                        status=404
                    )

                # Check stock availability
                available_stock = product.get("stock", 0)
                if requested_quantity > available_stock:
                    insufficient_stock.append({
                        "product_id": product_id,
                        "product_name": product.get("product_name", "Unknown"),
                        "available_stock": available_stock,
                        "requested_quantity": requested_quantity
                    })

            # Return insufficient stock details if any
            if insufficient_stock:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Insufficient stock for some products.",
                        "insufficient_stock": insufficient_stock
                    },
                    status=400
                )

            # All products are in stock
            return JsonResponse({"success": True, "message": "All products are in stock."}, status=200)

        except Exception as e:
            # Catch all unexpected errors
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        
    def update_OrderStatus(self, data, db):
        try:
            # Extract order ID and status from the input data
            order_id = data.get("order_id")
            new_status = data.get("status")

            # Validate inputs
            if not order_id or not new_status:
                return JsonResponse(
                    {"error": "Order ID and new status are required."},
                    status=400
                )

            # Define valid order statuses
            valid_statuses = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
            if new_status not in valid_statuses:
                return JsonResponse(
                    {"error": f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}."},
                    status=400
                )

            # Find the order by ID
            try:
                order = db['Orders'].find_one({"_id": ObjectId(order_id)})
            except Exception:
                return JsonResponse(
                    {"error": f"Invalid order_id format: {order_id}"},
                    status=400
                )

            if not order:
                return JsonResponse(
                    {"error": f"No order found with ID: {order_id}"},
                    status=404
                )

            # Update the order status
            db['Orders'].update_one(
                {"_id": ObjectId(order_id)},
                {
                    "$set": {
                        "status": new_status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Return success response
            return JsonResponse(
                {
                    "success": True,
                    "message": "Order status updated successfully.",
                    "order_id": order_id,
                    "new_status": new_status
                },
                status=200
            )

        except Exception as e:
            # Handle unexpected errors
            return JsonResponse(
                {"error": "Internal Server Error", "details": str(e)},
                status=500
            )


    def getOrders_ForStore(self, data, db):
        try:
            # Extract store ID and page number
            store_id = data.get("store_id")
            page = int(data.get("page", 1))  # Default to page 1 if not provided
            limit = 20  # Limit results to 20 orders per page
            skip = (page - 1) * limit

            # Validate input
            if not store_id:
                return JsonResponse({"error": "Store ID is required."}, status=400)

            # Fetch orders for the store with pagination
            total_orders = db['Orders'].count_documents({"store_id": store_id})
            orders = list(db['Orders'].find({"store_id": store_id}).skip(skip).limit(limit))

            if not orders:
                return JsonResponse({"message": "No orders found for this store."}, status=404)

            # Format response
            response = []
            for order in orders:
                # Fetch customer details
                customer = db['users'].find_one({"_id": ObjectId(order["customer_id"])})
                customer_name = customer.get("name") if customer else "Unknown"
                customer_email = customer.get("email") if customer else "Unknown"
                customer_phone = customer.get("mobileNumber") if customer else "Unknown"

                response.append({
                    "order_id": str(order["_id"]),
                    "customer_id": order["customer_id"],
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "customer_phone": customer_phone,
                    "products": order["products"],
                    "total_price": round(order["total_price"], 2),
                    "tax_amount": round(order["tax_amount"], 2),
                    "total_price_with_tax": round(order["total_price_with_tax"], 2),
                    "status": order["status"],
                    "payment_type": order["payment_type"],
                    "created_at": order["created_at"].isoformat()
                })

            return JsonResponse({
                "success": True,
                "orders": response,
                "total_orders": total_orders,
                "page": page,
                "total_pages": (total_orders + limit - 1) // limit  # Calculate total pages
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)


    def getOrders_ForCustomer(self, data, db):
        try:
            # Extract customer ID
            customer_id = data.get("customer_id")

            # Validate input
            if not customer_id:
                return JsonResponse({"error": "Customer ID is required."}, status=400)

            # Fetch orders for the customer
            orders = list(db['Orders'].find({"customer_id": customer_id}))
            if not orders:
                return JsonResponse({"message": "No orders found for this customer."}, status=404)

            # Cache for store details to avoid redundant DB calls
            store_cache = {}
            product_cache = {}

            # Format response
            response = []
            for order in orders:
                store_id = order["store_id"]

                # Fetch store details (cache to prevent redundant queries)
                if store_id and store_id not in store_cache:
                    store = db['Stores'].find_one({"_id": ObjectId(store_id)})
                    if store:
                        # Construct full address
                        store_address = f"{store.get('street', '')}, {store.get('city', '')}, {store.get('state', '')} {store.get('pincode', '')}".strip(", ")
                        store_image = store.get("image_id", None)  # Fetch store image
                    else:
                        store_address = "Unknown Address"
                        store_image = None

                    store_cache[store_id] = {"address": store_address, "image_id": store_image}

                store_details = store_cache.get(store_id, {"address": "Unknown Address", "image_id": None})

                # Fetch products and include image_id
                products_with_images = []
                for product in order["products"]:
                    product_id = product.get("product_id")

                    # Fetch product details only if not cached
                    if product_id and product_id not in product_cache:
                        product_data = db['Products'].find_one({"_id": ObjectId(product_id)})
                        product_cache[product_id] = product_data.get("imageids") if product_data else None

                    products_with_images.append({
                        "product_id": product_id,
                        "product_name": product.get("product_name"),
                        "quantity": product.get("quantity"),
                        "price": product.get("price"),
                        "imageids": product_cache.get(product_id, None)
                    })

                response.append({
                    "order_id": str(order["_id"]),
                    "store_id": store_id,
                    "store_name": order["store_name"],
                    "store_address": store_details["address"],
                    "store_image": store_details["image_id"],  # Store image added
                    "products": products_with_images,
                    "total_price": round(order["total_price"], 2),
                    "tax_amount": round(order["tax_amount"], 2),
                    "total_price_with_tax": round(order["total_price_with_tax"], 2),
                    "status": order["status"],
                    "payment_type": order["payment_type"],
                    "created_at": order["created_at"].isoformat()
                })

            return JsonResponse({"success": True, "orders": response}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)



