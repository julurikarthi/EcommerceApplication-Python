from pymongo import MongoClient

# Update with the correct IP
client = MongoClient("mongodb://3.16.168.145:27017/")
db = client['EcommerceApplication']
