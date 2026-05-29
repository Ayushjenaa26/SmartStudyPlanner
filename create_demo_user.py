import hashlib
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["smartstudyplanner"]
users_collection = db["users"]

# Demo user
demo_username = "demo@studyflow.com"
demo_password = "DemoPass123!"

# Hash password
password_hash = hashlib.sha256(demo_password.encode()).hexdigest()

# Create demo user document
demo_user = {
    "auth0_user_id": "auth0|demo-user-001",
    "username": demo_username,
    "password_hash": password_hash,
    "display_name": "Demo User",
    "email": demo_username,
    "created_at": datetime.utcnow(),
    "google_calendar_connected": False,
    "links": [],
    "tasks": [],
    "goals": []
}

# Insert or update
result = users_collection.update_one(
    {"auth0_user_id": "auth0|demo-user-001"},
    {"$set": demo_user},
    upsert=True
)

print(f"Demo account created/updated:")
print(f"Username: {demo_username}")
print(f"Password: {demo_password}")
print(f"Auth0 User ID: auth0|demo-user-001")
print(f"Status: {'Created' if result.upserted_id else 'Updated'}")
