import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import 'api_service.dart';
import 'fcm_service.dart';

const _kSavedCustomerId = 'saved_customer_id';

class AuthProvider extends ChangeNotifier {
  User? _currentUser;
  bool _isLoading = false;
  bool _isInitializing = true;
  String? _error;

  User? get currentUser => _currentUser;
  bool get isLoggedIn => _currentUser != null;
  bool get isLoading => _isLoading;
  bool get isInitializing => _isInitializing;
  String? get error => _error;

  AuthProvider() {
    _initialize();
  }

  Future<void> _initialize() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedId = prefs.getInt(_kSavedCustomerId);
      if (savedId != null) {
        try {
          final user = await ApiService.instance
              .login(savedId)
              .timeout(const Duration(seconds: 5));
          _currentUser = user;
          FcmService.instance.registerTokenForUser(savedId).catchError((_) {});
        } catch (_) {
          final prefs2 = await SharedPreferences.getInstance();
          await prefs2.remove(_kSavedCustomerId);
          _currentUser = null;
        }
      }
    } catch (e) {
      debugPrint('AuthProvider init error: $e');
    } finally {
      _isInitializing = false;
      notifyListeners();
    }
  }

  Future<void> loginWithCustomerId(int customerId) async {
    _isLoading = true;
    notifyListeners();
    try {
      final user = await ApiService.instance.login(customerId);
      _currentUser = user;
      _error = null;
      FcmService.instance.registerTokenForUser(customerId).catchError((_) {});
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_kSavedCustomerId, customerId);
    } on ApiException catch (e) {
      _error = e.message;
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    _currentUser = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kSavedCustomerId);
    notifyListeners();
  }
}
