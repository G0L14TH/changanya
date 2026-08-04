// src/hooks/useKeyboard.ts

import { useEffect } from "react";

interface KeyboardActions {
  onSkip:        () => void;
  onPauseResume: () => void;
  onBack:        () => void;
}

export function useKeyboard({
  onSkip,
  onPauseResume,
  onBack,
}: KeyboardActions) {
  useEffect(() => {
    const handler = async (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (e.target instanceof HTMLInputElement) return;
      if (e.target instanceof HTMLTextAreaElement) return;

      switch (e.key) {
        case " ":
          e.preventDefault();
          onPauseResume();
          break;
        case "n":
        case "N":
          onSkip();
          break;
        case "p":
        case "P":
          onBack();
          break;
        case "ArrowRight": {
          // Seek forward 10 seconds
          e.preventDefault();
          const { invoke } = await import("@tauri-apps/api/core");
          invoke("seek_relative", { deltaMs: 10000 }).catch(console.error);
          break;
        }
        case "ArrowLeft": {
          // Seek back 10 seconds
          e.preventDefault();
          const { invoke } = await import("@tauri-apps/api/core");
          invoke("seek_relative", { deltaMs: -10000 }).catch(console.error);
          break;
        }
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onSkip, onPauseResume, onBack]);
}