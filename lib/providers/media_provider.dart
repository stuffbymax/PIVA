import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import '../models/media_item.dart';
import '../services/media_service.dart';

class UploadTask {
  final String label;
  double progress;
  String? error;
  bool done;
  UploadTask(this.label, {this.progress = 0, this.error, this.done = false});
}

/// Drives the main photo grid, the favorites view, and the trash view --
/// they all share this provider but filter with [trashed]/[favoritesOnly]
/// at construction time from the screen that owns them.
class MediaProvider extends ChangeNotifier {
  MediaProvider({this.trashed = false, this.favoritesOnly = false});

  final bool trashed;
  final bool favoritesOnly;
  final _service = MediaService();

  final List<MediaItem> items = [];
  bool loading = false;
  bool loadingMore = false;
  bool hasNext = true;
  int _page = 1;
  String? error;

  final List<UploadTask> uploadTasks = [];
  bool get isUploading => uploadTasks.any((t) => !t.done && t.error == null);

  Future<void> refresh() async {
    loading = true;
    error = null;
    notifyListeners();
    try {
      _page = 1;
      final result = await _service.list(
        page: _page,
        trashed: trashed,
        favoritesOnly: favoritesOnly,
      );
      items
        ..clear()
        ..addAll(result.items);
      hasNext = result.hasNext;
    } catch (e) {
      error = e.toString();
    } finally {
      loading = false;
      notifyListeners();
    }
  }

  Future<void> loadMore() async {
    if (loadingMore || !hasNext) return;
    loadingMore = true;
    notifyListeners();
    try {
      final result = await _service.list(
        page: _page + 1,
        trashed: trashed,
        favoritesOnly: favoritesOnly,
      );
      _page += 1;
      items.addAll(result.items);
      hasNext = result.hasNext;
    } catch (_) {
      // Leave hasNext as-is so the user can retry by scrolling again.
    } finally {
      loadingMore = false;
      notifyListeners();
    }
  }

  /// Uploads a batch of picked files one at a time (sequential keeps
  /// memory/bandwidth predictable on mobile connections), then refreshes
  /// the grid so newly uploaded items appear.
  Future<void> uploadFiles(List<XFile> files) async {
    for (final file in files) {
      final task = UploadTask(file.name);
      uploadTasks.add(task);
      notifyListeners();
      try {
        final media = await _service.upload(
          file,
          takenAt: DateTime.now(),
          onProgress: (f) {
            task.progress = f;
            notifyListeners();
          },
        );
        task.done = true;
        if (!trashed && (!favoritesOnly || media.isFavorite)) {
          items.insert(0, media);
        }
      } catch (e) {
        task.error = e.toString();
        task.done = true;
      }
      notifyListeners();
    }
    // Give the user a moment to see the final state, then clear the list.
    await Future.delayed(const Duration(seconds: 2));
    uploadTasks.removeWhere((t) => t.done && t.error == null);
    notifyListeners();
  }

  Future<void> toggleFavorite(MediaItem item) async {
    final newValue = !item.isFavorite;
    _replace(item.copyWith(isFavorite: newValue));
    try {
      final updated = await _service.setFavorite(item.id, newValue);
      _replace(updated);
      if (favoritesOnly && !updated.isFavorite) {
        items.removeWhere((m) => m.id == item.id);
        notifyListeners();
      }
    } catch (_) {
      _replace(item); // revert on failure
    }
  }

  Future<void> moveToTrash(MediaItem item) async {
    items.removeWhere((m) => m.id == item.id);
    notifyListeners();
    try {
      await _service.trash(item.id);
    } catch (_) {
      items.add(item);
      notifyListeners();
    }
  }

  Future<void> restore(MediaItem item) async {
    items.removeWhere((m) => m.id == item.id);
    notifyListeners();
    try {
      await _service.restore(item.id);
    } catch (_) {
      items.add(item);
      notifyListeners();
    }
  }

  Future<void> deletePermanently(MediaItem item) async {
    items.removeWhere((m) => m.id == item.id);
    notifyListeners();
    try {
      await _service.deletePermanently(item.id);
    } catch (_) {
      items.add(item);
      notifyListeners();
    }
  }

  Future<void> emptyTrash() async {
    items.clear();
    notifyListeners();
    try {
      await _service.emptyTrash();
    } catch (_) {
      await refresh();
    }
  }

  void _replace(MediaItem updated) {
    final idx = items.indexWhere((m) => m.id == updated.id);
    if (idx != -1) items[idx] = updated;
    notifyListeners();
  }
}
