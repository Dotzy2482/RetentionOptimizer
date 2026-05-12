import 'package:flutter/material.dart';

enum CustomerSegment {
  lowEngagement,
  atRisk,
  active,
  highValueLoyal,
}

extension CustomerSegmentLabel on CustomerSegment {
  String get label {
    switch (this) {
      case CustomerSegment.lowEngagement:
        return 'Yeni Müşteri';
      case CustomerSegment.atRisk:
        return 'Risk Altında';
      case CustomerSegment.active:
        return 'Aktif Müşteri';
      case CustomerSegment.highValueLoyal:
        return 'Sadık Müşteri';
    }
  }

  Color get color {
    switch (this) {
      case CustomerSegment.lowEngagement:
        return const Color(0xFF9CA3AF);
      case CustomerSegment.atRisk:
        return const Color(0xFFDC2626);
      case CustomerSegment.active:
        return const Color(0xFF1D4ED8);
      case CustomerSegment.highValueLoyal:
        return const Color(0xFF7C3AED);
    }
  }

  static CustomerSegment fromString(String s) {
    switch (s) {
      case 'High Value Loyal':
        return CustomerSegment.highValueLoyal;
      case 'Active Customer':
        return CustomerSegment.active;
      case 'At Risk':
        return CustomerSegment.atRisk;
      case 'Low Engagement':
        return CustomerSegment.lowEngagement;
      default:
        return CustomerSegment.active;
    }
  }
}

class User {
  final int customerId;
  final String name;
  final String email;
  final double loyaltyScore;
  final CustomerSegment segment;
  final String avatarInitial;
  final String? fcmToken;
  final int recency;
  final int frequency;
  final double monetary;
  final double? churnProbability;

  const User({
    required this.customerId,
    required this.name,
    required this.email,
    required this.loyaltyScore,
    required this.segment,
    required this.avatarInitial,
    this.fcmToken,
    this.recency = 0,
    this.frequency = 0,
    this.monetary = 0.0,
    this.churnProbability,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      customerId: json['customer_id'] as int,
      name: json['name'] as String,
      email: json['email'] as String,
      loyaltyScore: (json['loyalty_score'] as num).toDouble(),
      segment: CustomerSegmentLabel.fromString(json['segment'] as String),
      avatarInitial: json['avatar_initial'] as String,
      recency: (json['recency'] as int?) ?? 0,
      frequency: (json['frequency'] as int?) ?? 0,
      monetary: (json['monetary'] as num?)?.toDouble() ?? 0.0,
      churnProbability: (json['churn_probability'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'customer_id': customerId,
        'name': name,
        'email': email,
        'loyalty_score': loyaltyScore,
        'segment': segment.name,
        'avatar_initial': avatarInitial,
        'recency': recency,
        'frequency': frequency,
        'monetary': monetary,
        'churn_probability': churnProbability,
      };
}
