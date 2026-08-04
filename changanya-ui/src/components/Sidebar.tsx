
import { useState } from "react";

export type Screen = "home" | "library" | "liked" | "queue" | "search";

interface Props {
  current:  Screen;
  onChange: (screen: Screen) => void;
}

const items: { id: Screen; label: string; icon: string }[] = [
  { id: "home",    label: "Home",      icon: "ti-home"     },
  { id: "library", label: "Library",   icon: "ti-books" },
  { id: "liked",   label: "Liked",     icon: "ti-heart"    },
  { id: "queue",   label: "Queue",     icon: "ti-list"     },
];

export default function Sidebar({ current, onChange }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside style={{
      width:        collapsed ? 50 : 180,
      flexShrink:   0,
      background:   "#ede8dc",
      borderRight:  "1.5px solid #1a1612",
      display:      "flex",
      flexDirection: "column",
      padding:      "16px 10px",
      gap:          4,
      transition:   "width .2s",
      overflow:     "hidden",
    }}>

      {items.map(item => (
        <button
          key={item.id}
          onClick={() => onChange(item.id)}
          style={{
            display:        "flex",
            alignItems:     "center",
            gap:            10,
            padding:        "7px 10px",
            borderRadius:   4,
            cursor:         "pointer",
            fontFamily:     "'Caveat', cursive",
            fontSize:       14, fontWeight: 600,
            color:          current === item.id ? "#1a1612" : "#6b6355",
            background:     current === item.id ? "#faf7f0" : "none",
            border:         current === item.id
              ? "1.5px solid #1a1612"
              : "1px solid transparent",
            boxShadow:      current === item.id
              ? "2px 2px 0 #1a1612"
              : "none",
            transition:     "all .12s",
            whiteSpace:     "nowrap",
            overflow:       "hidden",
          }}
        >
          <i
            className={`ti ${item.icon}`}
            style={{ fontSize: 15, flexShrink: 0 }}
            aria-hidden="true"
          />
          {!collapsed && <span>{item.label}</span>}
        </button>
      ))}

      {/* Footer */}
      <div style={{
        marginTop:  "auto",
        display:    "flex",
        gap:        6,
        alignItems: "center",
      }}>
        {!collapsed && (
          <button style={{
            flex:        1,
            fontFamily:  "'Caveat', cursive",
            fontSize:    12, fontWeight: 700,
            color:       "#1a1612", background: "#faf7f0",
            border:      "1.5px solid #1a1612",
            borderRadius: 3, padding: "5px 8px",
            cursor:      "pointer",
            boxShadow:   "2px 2px 0 #1a1612",
            whiteSpace:  "nowrap",
          }}>
            + New Playlist
          </button>
        )}
        <button
          onClick={() => setCollapsed(c => !c)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          style={{
            width:          28, height: 28,
            border:         "1.5px solid #1a1612",
            borderRadius:   3,
            background:     "#faf7f0", color: "#1a1612",
            display:        "flex", alignItems: "center",
            justifyContent: "center",
            cursor:         "pointer", fontSize: 12,
            boxShadow:      "2px 2px 0 #1a1612",
            flexShrink:     0,
          }}
        >
          {collapsed ? "→" : "←"}
        </button>
      </div>

    </aside>
  );
}