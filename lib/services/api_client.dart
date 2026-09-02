import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Thrown for any non-2xx response. [statusCode] lets callers branch on
/// e.g. 409 (username taken) vs 413 (quota exceeded) without string
/// matching the message.
class ApiException implements Exception {
  final String message;
  final int statusCode;
  ApiException(this.message, this.statusCode);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// Thin wrapper around [http] that:
///  - stores the server URL + JWT access/refresh tokens in secure storage
///  - attaches `Authorization: Bearer <token>` to every request
///  - on a 401, silently refreshes the access token once and retries
///    the original request, so the rest of the app never has to think
///    about token expiry.
class ApiClient {
  ApiClient._internal();
  static final ApiClient instance = ApiClient._internal();

  final _storage = const FlutterSecureStorage();
  static const _kServerUrl = 'server_url';
  static const _kAccessToken = 'access_token';
  static const _kRefreshToken = 'refresh_token';

  String? _baseUrl;
  String? _accessToken;
  String? _refreshToken;

  bool get isConfigured => _baseUrl != null && _baseUrl!.isNotEmpty;
  bool get isLoggedIn => _accessToken != null;
  String? get baseUrl => _baseUrl;

  /// Call once at app startup to restore any saved session.
  Future<void> loadFromStorage() async {
    _baseUrl = await _storage.read(key: _kServerUrl);
    _accessToken = await _storage.read(key: _kAccessToken);
    _refreshToken = await _storage.read(key: _kRefreshToken);
  }

  Future<void> setServerUrl(String url) async {
    // Trim any trailing slash so path-joining below is never ambiguous.
    _baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
    await _storage.write(key: _kServerUrl, value: _baseUrl);
  }

  Future<void> setTokens({required String access, required String refresh}) async {
    _accessToken = access;
    _refreshToken = refresh;
    await _storage.write(key: _kAccessToken, value: access);
    await _storage.write(key: _kRefreshToken, value: refresh);
  }

  Future<void> clearSession() async {
    _accessToken = null;
    _refreshToken = null;
    await _storage.delete(key: _kAccessToken);
    await _storage.delete(key: _kRefreshToken);
  }

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    if (_baseUrl == null) {
      throw ApiException('Server URL is not configured.', 0);
    }
    final q = query?.map((k, v) => MapEntry(k, '$v'));
    return Uri.parse('$_baseUrl$path').replace(queryParameters: q);
  }

  Map<String, String> _headers({bool json = true, bool useRefresh = false}) {
    final headers = <String, String>{};
    if (json) headers['Content-Type'] = 'application/json';
    final token = useRefresh ? _refreshToken : _accessToken;
    if (token != null) headers['Authorization'] = 'Bearer $token';
    return headers;
  }

  /// Tries the given request once; if it comes back 401 and we have a
  /// refresh token, refreshes the access token and retries exactly once.
  Future<http.Response> _withAutoRefresh(
      Future<http.Response> Function() attempt) async {
    var response = await attempt();
    if (response.statusCode == 401 && _refreshToken != null) {
      final refreshed = await _tryRefresh();
      if (refreshed) {
        response = await attempt();
      }
    }
    return response;
  }

  Future<bool> _tryRefresh() async {
    try {
      final response = await http.post(
        _uri('/auth/refresh'),
        headers: _headers(json: false, useRefresh: true),
      );
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        _accessToken = body['access_token'] as String;
        await _storage.write(key: _kAccessToken, value: _accessToken);
        return true;
      }
    } catch (_) {
      // Network error during refresh -- fall through to returning false,
      // caller will surface the original 401 as a normal ApiException.
    }
    return false;
  }

  dynamic _decodeOrThrow(http.Response response) {
    final isJson =
        response.headers['content-type']?.contains('application/json') ?? false;
    final decoded = isJson && response.bodyBytes.isNotEmpty
        ? jsonDecode(utf8.decode(response.bodyBytes))
        : null;

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }

    String message = 'Request failed (${response.statusCode}).';
    if (decoded is Map && decoded['error'] != null) {
      message = decoded['error'].toString();
    }
    throw ApiException(message, response.statusCode);
  }

  // ---------------------------------------------------------------- GET --
  Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    final response = await _withAutoRefresh(
      () => http.get(_uri(path, query), headers: _headers(json: false)),
    );
    return _decodeOrThrow(response);
  }

  // --------------------------------------------------------------- POST --
  Future<dynamic> postJson(String path, Map<String, dynamic> body) async {
    final response = await _withAutoRefresh(
      () => http.post(_uri(path), headers: _headers(), body: jsonEncode(body)),
    );
    return _decodeOrThrow(response);
  }

  Future<dynamic> patchJson(String path, Map<String, dynamic> body) async {
    final response = await _withAutoRefresh(
      () => http.patch(_uri(path), headers: _headers(), body: jsonEncode(body)),
    );
    return _decodeOrThrow(response);
  }

  Future<dynamic> post(String path) async {
    final response = await _withAutoRefresh(
      () => http.post(_uri(path), headers: _headers(json: false)),
    );
    return _decodeOrThrow(response);
  }

  Future<dynamic> delete(String path) async {
    final response = await _withAutoRefresh(
      () => http.delete(_uri(path), headers: _headers(json: false)),
    );
    return _decodeOrThrow(response);
  }

  // -------------------------------------------------------- file upload --
  /// Uploads a single file as multipart/form-data. [onProgress] receives
  /// a 0.0-1.0 fraction; note plain [http] can't report *streaming*
  /// upload progress, so this reports 0.0 while sending and 1.0 once the
  /// server has responded -- fine for a per-file progress list, not a
  /// smooth progress bar for one huge video. See README for swapping in
  /// `dio` if you need byte-level progress.
  Future<Map<String, dynamic>> uploadFile(
    String path,
    File file, {
    double? takenAtEpoch,
    void Function(double fraction)? onProgress,
  }) async {
    Future<http.StreamedResponse> attempt() async {
      final request = http.MultipartRequest('POST', _uri(path));
      request.headers.addAll(_headers(json: false));
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
      if (takenAtEpoch != null) {
        request.fields['taken_at'] = takenAtEpoch.toString();
      }
      onProgress?.call(0.0);
      final streamed = await request.send();
      onProgress?.call(1.0);
      return streamed;
    }

    var streamed = await attempt();
    if (streamed.statusCode == 401 && _refreshToken != null) {
      final refreshed = await _tryRefresh();
      if (refreshed) streamed = await attempt();
    }
    final response = await http.Response.fromStream(streamed);
    return _decodeOrThrow(response) as Map<String, dynamic>;
  }

  /// Returns headers to use with e.g. [CachedNetworkImage] so authenticated
  /// thumbnail/file URLs load correctly.
  Map<String, String> get authHeaders => _headers(json: false);
}
