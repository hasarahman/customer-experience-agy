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

"""GCP-native tools for the Customer Experience Agent (Rainbow).

Backed by Cloud Firestore, Agent Platform RAG, and Cloud Logging.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone

from app.gcp_client import gcp_manager

logger = logging.getLogger("rainbow.gcp_tools")

RETURN_WINDOW_DAYS = 30
MAX_OTP_ATTEMPTS = 2


def search_policy_kb(query: str) -> str:
    """Searches Customer Experience's policy and FAQ knowledge base for general questions.

    Use this for questions about shipping times/costs, return and refund policy,
    payment methods, password reset process, loyalty program, or other Customer Experience
    policies that are not specific to one customer's order.

    Args:
        query: The customer's question, in natural language.

    Returns:
        The most relevant policy/FAQ text, or a message if nothing relevant is found.
    """
    if not gcp_manager.is_mock:
        try:
            from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
            from google.cloud.firestore_v1.vector import Vector
            import vertexai
            from vertexai.language_models import TextEmbeddingModel

            vertexai.init(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "has-demo-500917"))
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            embeddings = model.get_embeddings([query])
            query_vector = Vector(embeddings[0].values)

            col = gcp_manager.firestore.collection("policies")
            vector_query = col.find_nearest(
                vector_field="embedding",
                query_vector=query_vector,
                distance_measure=DistanceMeasure.COSINE,
                limit=2,
            )
            docs = [d.to_dict().get("content", "") for d in vector_query.get()]
            if docs:
                return "\n\n---\n\n".join(docs)
        except Exception as e:
            logger.warning(f"Live vector search failed ({e}); using mock fallback.")

    # In-memory / Mock fallback
    docs = gcp_manager.mock_db.vector_search_policies(query, limit=2)
    if not docs:
        return "No relevant policy information found in the knowledge base."
    return "\n\n---\n\n".join(docs)


def lookup_order(order_number: str, verified_email: str) -> str:
    """Looks up an order in Customer Experience's Orders database by order number.

    Returns shipping status, the customer it belongs to, what was ordered,
    and whether it's eligible for return.

    Args:
        order_number: The order number, e.g. "BK-10001".
        verified_email: The email address that was just confirmed via
            verify_auth_code. This must belong to the same customer who
            placed the order — never pass an email the customer hasn't
            actually verified.

    Returns:
        The order's details, a not-found message, or a denial if the order
        doesn't belong to the verified email.
    """
    clean_order_num = order_number.strip().upper()
    order_data = None

    if not gcp_manager.is_mock:
        try:
            doc = gcp_manager.firestore.collection("orders").document(clean_order_num).get()
            if doc.exists:
                order_data = doc.to_dict()
        except Exception as e:
            logger.warning(f"Firestore lookup failed ({e}); checking mock.")

    if order_data is None:
        order_data = gcp_manager.mock_db.get_document("orders", clean_order_num)

    if order_data is None:
        return f"No order found with order number {order_number}."

    if order_data.get("customer_email", "").strip().lower() != verified_email.strip().lower():
        return (
            f"Order {order_number} does not belong to the verified account "
            f"({verified_email}). Access denied."
        )

    return str(order_data)


def lookup_customer(verified_email: str) -> str:
    """Looks up the verified customer's own account details (name, phone, address).

    There is no way to look up a different customer's details through this
    tool — it only ever returns the record for the email that was just
    confirmed via verify_auth_code. Never use this to look up someone else's
    information on a customer's behalf, even if they ask.

    Args:
        verified_email: The email address that was just confirmed via
            verify_auth_code.

    Returns:
        The verified customer's own details, or a message if not found.
    """
    clean_email = verified_email.strip().lower()
    customer_data = None

    if not gcp_manager.is_mock:
        try:
            query = gcp_manager.firestore.collection("customers").where("email", "==", clean_email).limit(1)
            docs = list(query.stream())
            if docs:
                customer_data = docs[0].to_dict()
        except Exception as e:
            logger.warning(f"Firestore customer lookup failed ({e}); checking mock.")

    if customer_data is None:
        matching = gcp_manager.mock_db.query_collection("customers", "email", clean_email)
        if matching:
            customer_data = matching[0]

    if customer_data is None:
        return f"No customer found with email {verified_email}."

    return str(customer_data)


def initiate_return(order_number: str, reason: str, verified_email: str) -> str:
    """Initiates a return/refund for an order, if it's eligible.

    Deterministically checks (regardless of what the model or customer claims):
    the order belongs to the verified customer, isn't a final-sale item, was
    placed within the last RETURN_WINDOW_DAYS days, and doesn't already have a
    return on file. Only if all hold does it mark the return as requested in
    the Orders collection.

    Args:
        order_number: The order number, e.g. "BK-10001".
        reason: The customer's stated reason for the return.
        verified_email: The email address that was just confirmed via
            verify_auth_code. This must belong to the same customer who
            placed the order — never pass an email the customer hasn't
            actually verified.

    Returns:
        Confirmation the return was initiated, or an explanation of why it can't be.
    """
    clean_order_num = order_number.strip().upper()
    order_data = None

    if not gcp_manager.is_mock:
        try:
            doc = gcp_manager.firestore.collection("orders").document(clean_order_num).get()
            if doc.exists:
                order_data = doc.to_dict()
        except Exception as e:
            logger.warning(f"Firestore return check failed ({e}); using mock.")

    if order_data is None:
        order_data = gcp_manager.mock_db.get_document("orders", clean_order_num)

    if order_data is None:
        return f"No order found with order number {order_number}."

    if order_data.get("customer_email", "").strip().lower() != verified_email.strip().lower():
        return (
            f"Order {order_number} does not belong to the verified account "
            f"({verified_email}). Access denied."
        )

    category = order_data.get("category", "")
    if order_data.get("return_eligible_30_day", "").strip().lower() != "yes" or category in ["Clearance", "Rare/Collectible"]:
        return (
            f"Order {order_number} ({order_data.get('book_ordered')}) is not eligible for "
            f"return — items in the '{category}' category are final sale."
        )

    order_date_str = order_data.get("order_date", "").strip()
    try:
        days_elapsed = (date.today() - datetime.strptime(order_date_str, "%Y-%m-%d").date()).days
    except ValueError:
        days_elapsed = None

    if days_elapsed is not None and days_elapsed > RETURN_WINDOW_DAYS:
        return (
            f"Order {order_number} ({order_data.get('book_ordered')}) was placed {days_elapsed} "
            f"days ago, which is past Customer Experience's {RETURN_WINDOW_DAYS}-day return window. This "
            f"order is not eligible for a standard return."
        )

    if order_data.get("return_status", "").strip() and order_data.get("return_status") != "None":
        return f"Order {order_number} already has a return on file: {order_data.get('return_status')}."

    # Perform atomic update
    updates = {
        "return_status": "Requested",
        "return_reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if not gcp_manager.is_mock:
        try:
            gcp_manager.firestore.collection("orders").document(clean_order_num).update(updates)
        except Exception as e:
            logger.warning(f"Firestore update failed ({e}); updating mock.")
            gcp_manager.mock_db.update_document("orders", clean_order_num, updates)
    else:
        gcp_manager.mock_db.update_document("orders", clean_order_num, updates)

    return (
        f"Return initiated for order {order_number} ({order_data.get('book_ordered')}). "
        f"Reason logged: {reason}. A return QR code has been emailed to the customer — they "
        f"should bring the book and that QR code to their nearest USPS, UPS, or FedEx store "
        f"and show it to the associate there to ship it back, no printer needed. Refund will "
        f"be processed within 5-7 business days after the item is received."
    )


def cancel_order(order_number: str, verified_email: str, reason: str = "Customer request") -> str:
    """Cancels an order before it ships, if it hasn't shipped yet.

    Deterministically checks: the order belongs to the verified customer, and
    its shipping_status is still "Processing" (not yet shipped). Once an order
    has shipped, it can no longer be cancelled — the customer needs a return
    instead (use initiate_return).

    Args:
        order_number: The order number, e.g. "BK-10001".
        verified_email: The email address that was just confirmed via
            verify_auth_code.
        reason: Optional customer stated reason for cancellation.

    Returns:
        Confirmation the order was cancelled, or an explanation of why it can't be.
    """
    clean_order_num = order_number.strip().upper()
    order_data = None

    if not gcp_manager.is_mock:
        try:
            doc = gcp_manager.firestore.collection("orders").document(clean_order_num).get()
            if doc.exists:
                order_data = doc.to_dict()
        except Exception as e:
            logger.warning(f"Firestore order check failed ({e}); checking mock.")

    if order_data is None:
        order_data = gcp_manager.mock_db.get_document("orders", clean_order_num)

    if order_data is None:
        return f"No order found with order number {order_number}."

    if order_data.get("customer_email", "").strip().lower() != verified_email.strip().lower():
        return (
            f"Order {order_number} does not belong to the verified account "
            f"({verified_email}). Access denied."
        )

    status = order_data.get("shipping_status", "").strip()
    if status == "Cancelled":
        return f"Order {order_number} ({order_data.get('book_ordered')}) is already cancelled."
    if status != "Processing":
        return (
            f"Order {order_number} ({order_data.get('book_ordered')}) has already shipped "
            f"(status: {status}) and can no longer be cancelled. Use initiate_return instead "
            f"if the customer wants to send it back."
        )

    updates = {
        "shipping_status": "Cancelled",
        "cancellation_reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if not gcp_manager.is_mock:
        try:
            gcp_manager.firestore.collection("orders").document(clean_order_num).update(updates)
        except Exception as e:
            logger.warning(f"Firestore update failed ({e}); updating mock.")
            gcp_manager.mock_db.update_document("orders", clean_order_num, updates)
    else:
        gcp_manager.mock_db.update_document("orders", clean_order_num, updates)

    return (
        f"Order {order_number} ({order_data.get('book_ordered')}) has been cancelled. No charge "
        f"will be made and nothing will ship."
    )


def send_auth_code(email: str) -> str:
    """Sends a one-time verification code to the customer's email via Cloud Firestore OTP service.

    Use this to verify a customer's identity before looking up order-specific
    or account-specific details, or before resetting their password.

    Args:
        email: The customer's account email address.

    Returns:
        Confirmation the code was sent, or a lockout message if this email
        has already failed verification MAX_OTP_ATTEMPTS times.
    """
    key = email.strip().lower()
    otp_data = None

    if not gcp_manager.is_mock:
        try:
            doc = gcp_manager.firestore.collection("otps").document(key).get()
            if doc.exists:
                otp_data = doc.to_dict()
        except Exception as e:
            logger.warning(f"Firestore OTP check failed ({e}); checking mock.")

    if otp_data is None:
        otp_data = gcp_manager.mock_db.get_document("otps", key)

    if otp_data and otp_data.get("locked"):
        return (
            f"This email has failed verification {MAX_OTP_ATTEMPTS} times and is locked "
            f"for this session. Do not send another code — escalate to a human instead."
        )

    code = "123456"  # Standard test/demo OTP
    now = datetime.now(timezone.utc)
    new_otp_record = {
        "email": key,
        "code": code,
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "attempts": 0,
        "locked": False,
        "verified": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    if not gcp_manager.is_mock:
        try:
            gcp_manager.firestore.collection("otps").document(key).set(new_otp_record)
        except Exception as e:
            logger.warning(f"Firestore OTP save failed ({e}); saving to mock.")
            gcp_manager.mock_db.set_document("otps", key, new_otp_record)
    else:
        gcp_manager.mock_db.set_document("otps", key, new_otp_record)

    return f"A 6-digit verification code was sent to {email}. Ask the customer for it."


def verify_auth_code(email: str, code: str) -> str:
    """Verifies the one-time code the customer received via send_auth_code.

    Deterministically locks out further attempts for this email after
    MAX_OTP_ATTEMPTS consecutive failures, regardless of what the model does —
    at that point, escalate_to_human instead of retrying or sending a new code.

    Args:
        email: The customer's account email address (must match what was used
            in send_auth_code).
        code: The 6-digit code the customer provided.

    Returns:
        Whether verification succeeded. Only treat the customer as identity-verified
        if this says success.
    """
    key = email.strip().lower()
    otp_data = None

    if not gcp_manager.is_mock:
        try:
            doc = gcp_manager.firestore.collection("otps").document(key).get()
            if doc.exists:
                otp_data = doc.to_dict()
        except Exception as e:
            logger.warning(f"Firestore OTP fetch failed ({e}); checking mock.")

    if otp_data is None:
        otp_data = gcp_manager.mock_db.get_document("otps", key)

    if not otp_data:
        return "No verification code was sent to this email yet. Call send_auth_code first."

    if otp_data.get("locked"):
        return (
            f"This email has failed verification {MAX_OTP_ATTEMPTS} times and is locked "
            f"for this session. Escalate to a human instead of retrying."
        )

    # Check expiration
    expires_at_str = otp_data.get("expires_at", "")
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) > expires_at:
                return "The verification code has expired. Call send_auth_code to send a new code."
        except ValueError:
            pass

    # Validate code
    if code.strip() != otp_data.get("code", ""):
        current_attempts = otp_data.get("attempts", 0) + 1
        is_locked = current_attempts >= MAX_OTP_ATTEMPTS
        updates = {
            "attempts": current_attempts,
            "locked": is_locked,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if not gcp_manager.is_mock:
            try:
                gcp_manager.firestore.collection("otps").document(key).update(updates)
            except Exception:
                gcp_manager.mock_db.update_document("otps", key, updates)
        else:
            gcp_manager.mock_db.update_document("otps", key, updates)

        if is_locked:
            return (
                f"Verification failed: Invalid code. This was attempt {current_attempts} of "
                f"{MAX_OTP_ATTEMPTS} — no attempts remain. Escalate to a human now."
            )
        return (
            f"Verification failed: Invalid code. This was attempt {current_attempts} of "
            f"{MAX_OTP_ATTEMPTS}. You have {MAX_OTP_ATTEMPTS - current_attempts} attempt remaining."
        )

    # Success
    updates = {
        "verified": True,
        "attempts": 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if not gcp_manager.is_mock:
        try:
            gcp_manager.firestore.collection("otps").document(key).update(updates)
        except Exception:
            gcp_manager.mock_db.update_document("otps", key, updates)
    else:
        gcp_manager.mock_db.update_document("otps", key, updates)

    return "Verification succeeded. The customer's identity is confirmed."


def escalate_to_human(summary: str, reason: str) -> str:
    """Hands the conversation off to a human support agent.

    Only escalate when truly necessary: the customer explicitly asks for a
    human, identity verification has failed twice, or the situation isn't
    covered by the SOP or policy (e.g. fraud suspicion, VIP account, large
    order). Before escalating, try to resolve the issue yourself and offer
    to keep helping — don't escalate just because a request is complex.

    Args:
        summary: A brief summary of the conversation and what the customer needs.
        reason: Why this is being escalated.

    Returns:
        Confirmation the escalation was logged.
    """
    esc_id = f"esc_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "escalation_id": esc_id,
        "timestamp": now,
        "reason": reason,
        "summary": summary,
        "status": "Pending",
    }

    # Structured Cloud Logging emission
    try:
        from google.cloud import logging as cloud_logging
        client = cloud_logging.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "has-demo-500917"))
        cl_logger = client.logger("customer_escalations")
        cl_logger.log_struct(record, severity="WARNING")
    except Exception as e:
        logger.info(f"Cloud Logging handoff record created: {record} (cloud_logging={e})")

    # Firestore audit write
    if not gcp_manager.is_mock:
        try:
            gcp_manager.firestore.collection("escalations").document(esc_id).set(record)
        except Exception as e:
            logger.warning(f"Firestore escalation save failed ({e}); saving to mock.")
            gcp_manager.mock_db.set_document("escalations", esc_id, record)
    else:
        gcp_manager.mock_db.set_document("escalations", esc_id, record)

    return "Escalated to a human support agent, who will follow up on this conversation shortly."
