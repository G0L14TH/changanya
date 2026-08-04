// src/components/NowPlaying.tsx

import { useEffect, useState, type CSSProperties } from "react";
import AlbumArt     from "./AlbumArt";
import ToggleSwitch from "./ToggleSwitch";
import { Track }    from "../hooks/useEngine";

interface Props {
  track:                  Track | null;
  isPlaying:              boolean;
  progressMs:             number;
  shuffleEnabled:         boolean;
  albumShuffleEnabled:    boolean;
  albumMode:              boolean;
  onToggleShuffle:        (enabled: boolean) => void;
  onToggleAlbumShuffle:   (enabled: boolean) => void;
  onSkip:                 () => void;
  onPauseResume:          () => void;
  onSeek:                 (positionMs: number) => void;
}

type RepeatState = "All" | "One" | "Off";

export default function NowPlaying({
  track, isPlaying, progressMs, shuffleEnabled, albumShuffleEnabled, onToggleShuffle, onToggleAlbumShuffle, onSkip, onPauseResume, onSeek,
}: Props): import("react").JSX.Element {
  const [repeat,  setRepeat]  = useState<RepeatState>("All");
  const [volOpen, setVolOpen] = useState(false);
  const [volume,  setVolume]  = useState(75);

  const cycleRepeat = () =>
    setRepeat(r => r === "All" ? "One" : r === "One" ? "Off" : "All");

  const duration  = track?.duration_ms ?? 0;
  const progress  = duration > 0 ? (progressMs / duration) * 100 : 0;
  const remaining = duration - progressMs;
  const albumMode = track?.albumMode ?? false;

  const fmt = (ms: number) => {
    const total = Math.floor(ms / 1000);
    const m     = Math.floor(total / 60);
    const sec   = total % 60;
    return `${m}:${String(sec).padStart(2, "0")}`;
  };

  const ctrlBtn = (style?: CSSProperties): CSSProperties => ({
    width:          44,
    height:         44,
    border:         "1.5px solid #1a1612",
    borderRadius:   5,
    background:     "#f5f0e6",
    color:          "#1a1612",
    display:        "flex",
    alignItems:     "center",
    justifyContent: "center",
    cursor:         "pointer",
    fontSize:       20,
    boxShadow:      "2px 2px 0 #1a1612",
    ...style,
  });

  // Close volume panel when clicking outside
  useEffect(() => {
    if (!volOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest(".vol-container")) {
        setVolOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [volOpen]);

  return (
    <div style={{
      display:       "flex",
      flexDirection: "column",
      gap:           14,
      padding:       18,
      borderRight:   "1.5px solid #b0a898",
      background:    "#ede8dc",
      minWidth:      280,
      width:         300,
      overflowY:     "auto",
    }}>

      {/* ALBUM ART */}
      <div key={`art-${track?.id ?? "empty"}`} className="track-fade">
        <AlbumArt
          artworkPath={track?.artwork_path ?? null}
          artist={track?.artist ?? null}
          isPlaying={isPlaying}
        />
      </div>

      {/* YEAR · ALBUM */}
      <div style={{
        textAlign:  "center",
        fontFamily: "'Kalam', cursive",
        fontSize:   11,
        color:      "#8a8070",
      }}>
        {track
          ? `${track.year ?? "N/A"} · ${track.album || "Unknown Album"}`
          : "—"}
      </div>

      {/* TRACK INFO */}
      <div key={track?.id ?? "empty"} className="track-fade">
        <div style={{
          fontFamily:   "'Caveat', cursive",
          fontSize:     22,
          fontWeight:   700,
          color:        "#1a1612",
          lineHeight:   1.1,
          marginBottom: 3,
          whiteSpace:   "nowrap",
          overflow:     "hidden",
          textOverflow: "ellipsis",
        }}>
          {track?.title ?? "—"}
        </div>
        <div style={{
          fontFamily:   "'Kalam', cursive",
          fontSize:     13,
          color:        "#6b6355",
          marginBottom: 5,
        }}>
          {track?.artist ?? "—"}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <span style={{
            fontFamily:    "'Caveat', cursive",
            fontSize:      10,
            fontWeight:    700,
            letterSpacing: ".1em",
            textTransform: "uppercase",
            border:        "1.5px solid #b0a898",
            borderRadius:  2,
            padding:       "1px 6px",
            color:         "#8a8070",
          }}>
            Album
          </span>
          <span style={{
            fontFamily:   "'Kalam', cursive",
            fontSize:     12,
            color:        "#8a8070",
            whiteSpace:   "nowrap",
            overflow:     "hidden",
            textOverflow: "ellipsis",
          }}>
            {track?.album ?? "—"}
          </span>
          {albumMode && (
            <span style={{
              fontFamily: "'Caveat', cursive",
              fontSize: 10,
              fontWeight: 700,
              color: "#7a1a1a",
              background: "#fde2d6",
              padding: "1px 6px",
              borderRadius: 4,
              border: "1px solid #7a1a1a",
            }}>
              Album Mode
            </span>
          )}
        </div>
      </div>

      {/* ACTION ICONS */}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 6 }}>
        {([
          {
            icon:   track?.liked ? "ti-heart-filled" : "ti-heart",
            label:  "Like",
            active: track?.liked ?? false,
            action: async () => {
              if (!track) return;
              const { invoke } = await import("@tauri-apps/api/core");
              invoke("like_song", { songId: track.id }).catch(console.error);
            },
          },
          {
            icon:   "ti-plus",
            label:  "Add to queue",
            active: false,
            action: async () => {
              const { invoke } = await import("@tauri-apps/api/core");
              invoke("get_state").catch(console.error);
            },
          },
          {
            icon:   "ti-dots",
            label:  "More",
            active: false,
            action: () => {},
          },
        ] as const).map(btn => (
          <button
            key={btn.label}
            aria-label={btn.label}
            onClick={btn.action}
            style={{
              width:          34,
              height:         34,
              border:         `1.5px solid ${btn.active ? "#7a1a1a" : "#1a1612"}`,
              borderRadius:   4,
              background:     "#f5f0e6",
              color:          btn.active ? "#7a1a1a" : "#1a1612",
              display:        "flex",
              alignItems:     "center",
              justifyContent: "center",
              cursor:         "pointer",
              fontSize:       16,
              boxShadow:      `2px 2px 0 ${btn.active ? "#7a1a1a" : "#1a1612"}`,
            }}
          >
            <i className={`ti ${btn.icon}`} aria-hidden="true" />
          </button>
        ))}
      </div>

      {/* PLAYBACK CONTROLS */}
      <div style={{
        display:        "flex",
        flexDirection:  "column",
        alignItems:     "center",
        gap:            12,
      }}>
        {/* Main buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>

          <button
            aria-label="Previous"
            onClick={async () => {
              const { invoke } = await import("@tauri-apps/api/core");
              invoke("back").catch(console.error);
            }}
            style={ctrlBtn()}
          >
            <i className="ti ti-player-track-prev" aria-hidden="true" />
          </button>

          <button
            aria-label={isPlaying ? "Pause" : "Play"}
            onClick={onPauseResume}
            style={ctrlBtn({
              width:      56,
              height:     56,
              border:     "2px solid #1a1612",
              borderRadius: 7,
              background: "#1a1612",
              color:      "#e1cda5",
              fontSize:   24,
              boxShadow:  "3px 3px 0 #6b6355",
            })}
          >
            <i
              className={`ti ${isPlaying
                ? "ti-player-pause"
                : "ti-player-play"}`}
              aria-hidden="true"
            />
          </button>

          <button
            aria-label="Next"
            onClick={onSkip}
            style={ctrlBtn()}
          >
            <i className="ti ti-player-track-next" aria-hidden="true" />
          </button>

        </div>

        {/* TOGGLES */}
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>

          <ToggleSwitch
            on={albumMode ? albumShuffleEnabled : shuffleEnabled}
            label={albumMode
              ? (albumShuffleEnabled ? "Album shuffle on" : "Album shuffle off")
              : "Shuffle"
            }
            onClick={() => {
              if (albumMode) {
                onToggleAlbumShuffle(!albumShuffleEnabled);
              } else {
                onToggleShuffle(!shuffleEnabled);
              }
            }}
          />

          <ToggleSwitch
            on={repeat !== "Off"}
            label={`Repeat ${repeat}`}
            onClick={cycleRepeat}
          />

          {/* VOLUME */}
          <div className="vol-container" style={{ position: "relative" }}>
            <button
              aria-label="Volume"
              onClick={() => setVolOpen(v => !v)}
              style={{
                display:    "flex",
                alignItems: "center",
                gap:        7,
                background: "none",
                border:     "none",
                cursor:     "pointer",
                padding:    0,
              }}
            >
              <div style={{
                width:          46,
                height:         22,
                border:         "1.5px solid #1a1612",
                borderRadius:   4,
                background:     volOpen ? "#1a1612" : "#f5f0e6",
                display:        "flex",
                alignItems:     "center",
                justifyContent: volOpen ? "flex-end" : "flex-start",
                padding:        "0 2px",
                boxShadow:      "2px 2px 0 #1a1612",
                transition:     "background .18s",
              }}>
                <i
                  className={`ti ${volume === 0
                    ? "ti-volume-off"
                    : volume < 50
                    ? "ti-volume-2"
                    : "ti-volume"}`}
                  style={{
                    fontSize: 13,
                    color:    volOpen ? "#f5f0e6" : "#1a1612",
                  }}
                  aria-hidden="true"
                />
              </div>
              <span style={{
                fontFamily: "'Caveat', cursive",
                fontSize:   14,
                fontWeight: 600,
                color:      "#6b6355",
              }}>
                Volume
              </span>
            </button>

            {volOpen && (
              <div style={{
                position:     "absolute",
                bottom:       32,
                left:         0,
                background:   "#f5f0e6",
                border:       "1.5px solid #1a1612",
                borderRadius: 4,
                padding:      "10px 14px",
                boxShadow:    "3px 3px 0 #1a1612",
                zIndex:       99,
                minWidth:     180,
              }}>
                <div style={{
                  display:      "flex",
                  alignItems:   "center",
                  gap:          8,
                  marginBottom: 8,
                }}>
                  <i
                    className="ti ti-volume"
                    style={{ fontSize: 14, color: "#8a8070" }}
                    aria-hidden="true"
                  />
                  <span style={{
                    fontFamily: "'Caveat', cursive",
                    fontSize:   13,
                    color:      "#6b6355",
                    flex:       1,
                  }}>
                    Volume
                  </span>
                  <span style={{
                    fontFamily: "'Caveat', cursive",
                    fontSize:   13,
                    fontWeight: 600,
                    color:      "#1a1612",
                  }}>
                    {volume}%
                  </span>
                </div>
                <input
                  type="range"
                  min={0} max={100} value={volume}
                  aria-label="Volume level"
                  onChange={async (e) => {
                    const vol = Number(e.target.value);
                    setVolume(vol);
                    const { invoke } = await import("@tauri-apps/api/core");
                    invoke("set_volume", { volume: vol }).catch(console.error);
                  }}
                  style={{ width: "100%", accentColor: "#1a1612" }}
                />
              </div>
            )}
          </div>

        </div>
      </div>
      {/* END PLAYBACK CONTROLS */}

      {/* PROGRESS BAR */}
      <div>
        <div style={{
          display:        "flex",
          justifyContent: "space-between",
          fontFamily:     "'Kalam', cursive",
          fontSize:       11,
          color:          "#8a8070",
          marginBottom:   5,
        }}>
          <span>{fmt(progressMs)}</span>
          <span>−{fmt(Math.max(0, remaining))}</span>
        </div>
        <div
          style={{
            height:   4,
            background: "#d6d0c4",
            border:   "1px solid #b0a898",
            cursor:   "pointer",
            position: "relative",
          }}
          onClick={(e) => {
            const rail  = e.currentTarget;
            const rect  = rail.getBoundingClientRect();
            const pct   = Math.max(0, Math.min(1,
              (e.clientX - rect.left) / rect.width
            ));
            const seekMs = Math.round(pct * duration);
            onSeek(seekMs);  // onSeek handles both state update and VLC seek
          }}
        >
          <div style={{
            height:   "100%",
            width:    `${progress}%`,
            background: "#1a1612",
            position: "relative",
          }}>
            <div style={{
              width:     14,
              height:    14,
              border:    "2px solid #1a1612",
              background: "#f5f0e6",
              position:  "absolute",
              right:     -7,
              top:       -6,
              boxShadow: "1px 1px 0 #1a1612",
            }} />
          </div>
        </div>
      </div>

    </div>
  );
}