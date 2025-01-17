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
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.create_Store(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['get'])
    def storeDetails(self, request):
        try:
            store_operations = StoreOperation()
            details = store_operations.storeDetails()
            return Response(details)  # Use Response instead of JsonResponse
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getAllStores(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getAllStores(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getstoreCategories(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getCategoriesByStore(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def getCategoryProductByStore(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = CategoryOperations()
            return store_operations.getCategoryProductByStore(data=data, db=db)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    
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
        
    @action(detail=False, methods=['post'])
    def createProduct(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.create_product(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def updateProduct(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.updateProduct(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getAllProductbyStore(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.getAllProducts(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def deleteProduct(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            product_operations = ProductOperations()
            return product_operations.deleteProduct(data=data, db=db)
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
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.create_Cart(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def createCategory(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.createCategory(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def createOffer(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.createOffer(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getStoreOffers(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getStoreOffers(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def getAllOffers(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getAllOffers(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def deleteOffer(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.deleteOffer(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

    @action(detail=False, methods=['post'])
    def getCart(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.getCartProducts(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def getCartByStore(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.getCartByStore(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def updateCart(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.updateCart(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['get'])
    def deleteCartItem(self, request):
        try:
            db = self.getDatabase()
            user_operations = UserOperations()
            return user_operations.delete_all_carts(db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    @action(detail=False, methods=['post'])
    def createOrder(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.createOrder(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

    @action(detail=False, methods=['post'])
    def checkStock(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.checkStock(data=data,db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    
    @action(detail=False, methods=['post'])
    def updateOrderStatus(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.update_OrderStatus(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

    @action(detail=False, methods=['post'])
    def getOrdersForStore(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.getOrders_ForStore(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def getOrdersForCustomer(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            order_operations = OrdersOperations()
            return order_operations.getOrders_ForCustomer(data=data, db=db)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
        

    
            
            
        
    



        