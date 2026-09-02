import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../providers/album_provider.dart';
import '../services/media_service.dart';
import 'album_detail_screen.dart';

class AlbumsScreen extends StatefulWidget {
  const AlbumsScreen({super.key});

  @override
  State<AlbumsScreen> createState() => _AlbumsScreenState();
}

class _AlbumsScreenState extends State<AlbumsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AlbumProvider>().refresh();
    });
  }

  Future<void> _createAlbum() async {
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('New album'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Album name'),
          onSubmitted: (v) => Navigator.pop(context, v),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Create'),
          ),
        ],
      ),
    );
    if (name != null && name.trim().isNotEmpty) {
      await context.read<AlbumProvider>().create(name.trim());
    }
  }

  @override
  Widget build(BuildContext context) {
    final mediaService = MediaService();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Albums'),
        actions: [
          IconButton(icon: const Icon(Icons.add), onPressed: _createAlbum),
        ],
      ),
      body: Consumer<AlbumProvider>(
        builder: (context, provider, _) {
          if (provider.loading && provider.albums.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.albums.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.photo_album_outlined, size: 56, color: Colors.grey),
                  const SizedBox(height: 8),
                  const Text('No albums yet'),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _createAlbum,
                    icon: const Icon(Icons.add),
                    label: const Text('Create an album'),
                  ),
                ],
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: provider.refresh,
            child: GridView.builder(
              padding: const EdgeInsets.all(12),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 0.85,
              ),
              itemCount: provider.albums.length,
              itemBuilder: (context, i) {
                final album = provider.albums[i];
                return InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => AlbumDetailScreen(albumId: album.id),
                  )),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Container(
                            color: Colors.grey.shade300,
                            width: double.infinity,
                            child: album.coverMediaId != null
                                ? CachedNetworkImage(
                                    imageUrl: mediaService.thumbnailUrl(album.coverMediaId!),
                                    httpHeaders: mediaService.authHeaders,
                                    fit: BoxFit.cover,
                                  )
                                : const Icon(Icons.photo_album_outlined, size: 40),
                          ),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(album.name ?? 'Untitled',
                          style: const TextStyle(fontWeight: FontWeight.w500),
                          overflow: TextOverflow.ellipsis),
                      Text('${album.itemCount} items',
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
