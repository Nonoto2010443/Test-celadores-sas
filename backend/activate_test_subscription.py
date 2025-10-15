"""
Script para activar suscripción manualmente en cuenta de prueba
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def activate_subscription(email: str):
    """Activate subscription for a test user"""
    print(f"\n{'='*80}")
    print(f"ACTIVATING SUBSCRIPTION FOR TEST USER")
    print(f"{'='*80}\n")
    
    # Find user
    user = await db.users.find_one({"email": email})
    
    if not user:
        print(f"❌ User with email {email} not found")
        print(f"\nAvailable users:")
        users = await db.users.find({}, {"email": 1, "name": 1, "_id": 0}).to_list(10)
        for u in users:
            print(f"   - {u.get('email')} ({u.get('name', 'No name')})")
        return
    
    print(f"✅ User found: {user.get('name')} ({user.get('email')})")
    print(f"   Current subscription status: {user.get('subscription_status', 'inactive')}")
    
    # Update subscription
    result = await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "subscription_status": "active",
                "last_login": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"\n✅ Subscription activated successfully!")
        print(f"   Status: active")
        print(f"   User can now generate exams")
    else:
        print(f"\n⚠️  User already had active subscription or no changes needed")
    
    # Verify
    updated_user = await db.users.find_one({"email": email}, {"_id": 0})
    print(f"\n📊 FINAL USER STATUS:")
    print(f"   Name: {updated_user.get('name')}")
    print(f"   Email: {updated_user.get('email')}")
    print(f"   Subscription: {updated_user.get('subscription_status')}")
    print(f"   Stripe Customer ID: {updated_user.get('stripe_customer_id', 'None')}")
    
    print(f"\n{'='*80}")
    print(f"READY FOR TESTING!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python activate_test_subscription.py <email>")
        print("\nExample:")
        print("  python activate_test_subscription.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(activate_subscription(email))
