import 'media_item.dart';

class Album {
  final int id;
  final bool deleted;
  final String? name;
  final int? coverMediaId;
  final int itemCount;
  final double? createdAt;
  final double? updatedAt;
  final List<MediaItem> items;

  Album({
    required this.id,
    required this.deleted,
    this.name,
    this.coverMediaId,
    this.itemCount = 0,
    this.createdAt,
    this.updatedAt,
    this.items = const [],
  });

  factory Album.fromJson(Map<String, dynamic> json) {
    final itemsJson = json['items'] as List<dynamic>?;
    return Album(
      id: json['id'] as int,
      deleted: json['deleted'] as bool? ?? false,
      name: json['name'] as String?,
      coverMediaId: (json['cover_media_id'] as num?)?.toInt(),
      itemCount: (json['item_count'] as num?)?.toInt() ?? 0,
      createdAt: (json['created_at'] as num?)?.toDouble(),
      updatedAt: (json['updated_at'] as num?)?.toDouble(),
      items: itemsJson == null
          ? const []
          : itemsJson
              .map((e) => MediaItem.fromJson(e as Map<String, dynamic>))
              .toList(),
    );
  }
}
