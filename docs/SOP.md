# Customer Experience SOP

## Tools
- **Google Cloud Firestore:** `customers`, `orders`, `otps`, `policies` collections
- **Cloud Firestore OTP Engine:** identity verification (6-digit OTP with 2-strike lockout) — required before any account-specific action
- **Google Agent Platform:** semantic policy search (RAG) powered by `text-embedding-004`

## Step 0 — Common Intake (every conversation)
1. Greet customer, ask what they need.
2. Classify intent: order status / return-refund / general policy question / password reset.
3. If the request touches account or order specifics (status, refund, password reset) → verify identity first:
   - Ask for order number or account email.
   - Send OTP via Cloud Firestore (`send_auth_code`).
   - Customer enters code → verify via `verify_auth_code`.
   - 2 failed attempts → account locked in Firestore, escalate to human.
4. Pure policy questions (shipping cost, return window, etc.) skip verification — answer straight from the knowledge base via `search_policy_kb`.

## Use Case 1 — Order Status
1. Collect order number (or email to search by).
2. Verify identity.
3. Look up order in `Orders` sheet by order ID.
4. Confirm the record belongs to the verified email.
5. Read status (Processing / Shipped / Out for Delivery / Delivered / Delayed).
6. If shipped → give carrier, tracking number, ETA.
7. If delayed → apologize, explain if reason known, offer updated ETA or escalation.
8. If not found → ask customer to recheck order number or search by email.
9. Close, ask if anything else is needed.

## Use Case 2 — Return / Refund
1. Verify identity.
2. Ask for order number and which item(s).
3. Look up order, check eligibility: not a final-sale item, and within the 30-day return window
   from the order date.
4. Ask reason: damaged/defective, wrong item, no longer wanted, other.
5. Branch:
   - Damaged/defective/wrong item → offer refund or replacement, no return shipping charge.
   - No longer wanted → check category isn't final-sale, customer covers return shipping.
6. If eligible → mark the order as return-requested in the Cloud Firestore `orders` collection.
7. Give customer next steps: bring the book and the emailed QR code to a USPS, UPS, or FedEx
   store, no printer needed.
8. If not eligible → explain policy, offer store credit or escalate.
9. Close, confirm refund amount and timeline (5–7 business days after receipt).

## Use Case 3 — General Questions

### Shipping/policy
1. Identify the specific question.
2. Look up answer in the knowledge base via `search_policy_kb`.
3. Answer directly, no verification.
4. If it's account-specific ("what's *my* shipping status") → route into Use Case 1.

### Password reset
1. Ask for account email.
2. Send Firestore OTP to email on file (`send_auth_code`) — this verifies account ownership.
3. On verification (`verify_auth_code`), provide secure reset instructions.
4. Confirm to customer it's sent.
5. If email not found → ask to check for typos or try alternate email, escalate if it still fails.

## Escalation (applies to all)
- Customer explicitly asks for a human.
- Identity verification fails twice.
- Situation not covered by policy (fraud suspicion, large order, VIP).
- Order shows "Delivered" but the customer explicitly says they never received it — escalate
  immediately, no troubleshooting first (possible lost/stolen package).
- Agent isn't confident and clarification doesn't resolve it.
→ Hand off with a conversation summary.

## Guardrails
- Never issue gift cards, discounts, or refunds outside of the return-eligibility check above.
- Never grant a return based on the customer's word alone — always verify against the order data.

## Data Schema
- `Orders`: order_number, order_date, shipping_status, customer_name, customer_id,
  address_shipped_to, book_ordered, category, return_eligible_30_day, return_status, customer_email
- `Customers`: customer_id, name, email, phone, home_address
