import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import Coupon, NotificationLog, User
from schemas import SendCouponRequest, SendCouponResponse
from services.fcm_push import send_push

router = APIRouter(prefix="/api/admin", tags=["admin"])


def generate_coupon_code(prefix: str) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{suffix}"


@router.post("/send-coupon", response_model=SendCouponResponse)
def send_coupon(req: SendCouponRequest, db: Session = Depends(get_db)):
    target_users = db.execute(
        text("""
            SELECT u.user_id, u.customer_id, u.name
            FROM users u
            JOIN segments s ON u.customer_id = s.customer_id
            WHERE s.segment_label = :segment
        """),
        {"segment": req.segment},
    ).fetchall()

    if not target_users:
        raise HTTPException(
            status_code=404,
            detail=f"'{req.segment}' segmentinde kayitli mobil kullanici bulunamadi.",
        )

    coupon_codes = []
    expires_at = datetime.utcnow() + timedelta(days=req.days_valid)

    # Fetch FCM tokens for all target users in one query
    customer_ids = [u.customer_id for u in target_users]
    token_rows = (
        db.query(User.customer_id, User.fcm_token)
        .filter(User.customer_id.in_(customer_ids))
        .all()
    )
    token_map = {r.customer_id: r.fcm_token for r in token_rows}

    for u in target_users:
        code = generate_coupon_code(req.code_prefix)
        coupon_codes.append(code)

        db.add(
            Coupon(
                customer_id=u.customer_id,
                code=code,
                title=req.title,
                message=req.message,
                discount_percent=req.discount_percent,
                expires_at=expires_at,
            )
        )

        fcm_token = token_map.get(u.customer_id)
        if fcm_token:
            success = send_push(fcm_token, req.title, req.message)
            status = "sent" if success else "failed"
        else:
            status = "no_token"

        db.add(
            NotificationLog(
                customer_id=u.customer_id,
                title=req.title,
                body=req.message,
                status=status,
            )
        )

    db.commit()

    return SendCouponResponse(
        success=True,
        affected_users=len(target_users),
        coupon_codes=coupon_codes,
        message=f"{len(target_users)} kullaniciya kupon tanimlandi.",
    )


@router.get("/segments")
def list_segments(db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            SELECT s.segment_label, COUNT(u.user_id) as user_count
            FROM users u
            JOIN segments s ON u.customer_id = s.customer_id
            GROUP BY s.segment_label
        """)
    ).fetchall()
    return [{"segment": r[0], "user_count": r[1]} for r in result]
