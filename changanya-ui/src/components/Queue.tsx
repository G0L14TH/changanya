// src/components/Queue.tsx
//
// Queue panel — matches sketch layout with
// thumbnail, song, artist, duration, drag handle.
// Clicking a song plays it immediately.

import AlbumArt  from "./AlbumArt";
import { QueueItem } from "../hooks/useEngine";

interface Props {
  items:       QueueItem[];
  onPlayItem:  (id: string) => void;
  onClear:     () => void;
}

export default function Queue({ items, onPlayItem, onClear }: Props) {
  const btn = (label: string, onClick: () => void) => (
    <button
      onClick={onClick}
      style={{
        fontFamily: "'Caveat', cursive",
        fontSize: 12, fontWeight: 700,
        color: "#1a1612", background: "#f5f0e6",
        border: "1.5px solid #1a1612", borderRadius: 3,
        padding: "3px 14px", cursor: "pointer",
        boxShadow: "2px 2px 0 #1a1612",
      }}
    >
      {label}
    </button>
  );

  return (
    <div style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      padding: 18,
      background: "#ede8dc",
      maxHeight: "100%",
      overflowY: "auto",
    }}>
    <div style={{
      padding: "5px 8px",
    }}>
    <div style={{ width: 32, height: 32, flexShrink: 0}}></div>
    </div>

      {/* HEADER */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 12,
      }}>
        <div style={{
          fontFamily: "'Caveat', cursive",
          fontSize: 16, fontWeight: 700, color: "#1a1612",
        }}>
          Up Next · Queue ({items.length})
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {btn("Save Queue", () => {})}
          {btn("Clear", onClear)}
        </div>
      </div>

      {/* QUEUE ROWS */}
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {items.length === 0 && (
          <div style={{
            fontFamily: "'Kalam', cursive",
            fontSize: 13, color: "#8a8070",
            padding: "20px 0", textAlign: "center",
          }}>
            Queue is empty — the engine will keep picking
          </div>
        )}

        {items.map((item) => (
          <div
            key={item.id}
            onClick={() => onPlayItem(item.id)}
            style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "7px 8px",
              border: "1.5px solid transparent",
              borderRadius: 3,
              background: "#f5f0e6",
              cursor: "pointer",
              transition: "all .12s",
            }}
            onMouseEnter={e => {
              const el = e.currentTarget;
              el.style.borderColor = "#1a1612";
              el.style.boxShadow   = "2px 2px 0 #1a1612";
              el.style.transform   = "translate(-1px,-1px)";
            }}
            onMouseLeave={e => {
              const el = e.currentTarget;
              el.style.borderColor = "transparent";
              el.style.boxShadow   = "none";
              el.style.transform   = "none";
            }}
          >
            {/* Mini art */}
            <div style={{ width: 36, height: 36, flexShrink: 0 }}>
              <AlbumArt
                artworkPath={item.artwork_path}
                artist={item.artist}
                isPlaying={false}
                size="mini"
              />
            </div>

            {/* Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontFamily: "'Caveat', cursive",
                fontSize: 14, fontWeight: 700, color: "#1a1612",
                whiteSpace: "nowrap", overflow: "hidden",
                textOverflow: "ellipsis",
              }}>{item.title}</div>
              <div style={{
                fontFamily: "'Kalam', cursive",
                fontSize: 11, color: "#8a8070",
                whiteSpace: "nowrap", overflow: "hidden",
                textOverflow: "ellipsis",
              }}>{item.artist}</div>
            </div>

            {/* Drag handle */}
            <i
              className="ti ti-grip-vertical"
              aria-hidden="true"
              style={{ fontSize: 15, color: "#b0a898", flexShrink: 0 }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}