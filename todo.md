> AI gen todo list for the app. This is a living document and will be updated as we go.
### Finish album feature set
This is the best single milestone because it is already partially implemented and it adds the most obvious product value.

#### Required work
- create album
- rename album
- delete album
- add photo to album
- remove photo from album
- set album cover
- album detail view
- album list refresh after changes

#### Why this is the right “one”
- it is already in the codebase
- backend supports it
- Flutter screens already exist
- it gives the app a real “library” feel
- it unlocks the next features more naturally

#### Files involved
- `albums.py`
- `album_service.dart`
- `album_provider.dart`
- `albums_screen.dart`
- `album_detail_screen.dart`

#### What to finish specifically
- album rename works from UI
- album delete refreshes list correctly
- cover selection is obvious and works
- add/remove item updates item count immediately
- album detail view reloads after mutation