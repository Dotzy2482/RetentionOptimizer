class Coupon {
  final int couponId;
  final int customerId;
  final String code;
  final int discountPercent;
  final String title;
  final String message;
  final bool isUsed;
  final DateTime createdAt;
  final DateTime expiresAt;

  const Coupon({
    required this.couponId,
    required this.customerId,
    required this.code,
    required this.discountPercent,
    required this.title,
    required this.message,
    required this.isUsed,
    required this.createdAt,
    required this.expiresAt,
  });

  bool get isExpired => DateTime.now().isAfter(expiresAt);

  bool get expiresSoon {
    final diff = expiresAt.difference(DateTime.now());
    return !isExpired && diff.inDays <= 3;
  }

  factory Coupon.fromJson(Map<String, dynamic> json) {
    return Coupon(
      couponId: json['coupon_id'] as int,
      customerId: json['customer_id'] as int,
      code: json['code'] as String,
      discountPercent: json['discount_percent'] as int,
      title: json['title'] as String,
      message: json['message'] as String,
      isUsed: json['is_used'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      expiresAt: DateTime.parse(json['expires_at'] as String),
    );
  }
}
