from pymongo import MongoClient
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo.errors import ConnectionFailure
import json
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect
from .UsersOperations import UserOperations
from  .ProductOperations import ProductOperations
from rest_framework.decorators import action

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status
from rest_framework.exceptions import ValidationError

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
from .OrderOperation import OrdersOperations
from .StoreOperation import StoreOperation
from .CategoryOperations import CategoryOperations

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render
from django.shortcuts import render
from django.views import View
from django.http import FileResponse, HttpResponseRedirect
from PIL import Image
import io



secret_key = settings.SECRET_KEY


MONGODB_CONNECTION_STRING = "mongodb://18.188.42.21:27017/"

class HomeView(View):
    def get(self, request):
        return render(request, "react/index.html")
    

class AddProductView(View):
    def get(self, request):
        # Render the addProduct.html template
        return render(request, "react/addProduct.html")

class ProductViewSet(ViewSet):

    def home(request):
        return render(request, "home.html")
    
    def list(self, request):
        # Handle GET request (e.g., retrieve all products)
        products = [{"id": 1, "name": "Product A"}, {"id": 2, "name": "Product B"}]
        return Response(products)

    @action(detail=False, methods=['post'])
    def createStore(self, request):
        # Parsing the incoming data
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.create_Store(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def storeDetails(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            store_operations = StoreOperation()
            details = store_operations.storeDetails()
            return Response(details)  # Use Response instead of JsonResponse
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def deleteStore(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.delete_Store(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getStoreDetails(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.get_StoreDetails(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def updateStoreDetails(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.update_StoreDetails(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getDashboardData(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getDashboardData(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getstoreCategories(self, request):
        try:
            data = request.data

            # Skip token verification for customers
            if data.get("userType", "").lower() != "customer":
                token_response = self.verify_token(request=request)
                if isinstance(token_response, JsonResponse):
                    return token_response
            
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getCategoriesByStore(data=data, db=db)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


    @action(detail=False, methods=['post'])
    def getCategoryProductByStore(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = CategoryOperations()
            return store_operations.getCategoryProductByStore(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = UserOperations()
            return store_operations.login_user(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def loginstoreOwner(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = UserOperations()
            return store_operations.login_storeOwner(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['get'])
    def delete_all_collections(self, request):
        try:
            db = self.getDatabase()
            store_operations = UserOperations()
            return store_operations.delete_all_collections(db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        
        
    @action(detail=False, methods=['get'])
    def refreshtoken(self, request):
        try:
            store_operations = UserOperations()
            return store_operations.refresh_token(request=request)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['get'])
    def test(self, request):
        return Response({"status": "testing"}, status=200)

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

            # If everything is valid, return the decoded data (or just user_id, depending on needs)
            return decoded_data

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    
    @staticmethod
    def getDatabase():
        """
        Returns the 'MarketPlaceDatabase' database object after ensuring a successful connection.
        
        Raises:
            ConnectionFailure: If unable to connect to MongoDB.
        """
        try:
            # MongoDB client with a timeout setting
            client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
            db = client['MarketPlaceDatabase']
            
            # Attempt to check the connection
            client.server_info()  # This will throw an exception if unable to connect
            
            return db
        except ConnectionFailure as e:
            raise ConnectionFailure(f"Could not connect to MongoDB: {str(e)}")
        
    
    @action(detail=False, methods=['post'], url_path='uploadImage')
    def uploadImage(self, request):
        try:
            store_operations = StoreOperation()
            return store_operations.uploadImage(request=request)
        except Exception as e:
                return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'], url_path='uploadMultipleImages')
    def uploadMultipleImages(self, request):
        try:
            store_operations = StoreOperation()
            return store_operations.uploadMultipleImages(request=request)
        except Exception as e:
                    return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['get'], url_path='populateCategories')
    def populateCategories(self, request):
        try:
            store_operations = StoreOperation()
            db = self.getDatabase()
            return store_operations.populateCategories(db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['get'], url_path='getAllCategories')
    def getAllCategories(self, request):
        try:
            store_operations = StoreOperation()
            db = self.getDatabase()
            return store_operations.getAllCategories(db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    

    @action(detail=False, methods=['post'], url_path='createChildCategory')
    def createChildCategory(self, request):
        try:
            data = request.data
            store_operations = StoreOperation()
            db = self.getDatabase()
            return store_operations.createChildCategory(db=db, data=data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        


    @action(detail=False, methods=['post'], url_path='deleteImage')
    def delete_image(self, request):
        try:
            data = request.data
            store_operations = StoreOperation()
            return store_operations.delete_image(data=data)
        except Exception as e:
                return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['get'], url_path='deleteallImages')
    def deleteAllImages(self, request):
        try:
            store_operations = StoreOperation()
            return store_operations.delete_all_images()
        except Exception as e:
                return Response({"error": str(e)}, status=500)
    
   
    @action(detail=False, methods=['get'], url_path='downloadImage')
    def download_image(self, request):
        """
        Serve a resized image with a max width of 500px.
        """
        file_name = request.GET.get('file_name')
        max_width = 500  # Fixed width for mobile

        if not file_name:
            return Response({"error": "File name is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with default_storage.open(file_name, 'rb') as file:  # Open file from storage
                img = Image.open(file)

                # Maintain aspect ratio
                aspect_ratio = img.height / img.width
                new_height = int(max_width * aspect_ratio)

                img = img.resize((max_width, new_height), Image.LANCZOS)

                # Save resized image in memory
                img_io = io.BytesIO()
                img.save(img_io, format="JPEG", quality=85)  # Optimize quality
                img_io.seek(0)

                return FileResponse(img_io, content_type="image/jpeg")

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    @action(detail=False, methods=['post'])
    def createUser(self, request):
        """
        Handles creating a new user in the database.
        """
        try:
            # Parse request data
            data = request.data

            # Get the database connection
            db = self.getDatabase()

            # Create the user
            userOperation = UserOperations()
            response = userOperation.create_user(data=data, db=db)

            # Return the response from the UserOperations method
            return Response(response, status=response.get("status", 200))  # Use default 200 if status not provided

        except ValidationError as e:
            return Response({"error": e.detail}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['get'])
    def testProduct(self, request):
        try:
           return JsonResponse({"error": ""}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def updateProduct(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.updateProduct(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def createProduct(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.create_product(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getAllProductbyStore(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.getAllProducts(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def deleteProduct(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.deleteProduct(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getproductDetails(self, request):
        try:
            data = request.data
            if data.get("userType", "").lower() != "customer":
                token_response = self.verify_token(request=request)
                if isinstance(token_response, JsonResponse):
                    return token_response
          
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.get_productDetails(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getAllPublishedProducts(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.getAllPublishedProducts(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def createCart(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.create_Cart(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def createCategory(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.createCategory(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def createSubcategory(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.createSubcategory(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
        
    @action(detail=False, methods=['post'])
    def createOffer(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.createOffer(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
   
    @action(detail=False, methods=['post'])
    def getOffersByStore(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getOffersByStore(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
        
    @action(detail=False, methods=['post'])
    def getStoreOffers(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getStoreOffers(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getAllOffers(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getAllOffers(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def deleteOffer(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.deleteOffer(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

    @action(detail=False, methods=['post'])
    def getCart(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.getCartProducts(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def getCartByStore(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.getCartByStore(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def updateCart(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.updateCart(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['get'])
    def deleteCartItem(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.delete_all_carts(db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def createOrder(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.createOrder(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

    @action(detail=False, methods=['post'])
    def checkStock(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.checkStock(data=data,db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    
    @action(detail=False, methods=['post'])
    def updateOrderStatus(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.update_OrderStatus(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

    @action(detail=False, methods=['post'])
    def getOrdersForStore(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.getOrders_ForStore(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def getOrdersForCustomer(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.getOrders_ForCustomer(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


    
            
            
        
    



        