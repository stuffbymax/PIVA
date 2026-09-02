class MediaItem {
  final int id;
  final bool deleted;
  final String? originalFilename;
  final String? mediaType; // 'photo' | 'video'
  final String? mimeType;
  final int fileSize;
  final int? width;
  final int? height;
  final int? durationMs;
  final String? checksum;
  final double? takenAt;
  final double createdAt;
  final double updatedAt;
  final bool isFavorite;
  final bool isTrashed;
  final double? trashedAt;
  final String? downloadUrl;
  final String? thumbnailUrl;

  MediaItem({
    required this.id,
    required this.deleted,
    this.originalFilename,
    this.mediaType,
    this.mimeType,
    this.fileSize = 0,
    this.width,
    this.height,
    this.durationMs,
    this.checksum,
    this.takenAt,
    required this.createdAt,
    required this.updatedAt,
    this.isFavorite = false,
    this.isTrashed = false,
    this.trashedAt,
    this.downloadUrl,
    this.thumbnailUrl,
  });

  factory MediaItem.fromJson(Map<String, dynamic> json) {
    return MediaItem(
      id: json['id'] as int,
      deleted: json['deleted'] as bool? ?? false,
      originalFilename: json['original_filename'] as String?,
      mediaType: json['media_type'] as String?,
      mimeType: json['mime_type'] as String?,
      fileSize: (json['file_size'] as num?)?.toInt() ?? 0,
      width: (json['width'] as num?)?.toInt(),
      height: (json['height'] as num?)?.toInt(),
      durationMs: (json['duration_ms'] as num?)?.toInt(),
      checksum: json['checksum'] as String?,
      takenAt: (json['taken_at'] as num?)?.toDouble(),
      createdAt: (json['created_at'] as num?)?.toDouble() ?? 0,
      updatedAt: (json['updated_at'] as num?)?.toDouble() ?? 0,
      isFavorite: json['is_favorite'] as bool? ?? false,
      isTrashed: json['is_trashed'] as bool? ?? false,
      trashedAt: (json['trashed_at'] as num?)?.toDouble(),
      downloadUrl: json['download_url'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
    );
  }

  DateTime get displayDate {
    final epoch = takenAt ?? createdAt;
    return DateTime.fromMillisecondsSinceEpoch((epoch * 1000).round());
  }

  MediaItem copyWith({bool? isFavorite, bool? isTrashed}) {
    return MediaItem(
      id: id,
      deleted: deleted,
      originalFilename: originalFilename,
      mediaType: mediaType,
      mimeType: mimeType,
      fileSize: fileSize,
      width: width,
      height: height,
      durationMs: durationMs,
      checksum: checksum,
      takenAt: takenAt,
      createdAt: createdAt,
      updatedAt: updatedAt,
      isFavorite: isFavorite ?? this.isFavorite,
      isTrashed: isTrashed ?? this.isTrashed,
      trashedAt: trashedAt,
      downloadUrl: downloadUrl,
      thumbnailUrl: thumbnailUrl,
    );
  }
}
