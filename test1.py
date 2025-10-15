from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["arduino"]         # your database name
collection = db["test"]       # your collection name

# List all users
for user in collection.find():
    print(user)
