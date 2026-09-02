import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/media_item.dart';
import '../services/media_service.dart';

class PhotoGridTile extends StatelessWidget {
  const PhotoGridTile({
    super.key,
    required this.item,
    required this.onTap,
    this.onLongPress,
    this.selected = false,
    this.selectionMode = false,
  });

  final MediaItem item;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;
  final bool selected;
  final bool selectionMode;

  @override
  Widget build(BuildContext context) {
    final mediaService = MediaService();
    return GestureDetector(
      onTap: onTap,
      onLongPress: onLongPress,
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (item.thumbnailUrl != null)
            CachedNetworkImage(
              imageUrl: item.thumbnailUrl!,
              httpHeaders: mediaService.authHeaders,
              fit: BoxFit.cover,
              placeholder: (context, url) => Container(color: Colors.grey.shade300),
              errorWidget: (context, url, error) => Container(
                color: Colors.grey.shade300,
                child: const Icon(Icons.broken_image_outlined),
              ),
            )
          else
            Container(
              color: Colors.grey.shade800,
              child: Icon(
                item.mediaType == 'video' ? Icons.videocam_outlined : Icons.image_outlined,
                color: Colors.white70,
              ),
            ),
          if (item.mediaType == 'video')
            const Positioned(
              bottom: 4,
              right: 4,
              child: Icon(Icons.play_circle_outline, color: Colors.white, size: 20),
            ),
          if (item.isFavorite)
            const Positioned(
              top: 4,
              right: 4,
              child: Icon(Icons.favorite, color: Colors.redAccent, size: 16),
            ),
          if (selectionMode)
            Positioned(
              top: 4,
              left: 4,
              child: Icon(
                selected ? Icons.check_circle : Icons.radio_button_unchecked,
                color: selected ? Theme.of(context).colorScheme.primary : Colors.white,
              ),
            ),
          if (selectionMode && selected)
            Container(color: Colors.black.withValues(alpha: 0.25)),
        ],
      ),
    );
  }
}
