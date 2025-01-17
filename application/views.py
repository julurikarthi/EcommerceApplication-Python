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
    def getstoreCategories(self, request):
        try:
            data = request.data
            db = self.getDatabase()
            store_operations = StoreOperation()
            return store_operations.getCategoriesByStore(data=data, db=db)
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
        """
        Custom action to handle image upload via POST request.
        """
        if 'image' not in request.FILES:
            return Response({"error": "No image file found in the request."}, status=status.HTTP_400_BAD_REQUEST)
        try:
         # Get the uploaded image file
            image_file = request.FILES['image']
            
            # Get the uploaded image file
            image_file = request.FILES['image']
            
            # Open the image using Pillow
            image = Image.open(image_file)
            
            # Check if the image is not already in RGB mode (PNG images are typically in RGBA)
            if image.mode in ("RGBA", "P"):  # If the image has an alpha channel or palette
                image = image.convert("RGB")  # Convert to RGB for saving as JPEG
            
            # Resize the image (e.g., max width of 800px while maintaining aspect ratio)
            max_width = 800
            if image.width > max_width:
                new_height = int((max_width / image.width) * image.height)
                image = image.resize((max_width, new_height), Image.ANTIALIAS)
            
            # Compress the image (convert to JPEG for better compression)
            compressed_image_io = BytesIO()
            
            # If the image is PNG, we will save it as PNG, else as JPEG
            if image_file.name.lower().endswith(".png"):
                image.save(compressed_image_io, format='PNG')  # Save as PNG if original format is PNG
            else:
                image.save(compressed_image_io, format='JPEG', quality=85)  # Convert to JPEG for other formats

            # Save the compressed image to Django's storage backend
            compressed_image_io.seek(0)  # Reset the IO pointer

            # Clean the file name by removing spaces and special characters
            clean_name = image_file.name.replace(" ", "_")  # Replace spaces with underscores
            clean_name = "".join(c for c in clean_name if c.isalnum() or c in ['_', '.'])  # Allow only alphanumeric and _ . characters

            file_extension = "png" if image_file.name.lower().endswith(".png") else "jpg"
            file_name = f"{os.path.splitext(clean_name)[0]}_compressed.{file_extension}"  # Add suffix and extension
            file_path = default_storage.save(file_name, ContentFile(compressed_image_io.read()))

            # Get the URL for accessing the uploaded file
            file_url = default_storage.url(file_path)
            # Return only the file name
            return JsonResponse({"message": "Image uploaded successfully.", "file_name": file_name}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
    
        

    
            
            
        
    



        