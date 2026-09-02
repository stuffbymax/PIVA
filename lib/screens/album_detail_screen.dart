import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/album.dart';
import '../services/album_service.dart';
import '../services/media_service.dart';

class AlbumDetailScreen extends StatefulWidget {
  const AlbumDetailScreen({super.key, required this.albumId});
  final int albumId;

  @override
  State<AlbumDetailScreen> createState() => _AlbumDetailScreenState();
}

class _AlbumDetailScreenState extends State<AlbumDetailScreen> {
  final _service = AlbumService();
  final _mediaService = MediaService();
  Album? _album;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final album = await _service.get(widget.albumId);
      if (mounted) setState(() => _album = album);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _removeItem(int mediaId) async {
    await _service.removeItem(widget.albumId, mediaId);
    _load();
  }

  Future<void> _deleteAlbum() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete album?'),
        content: const Text('The photos inside it will not be deleted.'),
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
    if (confirmed == true) {
      await _service.delete(widget.albumId);
      if (mounted) Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_album?.name ?? 'Album'),
        actions: [
          IconButton(icon: const Icon(Icons.delete_outline), onPressed: _deleteAlbum),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text('Could not load album: $_error'))
              : (_album?.items.isEmpty ?? true)
                  ? const Center(child: Text('No photos in this album yet'))
                  : GridView.builder(
                      padding: const EdgeInsets.all(2),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 3,
                        crossAxisSpacing: 2,
                        mainAxisSpacing: 2,
                      ),
                      itemCount: _album!.items.length,
                      itemBuilder: (context, i) {
                        final item = _album!.items[i];
                        return GestureDetector(
                          onLongPress: () => _confirmRemove(item.id),
                          child: item.thumbnailUrl != null
                              ? CachedNetworkImage(
                                  imageUrl: item.thumbnailUrl!,
                                  httpHeaders: _mediaService.authHeaders,
                                  fit: BoxFit.cover,
                                )
                              : Container(color: Colors.grey.shade300),
                        );
                      },
                    ),
    );
  }

  void _confirmRemove(int mediaId) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remove from album?'),
        content: const Text('The photo stays in your library.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              _removeItem(mediaId);
            },
            child: const Text('Remove'),
          ),
        ],
      ),
    );
  }
}
