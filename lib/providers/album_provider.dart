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
