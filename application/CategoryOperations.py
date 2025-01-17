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


class CategoryOperations:

    def getCategoryProductByStore(self, data, db=None):
        try:
            # Ensure the database connection is provided
            if db is None:
                raise ValueError("Database connection is required.")

            # Extract store_id and validate it
            store_id = data.get("store_id")
            if not store_id or not ObjectId.is_valid(store_id):
                return JsonResponse({"error": "Invalid or missing store_id."}, status=400)

            # Set limits for categories and products per category
            max_categories = 10
            max_products_per_category = 15

            # Query categories for the store
            categories = list(db['Categories']
                            .find({"store_id": store_id})
                            .limit(max_categories))

            if not categories:
                return JsonResponse({"error": "No categories found for the store."}, status=404)

            # For each category, fetch up to 15 products
            result = []
            for category in categories:
                category_id = str(category["_id"])
                category_name = category.get("category_name", "Unknown Category")

                # Query products for the category
                products = list(db['Products']
                                .find({"category_id": category_id})
                                .limit(max_products_per_category))

                # Format products for response
                formatted_products = []
                for product in products:
                    formatted_products.append({
                        "product_id": str(product["_id"]),
                        "product_name": product.get("product_name"),
                        "price": product.get("price"),
                        "stock": product.get("stock"),
                        "description": product.get("description", ""),
                        "created_at": product.get("created_at"),
                        "updated_at": product.get("updated_at"),
                    })

                # Add category and its products to the result
                result.append({
                    "category_id": category_id,
                    "category_name": category_name,
                    "products": formatted_products
                })

            # Return the categories with their products
            return JsonResponse({"categories": result}, status=200)

        except Exception as e:
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)
