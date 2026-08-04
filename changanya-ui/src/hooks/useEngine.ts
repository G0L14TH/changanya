// src/hooks/useEngine.ts
//
// Custom hook — subscribes to all engine events
// and exposes clean state to components.
// Every component reads from this single source of truth.

import { useEffect, useState, useCallback } from "react";

export interface Track {
  id:           string;
  title:        string;
  artist:       string;
  album:        string;
  year:                  number | null;
  duration_ms:           number;
  artwork_path:          string | null;
  liked:                 boolean;
  shuffleEnabled:      boolean;
  albumMode:           boolean;
  albumShuffleEnabled: boolean;
}

export interface QueueItem {
  id:     string;
  title:  string;
  artist: string;
  score:  number;
  reason: string;
  artwork_path: string | null;
}

export interface EngineState {
  currentTrack: Track | null;
  queue:        QueueItem[];
  isPlaying:    boolean;
  status:       string;
  progressMs:   number;
  homeData:     HomeData | null;
  libraryData:  LibraryData;
  albumSongs:   LibrarySong[];
  shuffleEnabled: boolean;
  albumShuffleEnabled: boolean;
  albumMode:           boolean;
}

export interface HomeSong {
  id:         string;
  title:      string;
  artist:     string;
  album:      string;
  duration_ms:number;
  artwork_path: string | null;
  score?:     number;
}

export interface MoodPlaylist {
  id:       string;
  name:     string;
  count:    number;
  icon:     string;
}

export interface HomeData {
  recently_played: HomeSong[];
  recommended:  HomeSong[];
  favorites:    HomeSong[];
  mood_playlists:  MoodPlaylist[];
}

export interface LibrarySong {
  id:           string;
  title:        string;
  artist:       string;
  album:        string;
  genre:        string;
  year:         number | null;
  duration_ms:  number;
  play_count:   number;
  artwork_path: string | null;
}

export interface LibraryArtist {
  name:         string;
  song_count:   number;
  artwork_path: string | null;
}

export interface LibraryAlbum {
  name:         string;
  artist:       string;
  track_count:  number;
  year:         number | null;
  artwork_path: string | null;
}

export interface LibraryData {
  songs:   LibrarySong[];
  artists: LibraryArtist[];
  albums:  LibraryAlbum[];
}

