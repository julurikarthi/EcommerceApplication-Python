from django.http import JsonResponse
from pymongo import MongoClient
import bcrypt
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from .Database import Database

class UserOperations:
    db_instance = Database()
    db = db_instance.connect()
    users_collection = db_instance.get_collection("users")
    
    def create_user(request):
        if request.method == 'POST':
                try:
                    # Extract user data from request
                    data = request.POST
                    name = data.get("name")
                    email = data.get("email")
                    password = data.get("password")
                    mobile_number = data.get("mobileNumber")

                    # Validate required fields
                    if not all([name, email, password, mobile_number]):
                        return JsonResponse({"error": "All fields are required."}, status=400)

                    # Check if the user already exists
                    if users_collection.find_one({"email": email}):
                        return JsonResponse({"error": "User with this email already exists."}, status=400)

                    # Hash the password
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                    # Create user document
                    user = {
                        "name": name,
                        "email": email,
                        "password": hashed_password.decode('utf-8'),  # Store hashed password as string
                        "mobileNumber": mobile_number,
                    }

                    # Insert into MongoDB
                    users_collection.insert_one(user)

                    return JsonResponse({"message": "User created successfully."}, status=201)
                except Exception as e:
                    return JsonResponse({"error": str(e)}, status=500)
        else:
                return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)



