// reusable song card — used in Recently Played and Recommended

import { useState } from "react";
import AlbumArt   from "./AlbumArt";
import { HomeSong } from "../hooks/useEngine";

interface Props {
  song:     HomeSong;
  featured?: boolean;
  onClick:  (song: HomeSong) => void;
}

export default function SongCard({ song, featured = false, onClick }: Props) {
  const [hovered, setHovered] = useState(false);

  if (featured) {
    return (
      <div
        onClick={() => onClick(song)}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          background:   "#faf7f0",
          border:       "1.5px solid #1a1612",
          borderRadius: 5,
          overflow:     "hidden",
          cursor:       "pointer",
          boxShadow:    hovered ? "3px 3px 0 #1a1612" : "2px 2px 0 #1a1612",
          transform:    hovered ? "translate(-1px,-1px)" : "none",
          transition:   "all .12s",
        }}
      >
        <AlbumArt
          artworkPath={song.artwork_path}
          artist={song.artist}
          isPlaying={false}
        />
        <div style={{ padding: "8px 10px" }}>
          <div style={{
            fontFamily:   "'Caveat', cursive",
            fontSize:     14, fontWeight: 700,
            color:        "#1a1612",
            whiteSpace:   "nowrap", overflow: "hidden",
            textOverflow: "ellipsis",
          }}>
            {song.title || "Unknown"}
          </div>
          <div style={{
            fontFamily: "'Kalam', cursive",
            fontSize:   12, color: "#8a8070",
          }}>
            {song.artist || "Unknown"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={() => onClick(song)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background:   "#faf7f0",
        border:       "1.5px solid #1a1612",
        borderRadius: 5,
        overflow:     "hidden",
        cursor:       "pointer",
        boxShadow:    hovered ? "3px 3px 0 #1a1612" : "2px 2px 0 #1a1612",
        transform:    hovered ? "translate(-1px,-1px)" : "none",
        transition:   "all .12s",
        display:      "flex",
        alignItems:   "center",
        gap:          10,
        padding:      8,
      }}
    >
      <div style={{ width: 44, height: 44, flexShrink: 0 }}>
        <AlbumArt
          artworkPath={song.artwork_path}
          artist={song.artist}
          isPlaying={false}
        />
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{
          fontFamily:   "'Caveat', cursive",
          fontSize:     13, fontWeight: 700,
          color:        "#1a1612",
          whiteSpace:   "nowrap", overflow: "hidden",
          textOverflow: "ellipsis",
        }}>
          {song.title || "Unknown"}
        </div>
        <div style={{
          fontFamily: "'Kalam', cursive",
          fontSize:   11, color: "#8a8070",
        }}>
          {song.artist || "Unknown"}
        </div>
      </div>
    </div>
  );
}