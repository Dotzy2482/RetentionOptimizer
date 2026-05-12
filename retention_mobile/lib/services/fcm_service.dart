import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/foundation.dart';
import 'api_service.dart';
import 'auth_provider.dart';
import 'coupons_provider.dart';

class FcmService {
  FcmService._();
  static final FcmService instance = FcmService._();

  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotif =
      FlutterLocalNotificationsPlugin();

  String? _currentToken;
  String? get currentToken => _currentToken;

  AuthProvider? _authProvider;
  CouponsProvider? _couponsProvider;

  void setProviders(AuthProvider auth, CouponsProvider coupons) {
    _authProvider = auth;
    _couponsProvider = coupons;
  }

  Future<void> initialize() async {
    final settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    debugPrint('FCM permission: ${settings.authorizationStatus}');

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit);
    await _localNotif.initialize(initSettings);

    const channel = AndroidNotificationChannel(
      'retention_coupons',
      'Kupon Bildirimleri',
      description: 'Yeni kuponlar ve kampanyalar için bildirimler',
      importance: Importance.high,
    );
    await _localNotif
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);

    _currentToken = await _fcm.getToken();
    debugPrint('FCM TOKEN: $_currentToken');

    _fcm.onTokenRefresh.listen((newToken) {
      _currentToken = newToken;
      debugPrint('FCM TOKEN REFRESHED: $newToken');
    });

    FirebaseMessaging.onMessage.listen(_onForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_onNotificationOpened);

    final initialMessage = await _fcm.getInitialMessage();
    if (initialMessage != null) {
      _onNotificationOpened(initialMessage);
    }
  }

  Future<void> registerTokenForUser(int customerId) async {
    if (_currentToken == null) {
      debugPrint('FCM token yok, kayıt atlanıyor');
      return;
    }
    try {
      await ApiService.instance.updateFcmToken(customerId, _currentToken!);
      debugPrint("FCM token backend'e kaydedildi: customer_id=$customerId");
    } catch (e) {
      debugPrint('FCM token kayıt hatası: $e');
    }
  }

  void _onForegroundMessage(RemoteMessage message) {
    debugPrint('Foreground message: ${message.notification?.title}');
    final notif = message.notification;
    if (notif == null) return;

    _localNotif.show(
      DateTime.now().millisecondsSinceEpoch.remainder(100000),
      notif.title,
      notif.body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'retention_coupons',
          'Kupon Bildirimleri',
          channelDescription: 'Yeni kuponlar ve kampanyalar için bildirimler',
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
      ),
    );

    _refreshCoupons();
  }

  void _onNotificationOpened(RemoteMessage message) {
    debugPrint('Notification opened: ${message.notification?.title}');
    _refreshCoupons();
  }

  void _refreshCoupons() {
    final user = _authProvider?.currentUser;
    if (user == null) return;
    _couponsProvider?.loadCoupons(user.customerId);
  }
}
