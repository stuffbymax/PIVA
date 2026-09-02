import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';

enum AuthStatus { unknown, needsServer, needsLogin, authenticated }

class AuthProvider extends ChangeNotifier {
  final _authService = AuthService();
  final _api = ApiClient.instance;

  AuthStatus status = AuthStatus.unknown;
  AppUser? user;
  String? lastError;

  /// Call once at app startup. Restores any saved server URL / tokens
  /// and verifies the token is still valid before dropping the user
  /// straight into the app.
  Future<void> bootstrap() async {
    await _api.loadFromStorage();
    if (!_api.isConfigured) {
      status = AuthStatus.needsServer;
      notifyListeners();
      return;
    }
    if (!_api.isLoggedIn) {
      status = AuthStatus.needsLogin;
      notifyListeners();
      return;
    }
    try {
      user = await _authService.me();
      status = AuthStatus.authenticated;
    } catch (_) {
      status = AuthStatus.needsLogin;
    }
    notifyListeners();
  }

  Future<void> setServerUrl(String url) async {
    await _api.setServerUrl(url);
    status = _api.isLoggedIn ? AuthStatus.authenticated : AuthStatus.needsLogin;
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    lastError = null;
    try {
      user = await _authService.login(username, password);
      status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      lastError = _friendlyError(e);
      notifyListeners();
      return false;
    }
  }

  Future<bool> register(String username, String password, {String? email}) async {
    lastError = null;
    try {
      user = await _authService.register(username, password, email: email);
      status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      lastError = _friendlyError(e);
      notifyListeners();
      return false;
    }
  }

  Future<void> refreshUser() async {
    try {
      user = await _authService.me();
      notifyListeners();
    } catch (_) {
      // Non-fatal: storage widgets just show stale numbers until next call.
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    user = null;
    status = AuthStatus.needsLogin;
    notifyListeners();
  }

  String _friendlyError(Object e) {
    final msg = e.toString();
    return msg.replaceFirst('ApiException(', '').replaceFirst(RegExp(r'^\d+\): '), '');
  }
}
