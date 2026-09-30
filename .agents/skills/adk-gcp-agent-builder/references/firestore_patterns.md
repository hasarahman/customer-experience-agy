# Firestore Patterns for ADK Agents

This reference covers schema patterns, atomic transactions, and state management when using Cloud Firestore as the operational backbone for Google ADK agents.

---

## 1. Document Collection Architecture

| Collection | Document ID Pattern | Document Schema Highlights | Purpose |
| :--- | :--- | :--- | :--- |
| `customers` | `CUST-XXX` or email | `name`, `email`, `phone`, `shipping_address`, `loyalty_tier` | Identity and contact records. |
| `orders` | `ORD-XXXXX` | `customer_id`, `customer_email`, `status`, `items`, `tracking_number`, `delivery_date`, `is_final_sale`, `return_status` | Operational transactions and return tracking. |
| `otps` | `{customer_email}` | `code`, `attempts`, `locked`, `expires_at`, `verified` | Ephemeral authentication state and lockout enforcement. |
| `policies` | `policy_{idx}_{slug}` | `section`, `content`, `embedding` (768-dim list of floats) | RAG knowledge base chunks for vector search. |

---

## 2. Stateful OTP & Lockout Pattern

To enforce zero unauthorized access to customer records without complex OAuth flows in conversational interfaces:

1. **Step 1: Request Email**:
   Agent calls `send_auth_code(email)`. Generates a 6-digit OTP, stores it in `otps/{email}` with `attempts: 0`, `locked: false`, `verified: false`.
2. **Step 2: Lockout Enforcement**:
   When `verify_auth_code(email, code)` is invoked:
   - If `doc["locked"] == True`: Immediately fail with instruction to escalate to human.
   - If `code` does not match: Increment `attempts += 1`.
   - If `attempts >= 2`: Set `locked: True` and immediately return lockout error.
   - If code matches: Set `verified: True`, `attempts: 0`.
3. **Step 3: Gated Tool Execution**:
   Tools such as `lookup_order`, `initiate_return`, and `cancel_order` require `verified_email: str` and verify that `otps/{verified_email}.get("verified") == True` before querying or mutating data.

---

## 3. Atomic Order Mutation & Validation

When updating stateful attributes (such as initiating a return or cancellation):

```python
def initiate_return(order_id: str, verified_email: str, reason: str = "") -> dict:
    db = gcp_manager.firestore
    doc_ref = db.collection("orders").document(order_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return {"success": False, "error": f"Order {order_id} not found."}
    
    order = doc.to_dict()
    # 1. Authorization check
    if order.get("customer_email") != verified_email:
        return {"success": False, "error": "Order does not belong to verified email."}
    
    # 2. Final sale check
    if order.get("is_final_sale"):
        return {"success": False, "error": "This item was marked final sale and is not eligible for return."}
    
    # 3. Already returned check
    if order.get("return_status") in ("Requested", "Completed"):
        return {"success": False, "error": f"A return is already {order['return_status']} for this order."}
        
    # 4. State mutation
    doc_ref.update({
        "return_status": "Requested",
        "return_reason": reason,
        "return_requested_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True, "message": f"Return requested for order {order_id}."}
```

---

## 4. Test State Isolation & Teardown

Because integration tests run against live Cloud Firestore, mutations persist across runs. To prevent cascading failures:

```python
class TestFirestoreParity(unittest.TestCase):
    def setUp(self):
        # Always reset mutable state before each test
        db = gcp_manager.firestore
        db.collection("orders").document("ORD-1001").update({
            "return_status": "None",
            "status": "Delivered"
        })
        # Use isolated emails for lockout tests to avoid locking shared test records
        self.lockout_email = f"lockout.{int(time.time())}@example.com"
```
