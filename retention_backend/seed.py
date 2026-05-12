"""
Seed Script — Demo verileri yazar.
Kullanım: venv\\Scripts\\python.exe seed.py
İdempotent: birden fazla çalıştırılabilir, çakışma olmaz.
"""

from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import User, Coupon

DEMO_USERS = [
    {"customer_id": 12380, "name": "Selin Aydın",  "email": "selin@demo.com",  "avatar_initial": "S"},
    {"customer_id": 12348, "name": "Ayşe Yılmaz",  "email": "ayse@demo.com",   "avatar_initial": "A"},
    {"customer_id": 12372, "name": "Can Öztürk",   "email": "can@demo.com",    "avatar_initial": "C"},
    {"customer_id": 12385, "name": "Mehmet Demir", "email": "mehmet@demo.com", "avatar_initial": "M"},
    {"customer_id": 12353, "name": "Zeynep Kaya",  "email": "zeynep@demo.com", "avatar_initial": "Z"},
]

DEMO_COUPONS = {
    # Selin — High Value Loyal — VIP teşekkür kuponları
    12380: [
        {
            "code": "VIP-WELCOME25",
            "title": "VIP Üyemize Özel",
            "message": "Sadakatinin karşılığı: tüm ürünlerde %25 indirim!",
            "discount_percent": 25,
            "is_used": False,
            "days_until_expire": 30,
        },
        {
            "code": "VIP-GIFT15",
            "title": "Bu Hafta Hediyemiz",
            "message": "Her hafta seninleyiz. Bu hafta %15 indirim hediyemiz.",
            "discount_percent": 15,
            "is_used": True,
            "days_until_expire": -3,
        },
        {
            "code": "VIP-SPECIAL30",
            "title": "Sadık Müşteri Ayrıcalığı",
            "message": "Yeni sezon ürünlerinde %30 indirim, sana özel!",
            "discount_percent": 30,
            "is_used": False,
            "days_until_expire": 14,
        },
    ],
    # Ayşe — Active Customer — Teşvik kuponları
    12348: [
        {
            "code": "PROMO-LEVEL10",
            "title": "Bir Sonraki Seviyeye Geç",
            "message": "Alışverişine devam et, VIP olmana çok az kaldı!",
            "discount_percent": 10,
            "is_used": False,
            "days_until_expire": 14,
        },
        {
            "code": "PROMO-WEEKEND15",
            "title": "Hafta Sonu Fırsatı",
            "message": "Sadece bu hafta sonu, %15 indirim!",
            "discount_percent": 15,
            "is_used": False,
            "days_until_expire": 5,
        },
    ],
    # Can — Active Customer — Yükselen müşteri kuponu
    12372: [
        {
            "code": "PROMO-RISE20",
            "title": "Yükselişin Devamı",
            "message": "Bir adım daha, VIP üye olabilirsin! %20 indirim seni bekliyor.",
            "discount_percent": 20,
            "is_used": False,
            "days_until_expire": 10,
        },
    ],
    # Mehmet — At Risk — Geri kazanma kuponu
    12385: [
        {
            "code": "WINBACK-30",
            "title": "Seni Özledik!",
            "message": "Geri dönmen için sana özel %30 indirim. Sadece 3 gün geçerli!",
            "discount_percent": 30,
            "is_used": False,
            "days_until_expire": 3,
        },
    ],
    # Zeynep — Low Engagement — İlk alışveriş teşviki
    12353: [
        {
            "code": "WELCOME-15",
            "title": "Hoş Geldin Hediyemiz",
            "message": "İlk alışverişine özel %15 indirim. Seni aramızda görmek güzel!",
            "discount_percent": 15,
            "is_used": False,
            "days_until_expire": 30,
        },
    ],
}


def seed_users(session):
    added = updated = 0
    for udata in DEMO_USERS:
        existing = session.query(User).filter(User.customer_id == udata["customer_id"]).first()
        if existing:
            existing.name = udata["name"]
            existing.email = udata["email"]
            existing.avatar_initial = udata["avatar_initial"]
            updated += 1
        else:
            session.add(User(**udata))
            added += 1
    session.commit()
    return added, updated


def seed_coupons(session):
    added = skipped = 0
    now = datetime.utcnow()
    for customer_id, coupons in DEMO_COUPONS.items():
        for cdata in coupons:
            if session.query(Coupon).filter(Coupon.code == cdata["code"]).first():
                skipped += 1
                continue
            session.add(Coupon(
                customer_id=customer_id,
                code=cdata["code"],
                title=cdata["title"],
                message=cdata["message"],
                discount_percent=cdata["discount_percent"],
                is_used=cdata["is_used"],
                expires_at=now + timedelta(days=cdata["days_until_expire"]),
            ))
            added += 1
    session.commit()
    return added, skipped


def main():
    print("=" * 60)
    print("  Retention Backend — Seed Script")
    print("=" * 60)

    Base.metadata.create_all(engine)
    print("[OK] Tablolar hazir.")

    session = SessionLocal()
    try:
        added_u, updated_u = seed_users(session)
        print(f"[OK] User'lar: {added_u} eklendi, {updated_u} guncellendi.")

        added_c, skipped_c = seed_coupons(session)
        print(f"[OK] Kuponlar: {added_c} eklendi, {skipped_c} atlandi (zaten vardi).")

        total_users = session.query(User).count()
        total_coupons = session.query(Coupon).count()
        print()
        print(f"  Toplam user:  {total_users}")
        print(f"  Toplam kupon: {total_coupons}")
        print()
        print("  Demo customer_id'ler: 12380, 12348, 12372, 12385, 12353")
        print()
        print('  Test komutu:')
        print('    curl -X POST http://localhost:8000/api/login -H "Content-Type: application/json" -d "{\\"customer_id\\": 12380}"')
        print()
        print("[OK] Seed tamamlandi!")
    except Exception as e:
        session.rollback()
        print(f"[HATA] {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
