import '../models/user.dart';

class MockData {
  MockData._();

  static final List<User> demoUsers = [
    const User(
      customerId: 12380,
      name: 'Selin Aydın',
      email: 'selin@demo.com',
      loyaltyScore: 93.75,
      segment: CustomerSegment.highValueLoyal,
      avatarInitial: 'S',
    ),
    const User(
      customerId: 12348,
      name: 'Ayşe Yılmaz',
      email: 'ayse@demo.com',
      loyaltyScore: 64.0,
      segment: CustomerSegment.active,
      avatarInitial: 'A',
    ),
    const User(
      customerId: 12372,
      name: 'Can Öztürk',
      email: 'can@demo.com',
      loyaltyScore: 71.0,
      segment: CustomerSegment.active,
      avatarInitial: 'C',
    ),
    const User(
      customerId: 12385,
      name: 'Mehmet Demir',
      email: 'mehmet@demo.com',
      loyaltyScore: 36.2,
      segment: CustomerSegment.atRisk,
      avatarInitial: 'M',
    ),
    const User(
      customerId: 12353,
      name: 'Zeynep Kaya',
      email: 'zeynep@demo.com',
      loyaltyScore: 18.0,
      segment: CustomerSegment.lowEngagement,
      avatarInitial: 'Z',
    ),
  ];
}
