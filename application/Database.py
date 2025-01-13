from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class Database:
    def __init__(self):
        """
        Initialize the Database class.

        Args:
            connection_string (str): The MongoDB connection string.
            database_name (str): The name of the database to use.
        """

    def getDatabase():
        """
        Returns the 'MarketPlaceDatabase' database object after ensuring a successful connection.
        
        Raises:
            ConnectionFailure: If unable to connect to MongoDB.
        """
        try:
            # MongoDB client with a timeout setting
            MONGODB_CONNECTION_STRING = "mongodb://18.188.42.21:27017/"
            client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
            db = client['MarketPlaceDatabase']
            
            # Attempt to check the connection
            client.server_info()  # This will throw an exception if unable to connect
            
            return db
        except ConnectionFailure as e:
            raise ConnectionFailure(f"Could not connect to MongoDB: {str(e)}")