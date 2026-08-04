// src/App.tsx

import { useState, useCallback } from "react";
import { useEngine }    from "./hooks/useEngine";
import { useKeyboard }  from "./hooks/useKeyboard";
import Sidebar, { Screen } from "./components/Sidebar";
import MiniPlayer       from "./components/MiniPlayer";
import NowPlaying       from "./components/NowPlaying";
import Queue            from "./components/Queue";
import Home             from "./screens/Home";
import { HomeSong }     from "./hooks/useEngine";
import Library          from "./screens/Library";

export default function App() {
  const {
    state,
    skip,
    pauseResume,
    playSpecific,
    seekTo,
    loadHomeData,
    loadLibrarySongs,
    loadLibraryArtists,
    loadLibraryAlbums,
    loadAlbumSongs,
    playAlbum,
    setGlobalShuffle,
    setAlbumShuffle,
    playAlbumTrack,
    editAlbumTags,
  } = useEngine();

  const [screen,         setScreen]        = useState<Screen>("home");
  const [nowPlayingOpen, setNowPlayingOpen] = useState(false);

  const handleBack = useCallback(async () => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("back").catch(console.error);
  }, []);

  useKeyboard({
    onSkip:        skip,
    onPauseResume: pauseResume,
    onBack:        handleBack,
  });

  const handlePlaySong = useCallback((song: HomeSong) => {
    playSpecific(song.id);
    setNowPlayingOpen(true);
  }, [playSpecific]);

  return (
    <div style={{
      width:         "100vw",
      height:        "100vh",
      background:    "#f5f0e6",
      display:       "flex",
      flexDirection: "column",
      overflow:      "hidden",
    }}>

      {/* TOP NAV */}
      <nav style={{
        height:      46,
        background:  "#ede8dc",
        borderBottom: "1.5px solid #1a1612",
        display:     "flex",
        alignItems:  "center",
        padding:     "0 18px",
        gap:         16,
        flexShrink:  0,
      }}>
        <div style={{
          fontFamily: "'Caveat', cursive",
          fontSize:   18, fontWeight: 700,
          color:      "#1a1612",
          display:    "flex", alignItems: "center", gap: 6,
        }}>
          <div style={{
            width:          20, height: 20,
            borderRadius:   "50%",
            border:         "2px solid #1a1612",
            display:        "flex",
            alignItems:     "center",
            justifyContent: "center",
            fontSize:       9, fontWeight: 700,
          }}>©</div>
          CHANGANYA
        </div>

        {/* Search bar */}
        <div style={{
          flex:         1, maxWidth: 400, margin: "0 auto",
          display:      "flex", alignItems: "center", gap: 8,
          background:   "#faf7f0",
          border:       "1.5px solid #1a1612",
          borderRadius: 4,
          padding:      "5px 12px",
          boxShadow:    "2px 2px 0 #1a1612",
        }}>
          <i
            className="ti ti-search"
            style={{ color: "#b0a898", fontSize: 14 }}
            aria-hidden="true"
          />
          <input
            type="text"
            placeholder="Search library, artists, tracks"
            aria-label="Search"
            style={{
              border:     "none",
              background: "none",
              outline:    "none",
              fontFamily: "'Kalam', cursive",
              fontSize:   13,
              color:      "#1a1612",
              width:      "100%",
            }}
          />
        </div>

        {/* Status */}
        <div style={{
          fontFamily: "'Kalam', cursive",
          fontSize:   11, color: "#8a8070",
        }}>
          {state.status}
        </div>

        <button
          aria-label="Settings"
          style={{
            width:          30, height: 30,
            border:         "1.5px solid #1a1612",
            borderRadius:   4,
            background:     "#faf7f0", color: "#1a1612",
            display:        "flex", alignItems: "center",
            justifyContent: "center",
            cursor:         "pointer", fontSize: 14,
            boxShadow:      "2px 2px 0 #1a1612",
          }}
        >
          <i className="ti ti-settings" aria-hidden="true" />
        </button>
      </nav>

      {/* MAIN — sidebar + content */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden", position: "relative" }}>

        <Sidebar current={screen} onChange={setScreen} />

        {/* SCREEN CONTENT */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {screen === "home" && (
            <Home
              homeData={state.homeData}
              onLoadData={loadHomeData}
              onPlaySong={handlePlaySong}
              onOpenNowPlaying={() => setNowPlayingOpen(true)}
            />
          )}
          {screen === "queue" && (
            <Queue
              items={state.queue}
              onPlayItem={playSpecific}
              onClear={() => {}}
            />
          )}
          {/* Library, Liked, Search — coming in later phases */}
          {(screen === "library" || screen === "liked") && (
            <div style={{
              flex:           1,
              display:        "flex",
              alignItems:     "stretch",
              justifyContent: "flex-start",
              fontFamily:     "'Caveat', cursive",
              fontSize:       18, color: "#8a8070",
            }}>
              {screen === "library" && (
                <Library
                  libraryData={state.libraryData}
                  albumSongs={state.albumSongs}
                  onLoadSongs={loadLibrarySongs}
                  onLoadArtists={loadLibraryArtists}
                  onLoadAlbums={loadLibraryAlbums}
                  onLoadAlbumSongs={loadAlbumSongs}
                  onPlaySong={(id) => {
                    playSpecific(id);
                    setNowPlayingOpen(true);
                  }}
                  onPlayAlbum={playAlbum}
                  onPlayAlbumTrack={playAlbumTrack}
                  onEditAlbumTags={editAlbumTags}
                />
              )}
            </div>
          )}
        </div>

        {/* NOW PLAYING MODAL — floats over everything */}
        {nowPlayingOpen && (
          <>
            {/* Backdrop */}
            <div
              onClick={() => setNowPlayingOpen(false)}
              style={{
                position:   "absolute",
                inset:      0,
                background: "rgba(26,22,18,0.35)",
                zIndex:     40,
              }}
            />
            {/* Floating widget */}
            <div style={{
              position:     "absolute",
              top:          "50%",
              left:         "50%",
              transform:    "translate(-50%, -50%)",
              zIndex:       50,
              display:      "flex",
              gap:          0,
              background:   "#faf7f0",
              border:       "2px solid #1a1612",
              borderRadius: 8,
              boxShadow:    "6px 6px 0 #1a1612",
              overflow:     "hidden",
              maxHeight:    "85vh",
            }}>
              <NowPlaying
                track={state.currentTrack}
                isPlaying={state.isPlaying}
                progressMs={state.progressMs}
                shuffleEnabled={state.shuffleEnabled}
                albumShuffleEnabled={state.albumShuffleEnabled}
                albumMode={state.albumMode}
                onToggleShuffle={setGlobalShuffle}
                onToggleAlbumShuffle={setAlbumShuffle}
                onSkip={skip}
                onPauseResume={pauseResume}
                onSeek={seekTo}
              />
              <div style={{
                width:        280,
                borderLeft:   "1.5px solid #b0a898",
                overflowY:    "auto",
              }}>
                <Queue
                  items={state.queue}
                  onPlayItem={(id) => {
                    if (state.currentTrack?.albumMode && state.currentTrack.album && state.currentTrack.artist) {
                      playAlbumTrack(state.currentTrack.album, state.currentTrack.artist, id);
                    } else {
                      playSpecific(id);
                    }
                  }}
                  onClear={() => {}}
                />
              </div>
              {/* Close button */}
              <button
                onClick={() => setNowPlayingOpen(false)}
                style={{
                  position:     "absolute",
                  top:          10, right: 10,
                  width:        28, height: 28,
                  border:       "1.5px solid #1a1612",
                  borderRadius: 4,
                  background:   "#faf7f0", color: "#1a1612",
                  display:      "flex", alignItems: "center",
                  justifyContent: "center",
                  cursor:       "pointer", fontSize: 14,
                  boxShadow:    "2px 2px 0 #1a1612",
                  zIndex:       10,
                }}
                aria-label="Close Now Playing"
              >
                <i className="ti ti-x" aria-hidden="true" />
              </button>
            </div>
          </>
        )}

      </div>

      {/* MINI PLAYER — always visible */}
      <MiniPlayer
        track={state.currentTrack}
        isPlaying={state.isPlaying}
        progressMs={state.progressMs}
        onSkip={skip}
        onPauseResume={pauseResume}
        onOpenNowPlaying={() => setNowPlayingOpen(true)}
      />

      {/* FOOTER */}
      <div style={{
        height:          36,
        background:      "#1a1612",
        display:         "flex",
        alignItems:      "center",
        justifyContent:  "space-between",
        padding:         "0 18px",
        flexShrink:      0,
      }}>
        <span style={{
          fontFamily:  "'Caveat', cursive",
          fontSize:    13, fontWeight: 700,
          color:       "#ede8dc", letterSpacing: ".06em",
        }}>
          CHANGANYA
        </span>
        <span style={{
          fontFamily: "'Kalam', cursive",
          fontSize:   10, color: "#6b6355",
        }}>
          © 2026 CHANGANYA ENGINE, Inc. All rights reserved.
        </span>
      </div>

    </div>
  );
}