export function useEngine() {
  const [state, setState] = useState<EngineState>({
    currentTrack: null,
    queue:        [],
    isPlaying:    false,
    status:       "Starting engine...",
    progressMs:   0,
    homeData:     null,
    libraryData:  {
      songs:   [],
      artists: [],
      albums:  [],
    },
    albumSongs:   [],
    shuffleEnabled: true,
    albumShuffleEnabled: false,
    albumMode:           false,
  });

  useEffect(() => {
    let unlistenFn: (() => void) | null = null;
    let progressTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    async function setup() {
      // Wait for Tauri IPC to be fully ready
      // It may not be available immediately on first render
      let retries = 0;
      while (!(window as any).__TAURI_INTERNALS__ && retries < 20) {
        await new Promise(r => setTimeout(r, 100));
        retries++;
      }

      if (cancelled) return;

      try {
        const { listen } = await import("@tauri-apps/api/event");
        const { invoke } = await import("@tauri-apps/api/core");

        // Request state after a short delay
        progressTimer = setTimeout(() => {
          invoke("get_state").catch(console.error);
        }, 2000);

        const unlisten = await listen<string>("engine-event", (event) => {
          if (cancelled) return;

          try {
            const parsed = JSON.parse(event.payload);

            switch (parsed.event) {
              case "ready":
                setState(s => ({ ...s, status: "Engine ready" }));
                invoke("get_state").catch(console.error);
                invoke("get_home_data").catch(console.error);
                break;

              case "now_playing":
                setState(s => ({
                  ...s,
                  currentTrack: parsed.data as Track,
                  isPlaying:    true,
                  status:       "Playing",
                  progressMs:   0,
                }));
                break;

              case "queue_update":
                setState(s => ({
                  ...s,
                  queue: (parsed.data as { upcoming: QueueItem[] }).upcoming,
                }));
                break;

              case "progress":
                setState(s => ({
                  ...s,
                  progressMs: (parsed.data as { ms: number }).ms,
                }));
                break;

              case "paused":
                setState(s => ({ ...s, isPlaying: false, status: "Paused" }));
                break;

              case "resumed":
                setState(s => ({ ...s, isPlaying: true, status: "Playing" }));
                break;
              
              case "home_data":
                setState(s => ({
                  ...s,
                  homeData: parsed.data as HomeData,
                }));
                break;
               
              case "library_songs":
                setState(s => ({
                  ...s,
                  libraryData: {
                    ...s.libraryData,
                    songs: (parsed.data as { songs: LibrarySong[] }).songs,
                  },
                }));
                break;
              case "library_artists":
                setState(s => ({
                  ...s,
                  libraryData: {
                    ...s.libraryData,
                    artists: (parsed.data as { artists: LibraryArtist[] }).artists,
                  },
                }));
                break;

              case "library_albums":
                setState(s => ({
                  ...s,
                  libraryData: {
                    ...s.libraryData,
                    albums: (parsed.data as { albums: LibraryAlbum[] }).albums,
                  },
                }));
                break;  

              case "album_songs":
                setState(s => ({
                  ...s,
                  albumSongs: (parsed.data as { songs: LibrarySong[] }).songs,
                }));
                break;
              case "shuffle_changed":
                setState(s => ({
                  ...s,
                  shuffleEnabled: (parsed.data as { enabled: boolean }).enabled,
                }));
                break;

              case "album_shuffle_changed":
                setState(s => ({
                  ...s,
                  albumShuffleEnabled: (parsed.data as { enabled: boolean }).enabled,
                }));
                break;

              case "album_mode_changed":
                setState(s => ({
                  ...s,
                  albumMode: (parsed.data as { enabled: boolean }).enabled,
                }));
                break;

              case "error":
                console.error("Engine error:", (parsed.data as { message: string }).message);
                break;
            }
          } catch (e) {
            console.error("Failed to parse engine event:", e);
          }
        });

        unlistenFn = unlisten;

      } catch (e) {
        console.error("Failed to set up Tauri listeners:", e);
      }
    }

    setup();

    return () => {
      cancelled = true;
      if (progressTimer) clearTimeout(progressTimer);
      if (unlistenFn) unlistenFn();
    };
  }, []);

  const skip = useCallback(async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("skip");
      setState(s => ({ ...s, isPlaying: false }));
    } catch (e) {
      console.error("skip failed:", e);
    }
  }, []);

  const pauseResume = useCallback(async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("pause_resume");
      setState(s => ({ ...s, isPlaying: !state.isPlaying }));
    } catch (e) {
      console.error("pauseResume failed:", e);
    }
  }, [state.isPlaying]);

  const playSpecific = useCallback(async (songId: string) => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("play_specific", { songId });
    } catch (e) {
      console.error("playSpecific failed:", e);
    }
  }, []);

  const seekTo = useCallback(async(positionMs: number) => {
    try{
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("seek", { positionMs: positionMs });
      // update local state immediately so UI responds instantly
    } catch (e) {
      console.error("seek failed", e);
    }
  }, []);

  const loadHomeData = useCallback(async () => {
    try{
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("get_home_data");
    } catch (e) {
      console.error("loadHomeData failed:", e);
    }
  }, []);

  const loadLibrarySongs = useCallback(async (sortBy = "title") => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("get_library_songs", { sortBy }).catch(console.error);
  }, []);

  const loadLibraryArtists = useCallback(async () => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("get_library_artists").catch(console.error);
  }, []);

  const loadLibraryAlbums = useCallback(async () => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("get_library_albums").catch(console.error);
  }, []);

  const loadAlbumSongs = useCallback(async (album: string, artist: string) => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("get_album_songs", { album, artist }).catch(console.error);
  }, []);

  const playAlbum = useCallback(async (album: string, artist: string, shuffle = false) => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("play_album", { album, artist, shuffle }).catch(console.error);
  }, []);

  const setGlobalShuffle = useCallback(async (enabled: boolean) => {
  const { invoke } = await import("@tauri-apps/api/core");
  invoke("set_global_shuffle", { enabled }).catch(console.error);
}, []);

  const setAlbumShuffle = useCallback(async (enabled: boolean) => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("set_album_shuffle", { enabled }).catch(console.error);
  }, []);
  
  const playAlbumTrack = useCallback(async (
    album: string,
    artist: string,
    songId: string,
  ) => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("play_album_track", { album, artist, songId }).catch(console.error);
  }, []);
 
  const editAlbumTags = useCallback(async (
    album: string,
    artist: string,
    values: { newAlbum?: string; newArtist?: string; genre?: string; year?: string },
  ) => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke("edit_album_tags", {
      album,
      artist,
      newAlbum: values.newAlbum ?? "",
      newArtist: values.newArtist ?? "",
      genre: values.genre ?? "",
      year: values.year ?? "",
    }).catch(console.error);
  }, []);

  return {
    state,
    skip,
    pauseResume,
    playSpecific,
    seekTo,
    loadHomeData,
    loadLibrarySongs,
    loadLibraryArtists,
    loadLibraryAlbums,
    loadAlbumSongs,
    playAlbum,
    setAlbumShuffle,
    setGlobalShuffle,
    playAlbumTrack,
    editAlbumTags,
  };
}