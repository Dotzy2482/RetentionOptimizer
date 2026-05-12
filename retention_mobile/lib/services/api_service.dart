import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/user.dart';
import '../models/coupon.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiService {
  ApiService._();
  static final ApiService instance = ApiService._();

  final _client = http.Client();

  Future<Map<String, dynamic>> _get(String path) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path');
    try {
      final response =
          await _client.get(uri).timeout(ApiConfig.receiveTimeout);
      return _handleResponse(response) as Map<String, dynamic>;
    } on SocketException {
      throw ApiException('Sunucuya bağlanılamadı. Backend çalışıyor mu?');
    } on HttpException {
      throw ApiException('HTTP hatası oluştu.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Beklenmeyen hata: $e');
    }
  }

  Future<Map<String, dynamic>> _post(
      String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path');
    try {
      final response = await _client
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(ApiConfig.receiveTimeout);
      return _handleResponse(response) as Map<String, dynamic>;
    } on SocketException {
      throw ApiException('Sunucuya bağlanılamadı. Backend çalışıyor mu?');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Beklenmeyen hata: $e');
    }
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }

    String errorMessage = 'Hata: ${response.statusCode}';
    try {
      final body = jsonDecode(utf8.decode(response.bodyBytes));
      if (body is Map && body['detail'] != null) {
        errorMessage = body['detail'].toString();
      }
    } catch (_) {}

    throw ApiException(errorMessage, statusCode: response.statusCode);
  }

  Future<User> login(int customerId) async {
    final data = await _post(ApiConfig.login, {'customer_id': customerId});
    return User.fromJson(data);
  }

  Future<User> getProfile(int customerId) async {
    final data = await _get(ApiConfig.userProfile(customerId));
    return User.fromJson(data);
  }

  Future<void> updateFcmToken(int customerId, String token) async {
    await _post('/api/users/fcm-token', {
      'customer_id': customerId,
      'fcm_token': token,
    });
  }

  Future<List<Coupon>> getCoupons(int customerId) async {
    final uri = Uri.parse(
        '${ApiConfig.baseUrl}${ApiConfig.userCoupons(customerId)}');
    try {
      final response =
          await _client.get(uri).timeout(ApiConfig.receiveTimeout);
      if (response.statusCode >= 200 && response.statusCode < 300) {
        final List<dynamic> list =
            jsonDecode(utf8.decode(response.bodyBytes));
        return list.map((j) => Coupon.fromJson(j as Map<String, dynamic>)).toList();
      }
      throw ApiException('Kuponlar yüklenemedi: ${response.statusCode}');
    } on SocketException {
      throw ApiException('Sunucuya bağlanılamadı.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Beklenmeyen hata: $e');
    }
  }

  Future<void> deleteCoupon(int couponId) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/users/coupons/$couponId');
    try {
      final response =
          await _client.delete(uri).timeout(ApiConfig.receiveTimeout);
      if (response.statusCode >= 200 && response.statusCode < 300) return;
      throw ApiException('Kupon silinemedi: ${response.statusCode}');
    } on SocketException {
      throw ApiException('Sunucuya bağlanılamadı.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Beklenmeyen hata: $e');
    }
  }
}