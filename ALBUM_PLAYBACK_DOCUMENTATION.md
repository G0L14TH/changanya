# Album Playback and Library Enhancements

## Overview
This update resolves the Python IPC syntax error at `src/shuffle_engine/ipc.py:609`, restores the global shuffle toggle outside album mode, and implements a richer album playback experience in the library.

The new behavior includes:
- fixed IPC command parsing so `seek_relative` and later actions are handled correctly
- album item ordering preserved in the original file order
- album popup actions using icons for Play, Shuffle, and Edit Tags
- album track rows that show a play icon on hover and can be clicked to play from that track
- a dedicated "play from here" per-track action in the album popup
- album playback now preserves the current album queue order when a track is selected mid-album
- album-mode playback constrained to album songs only
- album-mode shuffle scoped to the selected album (OFF by default; users can enable album shuffle to randomize only the selected album's items)
- when album playback starts the engine emits the full album queue to the UI so the playlist shows the full album length; the upcoming list shortens as songs are consumed
- album playback stops when the album queue finishes (future option: continue into recommended songs)
- the now-playing panel exposes a shared toggle: outside album mode it controls global shuffle, while inside album mode it controls album-only shuffle via the new `set_album_shuffle` backend command.

## Files Changed

### 1. `src/shuffle_engine/ipc.py`
- Fixed the indentation bug in the `run_ipc()` parser chain around the `like_song` / `seek_relative` branch, resolving the error on line 609.
- Added support for a new `play_album_track` action from the UI.
- Preserved album ordering when emitting album track listings by ordering by `file_path`.
- Kept library title sorting logic that places symbol-starting titles before A–Z.
- Key changed locations: around lines 609, 621, and 526.

### 2. `src/shuffle_engine/engine.py`
- Added `play_album_track()` to play a specific song inside an album while continuing album-mode playback.
- Preserved the live album queue order when a track is selected mid-album, avoiding a reset to the original album ordering.
- Ensured `play_album()` queues all album songs and enters album playback mode.
- Updated `_play_next()` so album playback stops when the album queue empties instead of falling back to normal shuffle.
- Updated `_handle_player_event()` so the engine stops cleanly after album completion.

### 3. `src/catalog/repository.py`
- Confirmed `get_songs_by_album()` already orders album songs by `file_path`, preserving the original album sequence.

### 4. `changanya-ui/src/screens/Library.tsx`
- Added album popup row hover state and a left-side play icon for hovered album tracks.
- Added click-to-play behavior for individual album tracks inside the popup.
- Removed separate rectangular track action buttons inside the album popup; actions are now icon-based.
- Kept popup actions for Play, Shuffle, and Edit Tags.
- Preserved original album order and displayed track durations.

### 5. `changanya-ui/src/hooks/useEngine.ts`
- Added `playAlbumTrack()` to invoke the new backend command.
- Added `setGlobalShuffle()` and `setAlbumShuffle()` so the now-playing UI can toggle global vs album-only shuffle.
- Fixed the library songs event handling case from `library_spngs` to `library_songs` so song data loads correctly.

### 6. `changanya-ui/src-tauri/src/main.rs`
- Exposed the new `play_album_track` Tauri command.
- Added `set_global_shuffle` and `set_album_shuffle` Tauri commands and registered them in the invoke handler.

## How the Updated Album Experience Works
1. Open the Library screen and switch to the Albums tab.
2. Click an album card to open the album popup.
3. In the popup, use the icon buttons to:
   - play the album from the first track (album shuffle is OFF by default),
   - enable album shuffle to shuffle only the selected album's items,
   - edit the album tags.
4. Hover over any track row in the album popup to reveal a play icon on the left.
5. Click a hovered track row to start album playback from that track and continue through the remaining album songs.
6. When album playback reaches the end of the album queue, playback stops instead of continuing with global shuffle.

## Important Behavior Notes
- Album songs are emitted and queued in the original file order.
- When album playback begins the engine emits the full album queue to the UI so the queue shows the whole album length at the start; as each album track is played the UI's upcoming list shrinks accordingly.
- By default album-mode shuffle is OFF. The user can enable album shuffle while album mode is active — this will shuffle only the selected album's songs and will not affect the global shuffle state.
- Playing a specific song from an album ("Play from here") begins album-mode playback from that track and preserves the album-mode queue order for remaining tracks.
- Selecting a track while an album is already playing preserves the live album queue order instead of resetting playback to a different queue.
- Clicking an upcoming queue item while album mode is active now continues album-mode playback instead of exiting to global shuffle.
- The now-playing UI shows album mode status; the shuffle control works in both cases: outside album mode it toggles global shuffle, while inside album mode it toggles album-only shuffle.
- Album playlist emission now sends the full remaining album queue to the UI, so the queue area starts with the whole album length and shrinks as the album is consumed.
- Explicitly playing a single song outside of album mode still exits album mode and returns to normal playback.
- (Future) After an album finishes the player may optionally stop or continue into recommended tracks — this is a planned enhancement.

## Validation
- Frontend build succeeded: `npm run build` in `changanya-ui`.
- Python syntax verified for `src/shuffle_engine/ipc.py` and `src/shuffle_engine/engine.py`.

If you want, I can also add a short user-facing tooltip in the album popup explaining album-mode behavior.