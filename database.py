from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "hrms_lite")

client = None
db = None

def connect_to_mongo():
    """Connect to MongoDB"""
    global client, db
    try:
        client = MongoClient(MONGODB_URL)
        # Test connection
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        print("✅ Connected to MongoDB successfully")
        return db
    except ConnectionFailure as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        raise

def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("MongoDB connection closed")

def get_database():
    """Get database instance"""
    global db
    if db is None:
        db = connect_to_mongo()
    return db
