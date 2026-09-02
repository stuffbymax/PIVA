import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:provider/provider.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:intl/intl.dart';
import 'package:video_player/video_player.dart';
import '../models/media_item.dart';
import '../providers/media_provider.dart';
import '../services/media_service.dart';
import 'add_to_album_sheet.dart';

class PhotoDetailScreen extends StatefulWidget {
  const PhotoDetailScreen({
    super.key,
    required this.initialIndex,
    this.trashedView = false,
  });

  final int initialIndex;
  final bool trashedView;

  @override
  State<PhotoDetailScreen> createState() => _PhotoDetailScreenState();
}

class _PhotoDetailScreenState extends State<PhotoDetailScreen> {
  late final PageController _controller;
  late int _index;
  final _mediaService = MediaService();
  bool _chromeVisible = true;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex;
    _controller = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<MediaProvider>();
    if (provider.items.isEmpty) {
      // Everything on this screen got trashed/deleted -- nothing left to show.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) Navigator.of(context).pop();
      });
      return const Scaffold(backgroundColor: Colors.black);
    }
    final safeIndex = _index.clamp(0, provider.items.length - 1).toInt();
    final item = provider.items[safeIndex];

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: _chromeVisible
          ? AppBar(
              backgroundColor: Colors.black54,
              elevation: 0,
              iconTheme: const IconThemeData(color: Colors.white),
              title: Text(
                DateFormat.yMMMd().add_jm().format(item.displayDate),
                style: const TextStyle(color: Colors.white, fontSize: 15),
              ),
              actions: [
                if (!widget.trashedView)
                  IconButton(
                    icon: Icon(
                      item.isFavorite ? Icons.favorite : Icons.favorite_border,
                      color: item.isFavorite ? Colors.redAccent : Colors.white,
                    ),
                    onPressed: () => provider.toggleFavorite(item),
                  ),
              ],
            )
          : null,
      body: GestureDetector(
        onTap: () => setState(() => _chromeVisible = !_chromeVisible),
        child: PageView.builder(
          controller: _controller,
          itemCount: provider.items.length,
          onPageChanged: (i) => setState(() => _index = i),
          itemBuilder: (context, i) {
            final m = provider.items[i];
            return InteractiveViewer(
              minScale: 1,
              maxScale: 4,
              child: Center(
                child: m.mediaType == 'video' && m.downloadUrl != null
                    ? _AuthenticatedVideoPlayer(
                        url: m.downloadUrl!,
                        headers: _mediaService.authHeaders,
                      )
                    : m.downloadUrl != null
                    ? (kIsWeb
                        ? Image.network(
                            m.downloadUrl!,
                            headers: _mediaService.authHeaders,
                            fit: BoxFit.contain,
                            errorBuilder: (context, error, stackTrace) => const Icon(
                              Icons.broken_image_outlined,
                              color: Colors.white54,
                              size: 48,
                            ),
                          )
                        : CachedNetworkImage(
                            imageUrl: m.downloadUrl!,
                            httpHeaders: _mediaService.authHeaders,
                            fit: BoxFit.contain,
                            placeholder: (context, url) => m.thumbnailUrl != null
                                ? CachedNetworkImage(
                                    imageUrl: m.thumbnailUrl!,
                                    httpHeaders: _mediaService.authHeaders,
                                    fit: BoxFit.contain,
                                  )
                                : const CircularProgressIndicator(),
                            errorWidget: (context, url, error) => const Icon(
                              Icons.broken_image_outlined,
                              color: Colors.white54,
                              size: 48,
                            ),
                          ))
                    : const Icon(Icons.videocam_outlined, color: Colors.white54, size: 64),
              ),
            );
          },
        ),
      ),
      bottomNavigationBar: _chromeVisible ? _buildBottomBar(provider, item) : null,
    );
  }

  Widget _buildBottomBar(MediaProvider provider, MediaItem item) {
    return BottomAppBar(
      color: Colors.black54,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: widget.trashedView
            ? [
                IconButton(
                  icon: const Icon(Icons.restore, color: Colors.white),
                  tooltip: 'Restore',
                  onPressed: () => provider.restore(item),
                ),
                IconButton(
                  icon: const Icon(Icons.delete_forever_outlined, color: Colors.white),
                  tooltip: 'Delete forever',
                  onPressed: () => _confirmPermanentDelete(provider, item),
                ),
              ]
            : [
                IconButton(
                  icon: const Icon(Icons.add_to_photos_outlined, color: Colors.white),
                  tooltip: 'Add to album',
                  onPressed: () => showAddToAlbumSheet(context, item.id),
                ),
                IconButton(
                  icon: const Icon(Icons.delete_outline, color: Colors.white),
                  tooltip: 'Move to trash',
                  onPressed: () => provider.moveToTrash(item),
                ),
              ],
      ),
    );
  }

  Future<void> _confirmPermanentDelete(MediaProvider provider, MediaItem item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete forever?'),
        content: const Text('This cannot be undone.'),
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
    if (confirmed == true) await provider.deletePermanently(item);
  }
}

class _AuthenticatedVideoPlayer extends StatefulWidget {
  const _AuthenticatedVideoPlayer({required this.url, required this.headers});

  final String url;
  final Map<String, String> headers;

  @override
  State<_AuthenticatedVideoPlayer> createState() => _AuthenticatedVideoPlayerState();
}

class _AuthenticatedVideoPlayerState extends State<_AuthenticatedVideoPlayer> {
  late final VideoPlayerController _controller;

  @override
  void initState() {
    super.initState();
    _controller = VideoPlayerController.networkUrl(
      Uri.parse(widget.url),
      httpHeaders: widget.headers,
    )..initialize().then((_) {
        if (mounted) setState(() {});
      });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_controller.value.isInitialized) {
      if (_controller.value.hasError) {
        return const Icon(Icons.broken_image_outlined, color: Colors.white54, size: 48);
      }
      return const CircularProgressIndicator();
    }
    return GestureDetector(
      onTap: () {
        setState(() {
          _controller.value.isPlaying ? _controller.pause() : _controller.play();
        });
      },
      child: AspectRatio(
        aspectRatio: _controller.value.aspectRatio,
        child: VideoPlayer(_controller),
      ),
    );
  }
}
