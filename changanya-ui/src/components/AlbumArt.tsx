
import { useState, useEffect } from "react";
import { artistGradient, artworkUrl } from "../utils/artUtils";

interface Props {
  artworkPath: string | null;
  artist:      string | null;
  isPlaying:   boolean;
  size?:       "full" | "mini";
}

export default function AlbumArt({
  artworkPath,
  artist,
  isPlaying,
}: Props) {
  const [imgUrl,     setImgUrl]     = useState<string | null>(null);
  const [imgFailed,  setImgFailed]  = useState(false);

  const gradient = artistGradient(artist);

  // Resolve the asset URL asynchronously
  useEffect(() => {
    setImgUrl(null);
    setImgFailed(false);

    if (!artworkPath) return;

    artworkUrl(artworkPath).then(url => {
      if (url) setImgUrl(url);
    });
  }, [artworkPath]);

  const showReal = imgUrl && !imgFailed;

  return (
    <div style={{
      width:       "100%",
      aspectRatio: "1",
      border:      "1.5px solid #1a1612",
      position:    "relative",
      overflow:    "hidden",
      background:  showReal ? "#ddd7cc" : gradient,
      flexShrink:  0,
    }}>
      {showReal ? (
        <img
          src={imgUrl}
          alt={artist || "Album art"}
          onError={() => setImgFailed(true)}
          style={{
            width:      "100%",
            height:     "100%",
            objectFit:  "cover",
            display:    "block",
          }}
        />
      ) : (
        <svg
          viewBox="0 0 100 100"
          fill="none"
          style={{
            position: "absolute", inset: 0,
            width: "100%", height: "100%",
          }}
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <line x1="0" y1="0" x2="100" y2="100"
            stroke="rgba(255,255,255,0.15)" strokeWidth="1.5"/>
          <line x1="100" y1="0" x2="0" y2="100"
            stroke="rgba(255,255,255,0.15)" strokeWidth="1.5"/>
          <rect x="0.5" y="0.5" width="99" height="99"
            stroke="rgba(255,255,255,0.1)" strokeWidth="1"/>
        </svg>
      )}

      {/* Equaliser bars when playing */}
      {isPlaying && (
        <div style={{
          position:   "absolute",
          top:        10,
          right:      12,
          display:    "flex",
          alignItems: "flex-end",
          gap:        2,
        }}>
          {[7, 13, 9].map((h, i) => (
            <div
              key={i}
              style={{
                width:           3,
                height:          h,
                background:      showReal
                  ? "#fff"
                  : "rgba(255,255,255,0.7)",
                borderRadius:    1,
                animation:       `eq ${0.7 + i * 0.15}s ease-in-out infinite alternate`,
                animationDelay:  `${i * 0.18}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}