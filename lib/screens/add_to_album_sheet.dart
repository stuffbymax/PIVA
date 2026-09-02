import 'package:flutter/material.dart';
import '../models/album.dart';
import '../services/album_service.dart';

Future<void> showAddToAlbumSheet(BuildContext context, int mediaId) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    builder: (context) => _AddToAlbumSheet(mediaId: mediaId),
  );
}

class _AddToAlbumSheet extends StatefulWidget {
  const _AddToAlbumSheet({required this.mediaId});
  final int mediaId;

  @override
  State<_AddToAlbumSheet> createState() => _AddToAlbumSheetState();
}

class _AddToAlbumSheetState extends State<_AddToAlbumSheet> {
  final _service = AlbumService();
  List<Album> _albums = [];
  bool _loading = true;
  final _newAlbumController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _newAlbumController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final albums = await _service.list();
      if (mounted) setState(() {
        _albums = albums;
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _addTo(Album album) async {
    await _service.addItems(album.id, [widget.mediaId]);
    if (mounted) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Added to "${album.name}"')),
      );
    }
  }

  Future<void> _createAndAdd() async {
    final name = _newAlbumController.text.trim();
    if (name.isEmpty) return;
    final album = await _service.create(name);
    await _service.addItems(album.id, [widget.mediaId]);
    if (mounted) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Created "$name" and added photo')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: DraggableScrollableSheet(
          initialChildSize: 0.6,
          expand: false,
          builder: (context, scrollController) {
            return Column(
              children: [
                const Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('Add to album', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _newAlbumController,
                          decoration: const InputDecoration(
                            hintText: 'New album name',
                            border: OutlineInputBorder(),
                            isDense: true,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      FilledButton(onPressed: _createAndAdd, child: const Text('Create')),
                    ],
                  ),
                ),
                const Divider(height: 24),
                Expanded(
                  child: _loading
                      ? const Center(child: CircularProgressIndicator())
                      : _albums.isEmpty
                          ? const Center(child: Text('No albums yet'))
                          : ListView.builder(
                              controller: scrollController,
                              itemCount: _albums.length,
                              itemBuilder: (context, i) {
                                final album = _albums[i];
                                return ListTile(
                                  leading: const Icon(Icons.photo_album_outlined),
                                  title: Text(album.name ?? 'Untitled'),
                                  subtitle: Text('${album.itemCount} items'),
                                  onTap: () => _addTo(album),
                                );
                              },
                            ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
