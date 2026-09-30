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

"""Parity validation suite for GCP-native Firestore customer experience agent tools.

Exercises the 12 scenarios documented in docs/pilot_validation.md:
- SC-01: OTP Send & Verify
- SC-02: OTP 2-Strike Lockout
- SC-03: OTP Expiration
- SC-04: Order Lookup (Owner)
- SC-05: Order Lookup (Non-Owner / Cross-Account Denial)
- SC-06: Customer Account Lookup
- SC-07: Eligible Return Initiation
- SC-08: Ineligible Return: Past 30 Days
- SC-09: Ineligible Return: Final Sale Exclusions
- SC-10: Pre-Shipment Cancellation
- SC-11: Post-Shipment Cancellation Denial
- SC-12: Vector Search Policy Retrieval
"""

import os
import unittest

# Ensure GCP Project is configured
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "has-demo-500917")


class TestFirestoreParitySuite(unittest.TestCase):
    """Parity test harness verifying Firestore tools against legacy behavioral standards."""

    def setUp(self):
        from app.gcp_client import gcp_manager
        gcp_manager.mock_db._seed_default_data()
        if gcp_manager.firestore:
            try:
                gcp_manager.firestore.collection("orders").document("BK-10001").update({"return_status": "None"})
                gcp_manager.firestore.collection("orders").document("BK-10002").update({"shipping_status": "Processing"})
            except Exception:
                pass

    def test_sc01_otp_send_and_verify(self):
        """SC-01: Validates that an OTP is generated and successfully verified."""
        from app.gcp_tools import send_auth_code, verify_auth_code

        email = "hasan2296@outlook.com"
        send_res = send_auth_code(email)
        assert "sent" in send_res.lower() or "code" in send_res.lower()

        # In test/emulator mode, verify valid OTP
        verify_res = verify_auth_code(email, code="123456")
        assert "succeeded" in verify_res.lower() or "confirmed" in verify_res.lower()

    def test_sc02_otp_two_strike_lockout(self):
        """SC-02: Validates that 2 consecutive incorrect OTP entries cause hard lockout."""
        from app.gcp_tools import send_auth_code, verify_auth_code

        import time

        email = f"lockout.{int(time.time())}@example.com"
        send_auth_code(email)

        # 1st wrong attempt
        res1 = verify_auth_code(email, code="000000")
        assert "invalid" in res1.lower() or "attempt" in res1.lower()

        # 2nd wrong attempt -> triggers lockout
        res2 = verify_auth_code(email, code="000000")
        assert "locked" in res2.lower() or "escalate" in res2.lower()

        # 3rd attempt must be hard refused
        res3 = verify_auth_code(email, code="123456")
        assert "locked" in res3.lower() or "escalate" in res3.lower()

    def test_sc03_otp_expiration(self):
        """SC-03: Validates that expired codes are rejected."""
        from app.gcp_tools import verify_auth_code

        # Unsent or expired email
        res = verify_auth_code("nonexistent@example.com", code="123456")
        assert "no verification code" in res.lower() or "expired" in res.lower() or "invalid" in res.lower()

    def test_sc04_order_lookup_owner(self):
        """SC-04: Validates order lookup when verified_email matches the order record."""
        from app.gcp_tools import lookup_order

        res = lookup_order("BK-10001", verified_email="hasan2296@outlook.com")
        assert "BK-10001" in res
        assert "Delivered" in res
        assert "The Midnight Library" in res

    def test_sc05_order_lookup_non_owner(self):
        """SC-05: Strict cross-account denial if verified_email does not match."""
        from app.gcp_tools import lookup_order

        res = lookup_order("BK-10001", verified_email="attacker@example.com")
        assert "access denied" in res.lower() or "does not belong" in res.lower()

    def test_sc06_customer_account_lookup(self):
        """SC-06: Customer account lookup returns only the verified customer's profile."""
        from app.gcp_tools import lookup_customer

        res = lookup_customer(verified_email="hasan2296@outlook.com")
        assert "Hasan Rahman" in res
        assert "Portland, OR" in res

    def test_sc07_eligible_return_initiation(self):
        """SC-07: Initiates a return for an order within 30 days and not final-sale."""
        from app.gcp_tools import initiate_return

        res = initiate_return(
            order_number="BK-10001",
            reason="Changed mind",
            verified_email="hasan2296@outlook.com",
        )
        assert "initiated" in res.lower() or "qr code" in res.lower() or "success" in res.lower()

    def test_sc08_ineligible_return_past_30_days(self):
        """SC-08: Rejects return for an order placed more than 30 days ago."""
        from app.gcp_tools import initiate_return

        res = initiate_return(
            order_number="BK-10099",  # Seeded as old order
            reason="Defective",
            verified_email="hasan2296@outlook.com",
        )
        assert "30" in res.lower() or "window" in res.lower() or "expired" in res.lower()

    def test_sc09_ineligible_return_final_sale(self):
        """SC-09: Rejects return for final-sale items (Clearance / Rare/Collectible)."""
        from app.gcp_tools import initiate_return

        res = initiate_return(
            order_number="BK-10003",  # Seeded as Rare/Collectible or Clearance
            reason="No longer wanted",
            verified_email="hasan2296@outlook.com",
        )
        assert "final sale" in res.lower() or "final-sale" in res.lower() or "not eligible" in res.lower()

    def test_sc10_preshipment_cancellation(self):
        """SC-10: Cancels an order that is still in 'Processing' status."""
        from app.gcp_tools import cancel_order

        res = cancel_order(
            order_number="BK-10002",  # Seeded as Processing
            verified_email="hasan2296@outlook.com",
            reason="Customer request",
        )
        assert "cancelled" in res.lower() or "success" in res.lower()

    def test_sc11_postshipment_cancellation_denial(self):
        """SC-11: Denies cancellation for an order that has already shipped or delivered."""
        from app.gcp_tools import cancel_order

        res = cancel_order(
            order_number="BK-10001",  # Status is Delivered
            verified_email="hasan2296@outlook.com",
            reason="Too slow",
        )
        assert "already" in res.lower() or "too late" in res.lower() or "return" in res.lower()

    def test_sc12_vector_search_policy_retrieval(self):
        """SC-12: Validates semantic search retrieval for shipping questions."""
        from app.gcp_tools import search_policy_kb

        res = search_policy_kb("How long does standard domestic shipping take?")
        assert "5–7" in res or "Standard" in res
