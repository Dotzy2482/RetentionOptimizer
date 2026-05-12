from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import User, Coupon
from schemas import UserProfile, CouponResponse, FcmTokenRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{customer_id}/profile", response_model=UserProfile)
def get_profile(customer_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    result = db.execute(
        text("""
            SELECT
                r.loyalty_score, r.recency, r.frequency, r.monetary,
                s.segment_label, s.churn_probability
            FROM rfm_scores r
            LEFT JOIN segments s ON r.customer_id = s.customer_id
            WHERE r.customer_id = :cid
        """),
        {"cid": customer_id},
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="RFM verisi bulunamadı.")

    return UserProfile(
        user_id=user.user_id,
        customer_id=user.customer_id,
        name=user.name,
        email=user.email,
        avatar_initial=user.avatar_initial,
        loyalty_score=float(result[0]),
        recency=int(result[1]),
        frequency=int(result[2]),
        monetary=float(result[3]),
        segment=result[4] or "Unknown",
        churn_probability=float(result[5]) if result[5] is not None else None,
    )


@router.get("/{customer_id}/coupons", response_model=list[CouponResponse])
def get_coupons(customer_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    coupons = (
        db.query(Coupon)
        .filter(Coupon.customer_id == customer_id)
        .order_by(Coupon.created_at.desc())
        .all()
    )
    return coupons


@router.delete("/coupons/{coupon_id}")
def delete_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.coupon_id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Kupon bulunamadı.")
    db.delete(coupon)
    db.commit()
    return {"success": True, "message": "Kupon silindi.", "coupon_id": coupon_id}


@router.post("/fcm-token")
def update_fcm_token(req: FcmTokenRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.customer_id == req.customer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    user.fcm_token = req.fcm_token
    db.commit()
    return {"success": True, "message": "FCM token güncellendi."}
