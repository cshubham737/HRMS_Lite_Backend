from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
print(f"Connection String: {MONGODB_URL}")

try:
    client = MongoClient(MONGODB_URL)
    
    # Test ping
    client.admin.command('ping')
    print("✅ Ping successful")
    
    # Get database
    db = client['hrms_lite']
    
    # Test write
    test_result = db.test_collection.insert_one({"test": "data"})
    print(f"✅ Write successful: {test_result.inserted_id}")
    
    # Test read
    count = db.test_collection.count_documents({})
    print(f"✅ Read successful: {count} documents")
    
    # Cleanup
    db.test_collection.delete_many({})
    print("✅ All operations successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()