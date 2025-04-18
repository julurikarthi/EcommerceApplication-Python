from django.http import JsonResponse
from datetime import datetime
from bson import ObjectId 
import uuid

class ProductOperations:

    def create_product(self, data, db):
        """
        Creates a new product in the database after validating the store_id and category_id.
        """
        try:
            # Extract required fields from data
            name = data.get("product_name")
            description = data.get("description")
            stock = data.get("stock")
            imageIds = data.get("imageids", [])
            store_id = data.get("store_id")
            category_id = data.get("category_id")
            store_type = data.get("store_type")
            isPublish = data.get("isPublish", True)
            search_tags = data.get("search_tags", [])
            variants = data.get("variants", [])  # New field for product variants

            # Validate required fields
            if not all([name, description, stock, store_id, category_id, imageIds, store_type]):
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Validate stock
            if not isinstance(stock, int) or stock < 0:
                return JsonResponse({"error": "Stock must be a non-negative integer."}, status=400)

            # Validate variants
            formatted_variants = []
            for variant in variants:
                variant_type = variant.get("variant_type")
                value = variant.get("value")
                variant_price = variant.get("price")
                variant_stock = variant.get("stock")

                if not variant_type or not value:
                    return JsonResponse({"error": "Each variant must have a variant_type and value."}, status=400)
                if not isinstance(variant_price, (int, float)) or variant_price <= 0:
                    return JsonResponse({"error": "Each variant must have a valid price."}, status=400)
                if not isinstance(variant_stock, int) or variant_stock < 0:
                    return JsonResponse({"error": "Each variant must have a non-negative stock value."}, status=400)

                # Auto-generate unique variant_id
                variant_id = str(uuid.uuid4())

                formatted_variants.append({
                    "variant_id": variant_id,
                    "variant_type": variant_type,
                    "value": value,
                    "price": variant_price,
                    "stock": variant_stock
                })

            # Check if store_id exists
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Invalid store_id."}, status=400)

            # Check if category_id exists
            category = db['Categories'].find_one({"_id": ObjectId(category_id), "store_id": store_id})
            if not category:
                return JsonResponse({"error": "Invalid category_id."}, status=400)

            # Auto-generate search tags if not provided
            if not search_tags:
                search_tags = [name.lower()] + description.lower().split()[:5]
                search_tags.append(category.get("category_name", "").lower())

            # Ensure tags are unique and lowercase
            search_tags = list(set(tag.strip().lower() for tag in search_tags))

            # Create product document
            product = {
                "product_name": name,
                "description": description,
                "stock": stock,
                "store_id": store_id,
                "category_id": category_id,
                "created_at": datetime.utcnow(),
                "imageids": imageIds,
                "isPublish": isPublish,
                "store_type": store_type,
                "search_tags": search_tags,
                "variants": formatted_variants  # Store formatted variants
            }

            # Only store price at product level if no variants exist
            if not formatted_variants:
                product["price"] = data.get("price")

            # Insert product into the database
            result = db['Products'].insert_one(product)

            return JsonResponse({
                "message": "Product created successfully.",
                "product_id": str(result.inserted_id),
                "store_id": store_id,
                "category_id": category_id,
                "category_name": category.get("category_name"),
                "search_tags": search_tags,
                "variants": formatted_variants  # Return generated variants
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
            search_tags = data.get("search_tags", [])
            variants = data.get("variants", [])

            # Ensure valid ObjectId format
            if not ObjectId.is_valid(store_id):
                return JsonResponse({"error": "Invalid store_id format."}, status=400)
            if not ObjectId.is_valid(product_id):
                return JsonResponse({"error": "Invalid product_id format."}, status=400)

            # Check if store exists
            store = db['Stores'].find_one({"_id": ObjectId(store_id)})
            if not store:
                return JsonResponse({"error": "Invalid store_id. No store found with this ID."}, status=400)

            # Check if product exists
            product = db['Products'].find_one({"_id": ObjectId(product_id), "store_id": store_id})
            if not product:
                return JsonResponse({"error": "Product not found for the given store."}, status=404)

            # Prepare update data
            updated_data = {}
            if product_name:
                updated_data["product_name"] = product_name
            if description:
                updated_data["description"] = description
            if stock is not None:
                updated_data["stock"] = stock
            if isPublish is not None:
                updated_data["isPublish"] = isPublish
            if imageIds:
                updated_data["imageids"] = imageIds

            # Variants Processing
            formatted_variants = []
            if variants:
                for variant in variants:
                    variant_type = variant.get("variant_type")
                    variant_price = variant.get("price")
                    variant_stock = variant.get("stock")

                    if not variant_type or not isinstance(variant_price, (int, float)) or variant_price <= 0:
                        return JsonResponse({"error": "Each variant must have a valid variant_type and price."}, status=400)
                    if not isinstance(variant_stock, int) or variant_stock < 0:
                        return JsonResponse({"error": "Each variant must have a non-negative stock value."}, status=400)

                    formatted_variants.append({
                        "variant_type": variant_type,
                        "price": variant_price,
                        "stock": variant_stock
                    })

                updated_data["variants"] = formatted_variants
            else:
                # If no variants, allow price update
                if price is not None:
                    updated_data["price"] = price

            # Search Tags Processing
            if search_tags:
                updated_data["search_tags"] = list(set(tag.strip().lower() for tag in search_tags))
            else:
                auto_tags = [product_name.lower()] + description.lower().split()[:5]
                updated_data["search_tags"] = list(set(auto_tags))

            # Update the product in the database
            result = db['Products'].update_one({"_id": ObjectId(product_id)}, {"$set": updated_data})

            # Check if the update was successful
            if result.modified_count == 0:
                return JsonResponse({"error": "No changes made to the product."}, status=400)

            return JsonResponse({
                "message": "Product updated successfully!",
                "updated_fields": updated_data
            }, status=200)

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
                    "imageids": product.get("imageids"),
                    "isPublish": product.get("isPublish"),
                    "category_id": product.get("category_id"),
                    "description": product.get("description", ""),
                    "created_at": product.get("created_at", None),
                    "updated_at": product.get("updated_at", None),
                    "variants": product.get("variants", []),
                    "search_tags": product.get("search_tags", [])
                })

            # Return the list of products
            return JsonResponse({"products": formatted_products}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def getAllPublishedProducts(self, data, db=None):
        try:
            if db is None:
                raise ValueError("Database connection is required.")

            query = {"isPublish": True}  # Only fetch published products
            store_id = data.get("store_id")
            user_id = data.get("user_id")  # Fetch user_id if available
            
            if store_id:
                if not ObjectId.is_valid(store_id):
                    return JsonResponse({"error": "Invalid store_id format."}, status=400)
                query["store_id"] = store_id

            category_id = data.get("category_id")
            if category_id:
                query["category_id"] = category_id

            page = int(data.get("page", 1))  # Default to page 1 if not provided
            limit = 30
            skip = (page - 1) * limit

            # Fetch published products
            products = list(db['Products'].find(query).skip(skip).limit(limit))

            # Initialize cart products dictionary
            cart_products = {}

            # If user_id is provided, fetch cart data
            if user_id:
                cart = db['Carts'].find_one({"customer_id": user_id, "store_id": store_id})
                if cart:
                    for item in cart.get("products", []):
                        cart_products[item["product_id"]] = {
                            "isAddToCart": True,
                            "quantity": item.get("quantity", 1)
                        }

            # Format products with cart details
            formatted_products = []
            for product in products:
                product_id = str(product["_id"])
                formatted_products.append({
                    "product_id": product_id,
                    "store_id": str(product["store_id"]),
                    "product_name": product.get("product_name"),
                    "price": product.get("price"),
                    "stock": product.get("stock"),
                    "imageids": product.get("imageids"),
                    "isPublish": product.get("isPublish"),
                    "category_id": product.get("category_id"),
                    "description": product.get("description", ""),
                    "created_at": product.get("created_at", None),
                    "updated_at": product.get("updated_at", None),
                    "isAddToCart": cart_products.get(product_id, {}).get("isAddToCart", False),  # ✅ Check if product is in cart
                    "quantity": cart_products.get(product_id, {}).get("quantity", 0),  # ✅ Set quantity if in cart
                    "variants": product.get("variants", []),
                    "search_tags": product.get("search_tags", [])
                })

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
        


    def get_productDetails(self, data=None, db=None):
        try:
            if db is None:
                raise ValueError("Database connection is required.")
            if data is None:
                return JsonResponse({"error": "Request data is required."}, status=400)

            product_id = data.get("product_id")
            store_id = data.get("store_id")
            user_id = data.get("user_id")  # Optional

            if not product_id or not ObjectId.is_valid(product_id):
                return JsonResponse({"error": "Invalid or missing product_id."}, status=400)

            product = db['Products'].find_one({"_id": ObjectId(product_id)})
            if not product:
                return JsonResponse({"error": "Product not found."}, status=404)

            # Cart logic: Track quantity for each variant
            variant_cart_quantities = {}
            if user_id and store_id:
                cart = db['Carts'].find_one({"customer_id": user_id, "store_id": store_id})
                if cart:
                    for item in cart.get("products", []):
                        if item["product_id"] == product_id:
                            variant_type = item.get("variant_type")
                            variant_cart_quantities[variant_type] = item.get("quantity", 1)

            # Prepare product details response
            product_details = {
                "product_id": str(product["_id"]),
                "store_id": str(product["store_id"]),
                "product_name": product.get("product_name"),
                "price": product.get("price"),
                "stock": product.get("stock"),
                "imageids": product.get("imageids"),
                "isPublish": product.get("isPublish"),
                "category_id": product.get("category_id"),
                "description": product.get("description", ""),
                "created_at": product.get("created_at"),
                "updated_at": product.get("updated_at"),
                "variants": [],
                "isAddToCart": bool(variant_cart_quantities),  # True if any variant is in cart
                "quantity": sum(variant_cart_quantities.values())  # Total quantity of all variants
            }

            # Update variants list with cart quantities
            for variant in product.get("variants", []):
                variant_type = variant.get("variant_type")
                variant["cart_quantity"] = variant_cart_quantities.get(variant_type, 0)
                product_details["variants"].append(variant)

            return JsonResponse({"product": product_details}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
        

    def get_all_categories(self):
        return {
            "Groceries": {
                "Fresh Produce": [
                    "Fruits", "Vegetables", "Herbs", "Salads", "Organic Produce"
                ],
                "Snacks & Beverages": [
                    "Chips & Crisps", "Chocolates & Candies", "Nuts & Seeds",
                    "Soft Drinks", "Energy Drinks", "Tea & Coffee"
                ],
                "Dairy & Eggs": [
                    "Milk", "Cheese", "Yogurt", "Butter & Margarine", "Eggs"
                ],
                "Bakery & Confectionery": [
                    "Bread", "Cakes", "Cookies", "Pastries", "Breakfast Cereals"
                ],
                "Organic & Health Foods": [
                    "Gluten-Free Products", "Vegan Foods", "Protein Bars",
                    "Superfoods", "Dietary Supplements"
                ],
                "Canned & Packaged Foods": [
                    "Canned Vegetables", "Pasta & Noodles", "Sauces & Condiments",
                    "Soups", "Ready-to-Eat Meals"
                ],
                "Frozen Foods": [
                    "Frozen Vegetables", "Frozen Meals", "Ice Cream", "Frozen Snacks"
                ],
                "Beverages": [
                    "Water", "Juices", "Alcoholic Beverages", "Non-Alcoholic Beverages"
                ],
                "Pantry Staples": [
                    "Rice & Grains", "Flour", "Sugar", "Cooking Oil", "Spices & Seasonings"
                ]
            },
            "Fashion & Apparel": {
                "Men's Clothing": [
                    "T-Shirts", "Shirts", "Jeans", "Suits & Blazers", "Jackets & Coats",
                    "Shorts", "Activewear", "Underwear & Socks"
                ],
                "Women's Clothing": [
                    "Dresses", "Tops", "Jeans", "Skirts", "Jackets & Coats",
                    "Activewear", "Lingerie & Sleepwear"
                ],
                "Kids' Clothing": [
                    "Boys' Clothing", "Girls' Clothing", "Baby Clothing",
                    "School Uniforms", "Kids' Accessories"
                ],
                "Shoes": [
                    "Men's Shoes", "Women's Shoes", "Kids' Shoes", "Sports Shoes",
                    "Sandals & Flip-Flops", "Boots"
                ],
                "Accessories": [
                    "Bags & Backpacks", "Watches", "Jewelry", "Sunglasses",
                    "Belts", "Hats & Caps", "Scarves & Gloves"
                ],
                "Sportswear & Activewear": [
                    "Men's Activewear", "Women's Activewear", "Kids' Activewear",
                    "Gym Accessories", "Sports Shoes"
                ],
                "Lingerie & Sleepwear": [
                    "Bras", "Panties", "Lingerie Sets", "Pajamas", "Robes"
                ],
                "Ethnic & Traditional Wear": [
                    "Men's Ethnic Wear", "Women's Ethnic Wear", "Kids' Ethnic Wear",
                    "Traditional Accessories"
                ],
                "Seasonal Wear": [
                    "Winter Wear", "Summer Wear", "Rainwear"
                ]
            }
        }












