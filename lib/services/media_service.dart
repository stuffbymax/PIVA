import 'package:image_picker/image_picker.dart';
import '../models/media_item.dart';
import 'api_client.dart';

class MediaPage {
  final List<MediaItem> items;
  final bool hasNext;
  final int total;
  MediaPage({required this.items, required this.hasNext, required this.total});
}

class MediaService {
  final _api = ApiClient.instance;

  Future<MediaPage> list({
    int page = 1,
    int perPage = 60,
    bool trashed = false,
    bool favoritesOnly = false,
  }) async {
    final body = await _api.get('/media', query: {
      'page': page,
      'per_page': perPage,
      'trashed': trashed,
      'favorites': favoritesOnly,
    });
    final items = (body['items'] as List<dynamic>)
        .map((e) => MediaItem.fromJson(e as Map<String, dynamic>))
        .toList();
    return MediaPage(
      items: items,
      hasNext: body['has_next'] as bool? ?? false,
      total: (body['total'] as num?)?.toInt() ?? items.length,
    );
  }

  /// Batch-checks which checksums the server already has, so the caller
  /// can skip re-uploading files that are already backed up.
  Future<Set<String>> checkExisting(List<String> checksums) async {
    final body = await _api.postJson('/media/check', {'checksums': checksums});
    final existing = body['existing'] as Map<String, dynamic>;
    return existing.keys.toSet();
  }

  Future<MediaItem> upload(
    XFile file, {
    DateTime? takenAt,
    void Function(double fraction)? onProgress,
  }) async {
    final body = await _api.uploadFile(
      '/media/upload',
      file,
      takenAtEpoch: takenAt == null ? null : takenAt.millisecondsSinceEpoch / 1000,
      onProgress: onProgress,
    );
    return MediaItem.fromJson(body['media'] as Map<String, dynamic>);
  }

  Future<MediaItem> setFavorite(int id, bool favorite) async {
    final body = await _api.postJson('/media/$id/favorite', {'favorite': favorite});
    return MediaItem.fromJson(body['media'] as Map<String, dynamic>);
  }

  Future<MediaItem> trash(int id) async {
    final body = await _api.delete('/media/$id');
    return MediaItem.fromJson(body['media'] as Map<String, dynamic>);
  }

  Future<MediaItem> restore(int id) async {
    final body = await _api.post('/media/$id/restore');
    return MediaItem.fromJson(body['media'] as Map<String, dynamic>);
  }

  Future<void> deletePermanently(int id) async {
    await _api.delete('/media/$id/permanent');
  }

  Future<int> emptyTrash() async {
    final body = await _api.post('/media/trash/empty');
    return (body['deleted_count'] as num?)?.toInt() ?? 0;
  }

  String fileUrl(int id) => '${_api.baseUrl}/media/$id/file';
  String thumbnailUrl(int id) => '${_api.baseUrl}/media/$id/thumbnail';
  Map<String, String> get authHeaders => _api.authHeaders;
}
