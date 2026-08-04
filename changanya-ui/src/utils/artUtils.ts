// src/utils/artUtils.ts

/**
 * Generate a deterministic gradient from an artist name.
 * Same artist always gets the same colours.
 */
export function artistGradient(artist: string | null): string {
  const name = artist || "Unknown";
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
    hash |= 0;
  }
  const h1 = Math.abs(hash % 360);
  const h2 = (h1 + 140) % 360;
  return `linear-gradient(135deg, hsl(${h1},35%,25%) 0%, hsl(${h2},30%,18%) 100%)`;
}

/**
 * Convert a local file path to a Tauri v2 asset URL.
 *
 * Tauri v2 uses the convertFileSrc utility from the shell plugin.
 * Falls back to null if path is missing.
 */
export async function artworkUrl(filePath: string | null): Promise<string | null> {
  if (!filePath) return null;

  try {
    const { convertFileSrc } = await import("@tauri-apps/api/core");
    return convertFileSrc(filePath);
  } catch {
    return null;
  }
}