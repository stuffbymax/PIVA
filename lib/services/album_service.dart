import '../models/album.dart';
import 'api_client.dart';

class AlbumService {
  final _api = ApiClient.instance;

  Future<List<Album>> list() async {
    final body = await _api.get('/albums');
    return (body['albums'] as List<dynamic>)
        .map((e) => Album.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Album> create(String name) async {
    final body = await _api.postJson('/albums', {'name': name});
    return Album.fromJson(body['album'] as Map<String, dynamic>);
  }

  Future<Album> get(int id) async {
    final body = await _api.get('/albums/$id');
    return Album.fromJson(body['album'] as Map<String, dynamic>);
  }

  Future<Album> rename(int id, String name) async {
    final body = await _api.patchJson('/albums/$id', {'name': name});
    return Album.fromJson(body['album'] as Map<String, dynamic>);
  }

  Future<void> delete(int id) async {
    await _api.delete('/albums/$id');
  }

  Future<int> addItems(int albumId, List<int> mediaIds) async {
    final body = await _api.postJson('/albums/$albumId/items', {'media_ids': mediaIds});
    return (body['added'] as num?)?.toInt() ?? 0;
  }

  Future<void> removeItem(int albumId, int mediaId) async {
    await _api.delete('/albums/$albumId/items/$mediaId');
  }
}
