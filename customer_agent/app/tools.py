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

"""Tools module for the Customer Experience Agent.

All tools connect directly to Google Cloud Platform services:
- Cloud Firestore (otps, customers, orders)
- Agent Platform RAG (policies)
- Cloud Logging
"""

from app.gcp_tools import (
    RETURN_WINDOW_DAYS,
    MAX_OTP_ATTEMPTS,
    cancel_order,
    escalate_to_human,
    find_orders_by_email,
    initiate_return,
    lookup_customer,
    lookup_order,
    search_policy_kb,
    send_auth_code,
    verify_auth_code,
)

__all__ = [
    "RETURN_WINDOW_DAYS",
    "MAX_OTP_ATTEMPTS",
    "cancel_order",
    "escalate_to_human",
    "find_orders_by_email",
    "initiate_return",
    "lookup_customer",
    "lookup_order",
    "search_policy_kb",
    "send_auth_code",
    "verify_auth_code",
]
