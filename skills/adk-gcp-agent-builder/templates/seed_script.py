"""Generic Firestore Seeding Script for ADK Agent Datastore.

Seeds customers, transactional records (orders), and initial authentication state.
"""

import os
import sys
from datetime import datetime, timezone

# Ensure your app package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.gcp_client import gcp_manager


def seed_database():
    db = gcp_manager.firestore
    print(f"Seeding Firestore using live GCP: {gcp_manager.is_live_gcp}")

    # 1. Seed Customer
    customer_id = "CUST-001"
    customer_data = {
        "customer_id": customer_id,
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1-555-0199",
        "shipping_address": {
            "street": "100 Market Street",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.collection("customers").document(customer_id).set(customer_data)
    print(f"✓ Seeded customer: {customer_id} ({customer_data['email']})")

    # 2. Seed Sample Orders
    orders = [
        {
            "order_id": "ORD-1001",
            "customer_id": customer_id,
            "customer_email": "jane.doe@example.com",
            "customer_name": "Jane Doe",
            "item_name": "Ergonomic Wireless Keyboard",
            "status": "Delivered",
            "tracking_number": "1Z9999999999999999",
            "carrier": "UPS",
            "delivery_date": "2026-09-15T12:00:00Z",
            "is_final_sale": False,
            "return_status": "None",
        },
        {
            "order_id": "ORD-1002",
            "customer_id": customer_id,
            "customer_email": "jane.doe@example.com",
            "customer_name": "Jane Doe",
            "item_name": "Noise Cancelling Headphones",
            "status": "Shipped",
            "tracking_number": "9400111899223192000001",
            "carrier": "USPS",
            "is_final_sale": False,
            "return_status": "None",
        },
    ]

    for order in orders:
        db.collection("orders").document(order["order_id"]).set(order)
        print(f"✓ Seeded order: {order['order_id']}")

    # 3. Seed Default OTP state
    otp_data = {
        "email": "jane.doe@example.com",
        "code": "123456",
        "attempts": 0,
        "locked": False,
        "verified": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.collection("otps").document("jane.doe@example.com").set(otp_data)
    print("✓ Seeded verified OTP state for jane.doe@example.com (code: 123456)")

    print("\nDatabase seeding completed successfully.")


if __name__ == "__main__":
    seed_database()
