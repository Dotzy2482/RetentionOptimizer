import requests


class BackendClient:
    """Singleton — FastAPI backend ile HTTP iletişimi."""

    BASE_URL = "http://localhost:8000"
    TIMEOUT = 10

    @classmethod
    def is_alive(cls) -> bool:
        try:
            r = requests.get(f"{cls.BASE_URL}/", timeout=3)
            return r.status_code == 200
        except requests.RequestException:
            return False

    @classmethod
    def list_segments(cls) -> list[dict]:
        r = requests.get(f"{cls.BASE_URL}/api/admin/segments", timeout=cls.TIMEOUT)
        r.raise_for_status()
        return r.json()

    @classmethod
    def send_coupon(cls, segment: str, title: str, message: str,
                    discount_percent: int, days_valid: int = 7,
                    code_prefix: str = "PROMO") -> dict:
        payload = {
            "segment": segment,
            "title": title,
            "message": message,
            "discount_percent": discount_percent,
            "days_valid": days_valid,
            "code_prefix": code_prefix,
        }
        r = requests.post(
            f"{cls.BASE_URL}/api/admin/send-coupon",
            json=payload,
            timeout=cls.TIMEOUT,
        )
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            raise RuntimeError(f"Backend hatasi ({r.status_code}): {detail}")
        return r.json()
