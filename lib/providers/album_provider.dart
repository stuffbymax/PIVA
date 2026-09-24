import 'package:flutter/foundation.dart';
import '../models/album.dart';
import '../services/album_service.dart';

class AlbumProvider extends ChangeNotifier {
  final _service = AlbumService();

  List<Album> albums = [];
  bool loading = false;
  String? error;

  Future<void> refresh() async {
    loading = true;
    error = null;
    notifyListeners();
    try {
      albums = await _service.list();
    } catch (e) {
      error = e.toString();
    } finally {
      loading = false;
      notifyListeners();
    }
  }

  Future<Album?> create(String name) async {
    try {
      final album = await _service.create(name);
      albums.insert(0, album);
      notifyListeners();
      return album;
    } catch (_) {
      return null;
    }
  }

  void updateAlbum(Album album) {
    final index = albums.indexWhere((a) => a.id == album.id);
    if (index != -1) {
      albums[index] = album;
    } else {
      albums.insert(0, album);
    }
    notifyListeners();
  }

  Future<void> renameAlbum(int id, String name) async {
    final updated = await _service.rename(id, name);
    updateAlbum(updated);
  }

  Future<void> setCover(int albumId, int mediaId) async {
    final updated = await _service.update(albumId, coverMediaId: mediaId);
    updateAlbum(updated);
  }

  Future<void> delete(int id) async {
    albums.removeWhere((a) => a.id == id);
    notifyListeners();
    try {
      await _service.delete(id);
    } catch (_) {
      await refresh();
    }
  }
}
