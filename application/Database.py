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

    def connect(self):
        """
        Establish a connection to the database.

        Returns:
            pymongo.database.Database: The connected database object.
        
        Raises:
            ConnectionFailure: If unable to connect to MongoDB.
        """
        try:
            MONGODB_CONNECTION_STRING = "mongodb://18.188.42.21:27017/"

            self.client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
            self.client.server_info()  # Verify connection
            self.db = self.client["MarketPlaceDatabase"]
            return self.db
        except ConnectionFailure as e:
            raise ConnectionFailure(f"Could not connect to MongoDB: {str(e)}")