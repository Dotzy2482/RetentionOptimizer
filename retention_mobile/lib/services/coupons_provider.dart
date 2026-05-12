import 'package:flutter/foundation.dart';
import '../models/coupon.dart';
import 'api_service.dart';

class CouponsProvider extends ChangeNotifier {
  List<Coupon> _coupons = [];
  bool _isLoading = false;
  String? _error;
  int? _currentCustomerId;

  List<Coupon> get coupons => _coupons;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadCoupons(int customerId) async {
    _currentCustomerId = customerId;
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _coupons = await ApiService.instance.getCoupons(customerId);
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clear() {
    _coupons = [];
    _isLoading = false;
    _error = null;
    _currentCustomerId = null;
    notifyListeners();
  }

  Future<void> deleteCoupon(int couponId) async {
    _coupons.removeWhere((c) => c.couponId == couponId);
    notifyListeners();
    try {
      await ApiService.instance.deleteCoupon(couponId);
    } catch (e) {
      if (_currentCustomerId != null) {
        await loadCoupons(_currentCustomerId!);
      }
      rethrow;
    }
  }
}
