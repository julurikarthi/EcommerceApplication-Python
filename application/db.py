from pymongo import MongoClient

# Update with the correct IP
client = MongoClient("mongodb://18.188.42.21:27017/")
db = client['EcommerceApplication']