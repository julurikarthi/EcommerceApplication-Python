
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