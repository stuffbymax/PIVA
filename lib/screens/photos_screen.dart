import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import '../models/media_item.dart';
import '../providers/media_provider.dart';
import '../widgets/photo_grid_tile.dart';
import '../widgets/upload_banner.dart';
import 'photo_detail_screen.dart';

/// Reusable grid screen. Used for "All photos", "Favorites", and (with
/// [trashed]=true) the Trash tab -- they're the same UI over a different
/// server-side filter, so one screen covers all three.
class PhotosScreen extends StatefulWidget {
  const PhotosScreen({
    super.key,
    this.trashed = false,
    this.favoritesOnly = false,
    this.title = 'Photos',
  });

  final bool trashed;
  final bool favoritesOnly;
  final String title;

  @override
  State<PhotosScreen> createState() => _PhotosScreenState();
}

class _PhotosScreenState extends State<PhotosScreen> {
  late final MediaProvider _provider;
  final _scrollController = ScrollController();
  final _picker = ImagePicker();
  final Set<int> _selected = {};

  bool get _selectionMode => _selected.isNotEmpty;

  @override
  void initState() {
    super.initState();
    _provider = MediaProvider(trashed: widget.trashed, favoritesOnly: widget.favoritesOnly);
    _provider.refresh();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    _provider.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >
        _scrollController.position.maxScrollExtent - 400) {
      _provider.loadMore();
    }
  }

  Future<void> _pickAndUpload() async {
    final picked = await _picker.pickMultiImage(imageQuality: 95);
    if (picked.isEmpty) return;
    final files = picked.map((x) => File(x.path)).toList();
    await _provider.uploadFiles(files);
  }

  Future<void> _takePhoto() async {
    final photo = await _picker.pickImage(source: ImageSource.camera, imageQuality: 95);
    if (photo == null) return;
    await _provider.uploadFiles([File(photo.path)]);
  }

  void _toggleSelect(MediaItem item) {
    setState(() {
      if (_selected.contains(item.id)) {
        _selected.remove(item.id);
      } else {
        _selected.add(item.id);
      }
    });
  }

  Future<void> _trashSelected() async {
    final toTrash = _provider.items.where((m) => _selected.contains(m.id)).toList();
    setState(() => _selected.clear());
    for (final item in toTrash) {
      await _provider.moveToTrash(item);
    }
  }

  Future<void> _restoreSelected() async {
    final toRestore = _provider.items.where((m) => _selected.contains(m.id)).toList();
    setState(() => _selected.clear());
    for (final item in toRestore) {
      await _provider.restore(item);
    }
  }

  Future<void> _deleteSelectedForever() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete forever?'),
        content: Text('${_selected.length} item(s) will be permanently deleted.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    final toDelete = _provider.items.where((m) => _selected.contains(m.id)).toList();
    setState(() => _selected.clear());
    for (final item in toDelete) {
      await _provider.deletePermanently(item);
    }
  }

  Future<void> _confirmEmptyTrash() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Empty trash?'),
        content: const Text('Everything in Trash will be permanently deleted.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Empty trash'),
          ),
        ],
      ),
    );
    if (confirmed == true) await _provider.emptyTrash();
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _provider,
      child: Consumer<MediaProvider>(
        builder: (context, provider, _) {
          return Scaffold(
            appBar: AppBar(
              title: Text(_selectionMode ? '${_selected.length} selected' : widget.title),
              leading: _selectionMode
                  ? IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => setState(() => _selected.clear()),
                    )
                  : null,
              actions: _selectionMode
                  ? (widget.trashed
                      ? [
                          IconButton(
                              icon: const Icon(Icons.restore),
                              tooltip: 'Restore',
                              onPressed: _restoreSelected),
                          IconButton(
                              icon: const Icon(Icons.delete_forever_outlined),
                              tooltip: 'Delete forever',
                              onPressed: _deleteSelectedForever),
                        ]
                      : [
                          IconButton(
                              icon: const Icon(Icons.delete_outline),
                              tooltip: 'Move to trash',
                              onPressed: _trashSelected),
                        ])
                  : (widget.trashed
                      ? [
                          IconButton(
                            icon: const Icon(Icons.delete_sweep_outlined),
                            tooltip: 'Empty trash',
                            onPressed: provider.items.isEmpty ? null : _confirmEmptyTrash,
                          ),
                        ]
                      : null),
            ),
            body: Column(
              children: [
                UploadBanner(tasks: provider.uploadTasks),
                Expanded(child: _buildBody(provider)),
              ],
            ),
            floatingActionButton: widget.trashed
                ? null
                : FloatingActionButton(
                    onPressed: () => _showUploadOptions(context),
                    child: const Icon(Icons.add_photo_alternate_outlined),
                  ),
          );
        },
      ),
    );
  }

  void _showUploadOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Choose from gallery'),
              onTap: () {
                Navigator.pop(context);
                _pickAndUpload();
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: const Text('Take a photo'),
              onTap: () {
                Navigator.pop(context);
                _takePhoto();
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBody(MediaProvider provider) {
    if (provider.loading && provider.items.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (provider.error != null && provider.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off_outlined, size: 48),
            const SizedBox(height: 8),
            Text('Could not load photos'),
            const SizedBox(height: 4),
            Text(provider.error!, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: provider.refresh, child: const Text('Retry')),
          ],
        ),
      );
    }
    if (provider.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              widget.trashed ? Icons.delete_outline : Icons.photo_outlined,
              size: 56,
              color: Colors.grey,
            ),
            const SizedBox(height: 8),
            Text(
              widget.trashed
                  ? 'Trash is empty'
                  : (widget.favoritesOnly ? 'No favorites yet' : 'No photos yet'),
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: provider.refresh,
      child: GridView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(2),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3,
          crossAxisSpacing: 2,
          mainAxisSpacing: 2,
        ),
        itemCount: provider.items.length + (provider.loadingMore ? 3 : 0),
        itemBuilder: (context, index) {
          if (index >= provider.items.length) {
            return Container(color: Colors.grey.shade200);
          }
          final item = provider.items[index];
          return PhotoGridTile(
            item: item,
            selected: _selected.contains(item.id),
            selectionMode: _selectionMode,
            onTap: () {
              if (_selectionMode) {
                _toggleSelect(item);
              } else {
                Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => ChangeNotifierProvider.value(
                    value: provider,
                    child: PhotoDetailScreen(
                      initialIndex: index,
                      trashedView: widget.trashed,
                    ),
                  ),
                ));
              }
            },
            onLongPress: () => _toggleSelect(item),
          );
        },
      ),
    );
  }
}
