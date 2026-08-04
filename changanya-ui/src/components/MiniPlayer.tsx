// persistent mini player — always visible at bottom of every screen

import { Track } from "../hooks/useEngine";
import AlbumArt  from "./AlbumArt";

interface Props {
  track:         Track | null;
  isPlaying:     boolean;
  progressMs:    number;
  onSkip:        () => void;
  onPauseResume: () => void;
  onOpenNowPlaying: () => void;
}

export default function MiniPlayer({
  track, isPlaying, progressMs, onSkip, onPauseResume, onOpenNowPlaying,
}: Props) {
  const duration = track?.duration_ms ?? 0;
  const progress = duration > 0 ? (progressMs / duration) * 100 : 0;

  return (
    <div style={{
      height:          56,
      background:      "#ede8dc",
      borderTop:       "1.5px solid #1a1612",
      display:         "flex",
      alignItems:      "center",
      padding:         "0 16px",
      gap:             12,
      flexShrink:      0,
    }}>

      {/* Mini art */}
      <div style={{ width: 36, height: 36, flexShrink: 0 }}>
        <AlbumArt
          artworkPath={track?.artwork_path ?? null}
          artist={track?.artist ?? null}
          isPlaying={isPlaying}
        />
      </div>

      {/* Track info */}
      <div style={{ minWidth: 0, width: 160, flexShrink: 0 }}>
        <div style={{
          fontFamily:   "'Caveat', cursive",
          fontSize:     13, fontWeight: 700,
          color:        "#1a1612",
          whiteSpace:   "nowrap", overflow: "hidden",
          textOverflow: "ellipsis",
        }}>
          {track?.title ?? "Nothing playing"}
        </div>
        <div style={{
          fontFamily: "'Kalam', cursive",
          fontSize:   11, color: "#8a8070",
        }}>
          {track?.artist ?? "—"}
        </div>
      </div>

      {/* Progress */}
      <div style={{ flex: 1, maxWidth: 220 }}>
        <div style={{
          height:     3,
          background: "#d6d0c4",
          border:     "1px solid #b0a898",
        }}>
          <div style={{
            height:     "100%",
            width:      `${progress}%`,
            background: "#1a1612",
          }} />
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {[
          { label: "Previous", icon: "ti-player-track-prev",
            action: async () => {
              const { invoke } = await import("@tauri-apps/api/core");
              invoke("back").catch(console.error);
            }},
          { label: isPlaying ? "Pause" : "Play",
            icon:  isPlaying ? "ti-player-pause" : "ti-player-play",
            play:  true, action: onPauseResume },
          { label: "Next", icon: "ti-player-track-next",
            action: onSkip },
        ].map(btn => (
          <button
            key={btn.label}
            aria-label={btn.label}
            onClick={btn.action}
            style={{
              width:          btn.play ? 34 : 28,
              height:         btn.play ? 34 : 28,
              border:         "1.5px solid #1a1612",
              borderRadius:   4,
              background:     btn.play ? "#1a1612" : "#faf7f0",
              color:          btn.play ? "#faf7f0" : "#1a1612",
              display:        "flex",
              alignItems:     "center",
              justifyContent: "center",
              cursor:         "pointer",
              fontSize:       btn.play ? 15 : 13,
              boxShadow:      `2px 2px 0 ${btn.play ? "#6b6355" : "#1a1612"}`,
            }}
          >
            <i className={`ti ${btn.icon}`} aria-hidden="true" />
          </button>
        ))}
      </div>

      {/* Open Now Playing */}
      <button
        onClick={onOpenNowPlaying}
        style={{
          fontFamily:  "'Caveat', cursive",
          fontSize:    12, fontWeight: 700,
          color:       "#1a1612", background: "#faf7f0",
          border:      "1.5px solid #1a1612",
          borderRadius: 3, padding: "3px 12px",
          cursor:      "pointer",
          boxShadow:   "2px 2px 0 #1a1612",
          whiteSpace:  "nowrap",
        }}
      >
        Now Playing ↑
      </button>

    </div>
  );
}