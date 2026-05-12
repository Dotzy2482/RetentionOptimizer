import os
import firebase_admin
from firebase_admin import credentials, messaging

_CREDS_PATH = os.path.join(os.path.dirname(__file__), "..", "firebase_credentials.json.json")
_initialized = False


def _ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return
    cred = credentials.Certificate(os.path.abspath(_CREDS_PATH))
    firebase_admin.initialize_app(cred)
    _initialized = True


def send_push(token: str, title: str, body: str) -> bool:
    """Send a single FCM push notification. Returns True on success, False on failure."""
    _ensure_initialized()
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                channel_id="retention_coupons",
                priority="high",
            )
        ),
        token=token,
    )
    try:
        messaging.send(message)
        return True
    except Exception as e:
        print(f"FCM gonderim hatasi (token={token[:20]}...): {e}")
        return False
