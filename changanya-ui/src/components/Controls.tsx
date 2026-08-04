// Controls.tsx — playback control buttons

interface Props {
  isPlaying:      boolean;
  onSkip:         () => void;
  onPauseResume:  () => void;
}

export default function Controls({ isPlaying, onSkip, onPauseResume }: Props) {
  return (
    <div className="flex items-center justify-center gap-4 py-4">

      {/* Pause / Resume */}
      <button
        onClick={onPauseResume}
        className="w-12 h-12 rounded-full bg-white text-black
                   flex items-center justify-center text-lg
                   hover:bg-neutral-200 transition-colors"
      >
        {isPlaying ? "⏸" : "▶"}
      </button>

      {/* Skip */}
      <button
        onClick={onSkip}
        className="w-10 h-10 rounded-full bg-neutral-800
                   flex items-center justify-center text-sm
                   hover:bg-neutral-700 transition-colors"
      >
        ⏭
      </button>

    </div>
  );
}