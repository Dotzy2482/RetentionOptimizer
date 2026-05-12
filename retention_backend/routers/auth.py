from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import User
from schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.customer_id == req.customer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı. Demo hesaplardan birini seç.")

    result = db.execute(
        text("""
            SELECT r.loyalty_score, s.segment_label
            FROM rfm_scores r
            LEFT JOIN segments s ON r.customer_id = s.customer_id
            WHERE r.customer_id = :cid
        """),
        {"cid": req.customer_id},
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Bu müşteri için RFM verisi bulunamadı.")

    return LoginResponse(
        user_id=user.user_id,
        customer_id=user.customer_id,
        name=user.name,
        email=user.email,
        avatar_initial=user.avatar_initial,
        loyalty_score=float(result[0]),
        segment=result[1] or "Unknown",
    )
