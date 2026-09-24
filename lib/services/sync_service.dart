import 'package:shared_preferences/shared_preferences.dart';

import '../models/media_item.dart';
import '../models/album.dart';
import 'api_client.dart';

class SyncDelta {
  final double serverTime;
  final List<MediaItem> media;
  final List<Album> albums;
  final bool more;

  const SyncDelta({
    required this.serverTime,
    required this.media,
    required this.albums,
    required this.more,
  });
}

class SyncService {
  static const _lastServerTimeKey = 'last_server_time';
  final _api = ApiClient.instance;

  Future<double> lastServerTime() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getDouble(_lastServerTimeKey) ?? 0.0;
  }

  Future<void> saveServerTime(double serverTime) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_lastServerTimeKey, serverTime);
  }

  Future<SyncDelta> fetchDelta({double since = 0.0}) async {
    final body = await _api.get('/sync', query: {'since': since});
    final media = ((body['media'] as List<dynamic>? ?? [])
            .map((e) => MediaItem.fromJson(e as Map<String, dynamic>))
            .toList())
        .where((item) => !item.deleted)
        .toList();
    final albums = ((body['albums'] as List<dynamic>? ?? [])
            .map((e) => Album.fromJson(e as Map<String, dynamic>))
            .toList())
        .where((album) => !album.deleted)
        .toList();
    return SyncDelta(
      serverTime: (body['server_time'] as num?)?.toDouble() ?? since,
      media: media,
      albums: albums,
      more: body['more'] as bool? ?? false,
    );
  }

  void _applySyncDelta(List<MediaItem> items, List<Album> albums) {
    // This is intentionally left as a no-op here and handled by the provider.
    // Keeping this minimal keeps the feature testable without reworking the rest.
  }
}
