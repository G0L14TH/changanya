// src/components/ToggleSwitch.tsx
//
// The handwritten toggle — matches sketch exactly.
// Same component used for Shuffle, Repeat, Volume.

interface Props {
  on:       boolean;
  label:    string;
  onClick:  () => void;
  disabled?: boolean;
}

export default function ToggleSwitch({ on, label, onClick, disabled = false }: Props) {
  return (
    <div
      onClick={() => {
        if (!disabled) onClick();
      }}
      role="switch"
      aria-checked={on}
      aria-label={label}
      style={{
        display: "flex", alignItems: "center",
        gap: 8,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.55 : 1,
        userSelect: "none",
      }}
    >
      {/* Track */}
      <div style={{
        width: 46, height: 22,
        border: "1.5px solid #1a1612",
        borderRadius: 4,
        background: on ? "#1a1612" : "#f5f0e6",
        position: "relative",
        boxShadow: "2px 2px 0 #1a1612",
        transition: "background .18s",
        flexShrink: 0,
        opacity: disabled ? 0.65 : 1,
      }}>
        {/* Knob */}
        <div style={{
          width: 20, height: 18,
          borderRadius: 3,
          background: on ? "#f5f0e6" : "#b0a898",
          border: `1px solid ${on ? "#ede8dc" : "#8a8070"}`,
          position: "absolute",
          top: 1,
          left: on ? 24 : 1,
          transition: "left .18s, background .18s",
        }}/>
      </div>

      {/* Label */}
      <span style={{
        fontFamily: "'Caveat', cursive",
        fontSize: 14, fontWeight: 600,
        color: "#6b6355",
        letterSpacing: ".02em",
      }}>
        {label}
      </span>
    </div>
  );
}