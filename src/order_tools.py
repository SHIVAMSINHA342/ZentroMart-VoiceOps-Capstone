"""Order lookup with verification gates for ZentroMart VoiceOps."""
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def _lookup_function():
    try:
        from tools.tools import lookup_order
    except ImportError as exc:
        raise RuntimeError(
            "Could not import the supplied synthetic order lookup tool."
        ) from exc
    return lookup_order


def start_order_verification(order_id):
    order_id = str(order_id).strip()
    if not order_id:
        return {
            "order_id": "",
            "status": "invalid_request",
            "verified": False,
            "retries_used": 0,
            "message": "Please provide an order ID."
        }

    result = _lookup_function()(order_id)
    # Do not store or return order details before verification.
    return {
        "order_id": order_id,
        "status": "awaiting_verification",
        "verified": False,
        "retries_used": 0,
        "message": result.get(
            "message",
            "Please provide the requested verification detail."
        )
    }


def submit_order_verification(session, verification_value):
    if session.get("status") == "verified" and session.get("verified") is True:
        return {"success": True, "message": "Session already verified."}

    if session.get("status") == "verification_failed":
        return {
            "success": False,
            "message": "Verification attempts are exhausted. Please contact support."
        }

    if session.get("status") != "awaiting_verification":
        return {
            "success": False,
            "message": "Start a valid verification session first."
        }

    result = _lookup_function()(
        session["order_id"],
        verification_value=verification_value
    )

    if result.get("found") is True and result.get("verified") is True:
        session["verified"] = True
        session["status"] = "verified"
        session["verified_order"] = result
        return {"success": True, "message": "Verification successful."}

    session["retries_used"] = int(session.get("retries_used", 0)) + 1
    if session["retries_used"] >= 2:
        session["status"] = "verification_failed"
        message = "Verification failed. Please contact support."
    else:
        message = "Verification did not match. One attempt remains."

    return {
        "success": False,
        "message": message,
        "attempts_used": session["retries_used"]
    }


def get_verified_order(session):
    if (
        session.get("status") != "verified"
        or session.get("verified") is not True
        or not isinstance(session.get("verified_order"), dict)
        or session["verified_order"].get("verified") is not True
    ):
        return {
            "success": False,
            "message": "Order details are unavailable until verification succeeds."
        }

    return {"success": True, "order": session["verified_order"]}
