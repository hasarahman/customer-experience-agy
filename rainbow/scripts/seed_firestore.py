# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Seeds sample customer and order data directly into Cloud Firestore on project has-demo-500917.

Usage:
    python3 rainbow/scripts/seed_firestore.py
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "has-demo-500917")


def main():
    print(f"Connecting to Cloud Firestore for project '{PROJECT_ID}'...")
    try:
        from google.cloud import firestore
        db = firestore.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"Failed to connect to live Firestore: {e}")
        return

    today = date.today().isoformat()
    past_45_days = (date.today() - timedelta(days=45)).isoformat()

    # Seed Customers
    customers = [
        {
            "customer_id": "CUST-001",
            "name": "Hasan Rahman",
            "email": "hasan2296@outlook.com",
            "phone": "+1-503-555-0142",
            "home_address": "482 Elm Street, Portland, OR 97205",
        },
        {
            "customer_id": "CUST-002",
            "name": "Marcus Johnson",
            "email": "marcus.j@example.com",
            "phone": "+1-206-555-0198",
            "home_address": "714 Pine Ave, Seattle, WA 98101",
        },
    ]

    print(f"Seeding {len(customers)} customers into 'customers' collection...")
    for cust in customers:
        db.collection("customers").document(cust["customer_id"]).set(cust)
        print(f"  - Seeded customer: {cust['customer_id']} ({cust['name']})")

    # Seed Orders
    orders = [
        {
            "order_number": "BK-10001",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "The Midnight Library",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "USPS",
            "tracking_number": "9400111899223192000001",
            "return_eligible_30_day": "Yes",
            "return_status": "None",
        },
        {
            "order_number": "BK-10002",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "Project Hail Mary",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Processing",
            "carrier": "",
            "tracking_number": "",
            "return_eligible_30_day": "Yes",
            "return_status": "None",
        },
        {
            "order_number": "BK-10003",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "First Edition Atlas",
            "category": "Rare/Collectible",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "FedEx",
            "tracking_number": "780123456789",
            "return_eligible_30_day": "No",
            "return_status": "None",
        },
        {
            "order_number": "BK-10006",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "Rare Poetry Edition",
            "category": "Clearance",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "UPS",
            "tracking_number": "1Z9999999999999999",
            "return_eligible_30_day": "No",
            "return_status": "None",
        },
        {
            "order_number": "BK-10015",
            "order_date": today,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "Dune Messiah",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Processing",
            "carrier": "",
            "tracking_number": "",
            "return_eligible_30_day": "Yes",
            "return_status": "None",
        },
        {
            "order_number": "BK-10099",
            "order_date": past_45_days,
            "customer_id": "CUST-001",
            "customer_name": "Hasan Rahman",
            "customer_email": "hasan2296@outlook.com",
            "book_ordered": "The Great Gatsby",
            "category": "Fiction",
            "address_shipped_to": "482 Elm Street, Portland, OR 97205",
            "shipping_status": "Delivered",
            "carrier": "USPS",
            "tracking_number": "9400111899223192000099",
            "return_eligible_30_day": "Yes",
            "return_status": "None",
        },
    ]

    print(f"Seeding {len(orders)} orders into 'orders' collection...")
    for ord_doc in orders:
        db.collection("orders").document(ord_doc["order_number"]).set(ord_doc)
        print(f"  - Seeded order: {ord_doc['order_number']} ({ord_doc['book_ordered']})")

    print("Firestore seeding complete.")


if __name__ == "__main__":
    main()
