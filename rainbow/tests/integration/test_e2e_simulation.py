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

"""End-to-End integration test simulating a complete multi-turn customer experience lifecycle."""

import os
import unittest

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "has-demo-500917")


class TestEndToEndCustomerJourney(unittest.TestCase):
    """Simulates a real customer navigating intake, verification, order status, return, cancellation, and escalation."""

    def setUp(self):
        from app.gcp_client import gcp_manager
        gcp_manager.mock_db._seed_default_data()
        if gcp_manager.firestore:
            try:
                gcp_manager.firestore.collection("orders").document("BK-10001").update({"return_status": "None"})
                gcp_manager.firestore.collection("orders").document("BK-10015").update({"shipping_status": "Processing"})
            except Exception:
                pass

    def test_full_customer_experience_lifecycle_e2e(self):
        from app.gcp_client import gcp_manager
        from app.gcp_tools import (
            cancel_order,
            escalate_to_human,
            initiate_return,
            lookup_customer,
            lookup_order,
            search_policy_kb,
            send_auth_code,
            verify_auth_code,
        )

        customer_email = "hasan2296@outlook.com"

        # -------------------------------------------------------------
        # Step 1: General Policy Inquiry (Ungated, no auth required)
        # -------------------------------------------------------------
        policy_res = search_policy_kb("What is your standard return and refund window?")
        self.assertTrue(
            "30" in policy_res or "return" in policy_res.lower(),
            f"Policy search should return return window: {policy_res}",
        )

        # -------------------------------------------------------------
        # Step 2: Customer Identity Gating (OTP Send & Verification)
        # -------------------------------------------------------------
        send_res = send_auth_code(customer_email)
        self.assertIn("6-digit verification code was sent", send_res)

        verify_res = verify_auth_code(customer_email, code="123456")
        self.assertIn("Verification succeeded", verify_res)

        # -------------------------------------------------------------
        # Step 3: Verified Account Profile Lookup
        # -------------------------------------------------------------
        profile_res = lookup_customer(verified_email=customer_email)
        self.assertIn("Hasan Rahman", profile_res)
        self.assertIn("Portland, OR", profile_res)

        # -------------------------------------------------------------
        # Step 4: Order Status Inquiry (Delivered Order BK-10001)
        # -------------------------------------------------------------
        order_res = lookup_order("BK-10001", verified_email=customer_email)
        self.assertIn("The Midnight Library", order_res)
        self.assertIn("Delivered", order_res)
        self.assertIn("9400111899223192000001", order_res)

        # -------------------------------------------------------------
        # Step 5: Security Boundary Check (Attacker tries to view BK-10001)
        # -------------------------------------------------------------
        attacker_res = lookup_order("BK-10001", verified_email="malicious@example.com")
        self.assertIn("Access denied", attacker_res)

        # -------------------------------------------------------------
        # Step 6: Return Initiation on Eligible Order BK-10001
        # -------------------------------------------------------------
        return_res = initiate_return(
            order_number="BK-10001",
            reason="I changed my mind",
            verified_email=customer_email,
        )
        self.assertIn("Return initiated for order BK-10001", return_res)
        self.assertIn("return QR code has been emailed", return_res)

        # Verify mutation in database
        if gcp_manager.firestore:
            doc = gcp_manager.firestore.collection("orders").document("BK-10001").get()
            self.assertEqual(doc.to_dict().get("return_status"), "Requested")
        else:
            order_doc = gcp_manager.mock_db.get_document("orders", "BK-10001")
            self.assertEqual(order_doc.get("return_status"), "Requested")

        # -------------------------------------------------------------
        # Step 7: Order Cancellation on Processing Order BK-10015
        # -------------------------------------------------------------
        cancel_res = cancel_order(
            order_number="BK-10015",
            verified_email=customer_email,
            reason="No longer needed",
        )
        self.assertIn("has been cancelled", cancel_res)

        # Verify cancellation state in database
        if gcp_manager.firestore:
            cdoc = gcp_manager.firestore.collection("orders").document("BK-10015").get()
            self.assertEqual(cdoc.to_dict().get("shipping_status"), "Cancelled")
        else:
            cancelled_doc = gcp_manager.mock_db.get_document("orders", "BK-10015")
            self.assertEqual(cancelled_doc.get("shipping_status"), "Cancelled")

        # -------------------------------------------------------------
        # Step 8: Cancellation Denial on Already Delivered Order
        # -------------------------------------------------------------
        cant_cancel_res = cancel_order("BK-10001", verified_email=customer_email)
        self.assertIn("can no longer be cancelled", cant_cancel_res)
        self.assertIn("initiate_return instead", cant_cancel_res)

        # -------------------------------------------------------------
        # Step 9: Final Sale Return Denial on Clearance Item BK-10006
        # -------------------------------------------------------------
        final_sale_res = initiate_return(
            order_number="BK-10006",
            reason="Did not like it",
            verified_email=customer_email,
        )
        self.assertIn("final sale", final_sale_res.lower())

        # -------------------------------------------------------------
        # Step 10: Human Support Escalation (Delivered but Non-Receipt)
        # -------------------------------------------------------------
        esc_res = escalate_to_human(
            summary="Customer Hasan Rahman claims order BK-10001 was never delivered to porch.",
            reason="NON_RECEIPT_DELIVERED",
        )
        self.assertIn("Escalated to a human support agent", esc_res)


if __name__ == "__main__":
    unittest.main()
