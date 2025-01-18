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

secret_key = settings.SECRET_KEY

MONGODB_CONNECTION_STRING = "mongodb://18.188.42.21:27017/"

class ProductViewSet(ViewSet):
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
        
    @action(detail=False, methods=['get'])
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
    def getAllStores(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getAllStores(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getstoreCategories(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
            data = request.data
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
        
    @action(detail=False, methods=['get'], url_path='downloadImage')
    def download_image(self, request):
        """
        Custom action to handle image download via GET request.
        """
        file_name = request.GET.get('file_name')
        
        if not file_name:
            return Response({"error": "File name is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Generate the file URL using the default storage backend
            file_url = default_storage.url(file_name)

            # Redirect to the file URL (pre-signed URL if configured for S3, etc.)
            return HttpResponseRedirect(file_url)

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
    def getAllPublishedProducts(self, request):
        try:
            token_response = self.verify_token(request=request)
            if isinstance(token_response, JsonResponse):
                return token_response
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
    
        

    
            
            
        
    



        