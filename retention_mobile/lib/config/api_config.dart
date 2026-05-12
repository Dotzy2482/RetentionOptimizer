class ApiConfig {
  // Android emülatör için: 10.0.2.2 = host bilgisayarın localhost'u
  // Gerçek cihazda Wi-Fi'da: bilgisayar IP'si (192.168.x.x:8000)
  // iOS simulator için: localhost veya 127.0.0.1
  static const String baseUrl = 'http://10.0.2.2:8000';

  static const String login = '/api/login';
  static String userProfile(int customerId) => '/api/users/$customerId/profile';
  static String userCoupons(int customerId) => '/api/users/$customerId/coupons';
  static const String fcmToken = '/api/users/fcm-token';

  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 15);
}
