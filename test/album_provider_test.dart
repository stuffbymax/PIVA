import 'package:flutter_test/flutter_test.dart';
import 'package:photo_app/models/album.dart';
import 'package:photo_app/providers/album_provider.dart';

void main() {
  group('AlbumProvider', () {
    test('updateAlbum refreshes the matching album record', () {
      final provider = AlbumProvider();
      provider.albums = [
        Album(id: 1, deleted: false, name: 'Old name', coverMediaId: 2, itemCount: 3),
      ];

      provider.updateAlbum(
        Album(id: 1, deleted: false, name: 'New name', coverMediaId: 99, itemCount: 3),
      );

      expect(provider.albums.first.name, 'New name');
      expect(provider.albums.first.coverMediaId, 99);
    });
  });
}
