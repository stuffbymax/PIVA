class AppUser {
  final int id;
  final String username;
  final String? email;
  final int quotaBytes;
  final int storageUsedBytes;
  final bool isAdmin;

  AppUser({
    required this.id,
    required this.username,
    required this.email,
    required this.quotaBytes,
    required this.storageUsedBytes,
    required this.isAdmin,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: json['id'] as int,
      username: json['username'] as String,
      email: json['email'] as String?,
      quotaBytes: (json['quota_bytes'] as num?)?.toInt() ?? 0,
      storageUsedBytes: (json['storage_used_bytes'] as num?)?.toInt() ?? 0,
      isAdmin: json['is_admin'] as bool? ?? false,
    );
  }

  double get usedFraction =>
      quotaBytes <= 0 ? 0 : (storageUsedBytes / quotaBytes).clamp(0, 1).toDouble();
}
