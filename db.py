from pymongo import MongoClient
import time

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "arduino"
COLL_NAME = "test"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db[COLL_NAME]

def get_all_emails():
    return [u["email"] for u in users.find({}, {"email": 1, "_id": 0})]

def get_user(email):
    return users.find_one({"email": email})

def set_otp(email, otp):
    expiry = time.time() + 300  # 5 minutes
    users.update_one({"email": email}, {"$set": {"otp": otp, "otp_expiry": expiry}})

def verify_otp(email, entered_otp):
    doc = get_user(email)
    if not doc:
        return False
    return doc.get("otp") == entered_otp and time.time() < doc.get("otp_expiry", 0)
