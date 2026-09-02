import '../models/user.dart';
import 'api_client.dart';

class AuthService {
  final _api = ApiClient.instance;

  Future<AppUser> register(String username, String password, {String? email}) async {
    final body = await _api.postJson('/auth/register', {
      'username': username,
      'password': password,
      if (email != null && email.isNotEmpty) 'email': email,
    });
    await _api.setTokens(
      access: body['access_token'] as String,
      refresh: body['refresh_token'] as String,
    );
    return AppUser.fromJson(body['user'] as Map<String, dynamic>);
  }

  Future<AppUser> login(String username, String password) async {
    final body = await _api.postJson('/auth/login', {
      'username': username,
      'password': password,
    });
    await _api.setTokens(
      access: body['access_token'] as String,
      refresh: body['refresh_token'] as String,
    );
    return AppUser.fromJson(body['user'] as Map<String, dynamic>);
  }

  Future<AppUser> me() async {
    final body = await _api.get('/auth/me');
    return AppUser.fromJson(body['user'] as Map<String, dynamic>);
  }

  Future<void> logout() async {
    await _api.clearSession();
  }
}
