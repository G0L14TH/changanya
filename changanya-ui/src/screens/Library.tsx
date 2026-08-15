import { useEffect, useState } from "react";
import AlbumArt from "../components/AlbumArt";
import {
  LibrarySong, LibraryArtist, LibraryAlbum,
  LibraryData,
} from "../hooks/useEngine";

type Tab    = "songs" | "artists" | "albums";
type SortBy = "title" | "artist" | "album" | "play_count";

interface Props {
  libraryData:      LibraryData;
  albumSongs:       LibrarySong[];
  onLoadSongs:      (sortBy: string) => void;
  onLoadArtists:    () => void;
  onLoadAlbums:     () => void;
  onLoadAlbumSongs: (album: string, artist: string) => void;
  onPlaySong:       (id: string) => void;
  onPlayAlbum:      (album: string, artist: string, shuffle?: boolean) => void;
  onPlayAlbumTrack: (album: string, artist: string, songId: string) => void;
  onEditAlbumTags:  (
    album: string,
    artist: string,
    values: { newAlbum?: string; newArtist?: string; genre?: string; year?: string },
  ) => void;
}

function fmt(ms: number): string {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

function TabBtn({
  label, active, onClick,
}: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontFamily:   "'Caveat', cursive",
        fontSize:     14, fontWeight: 700,
        color:        active ? "#1a1612" : "#6b6355",
        background:   active ? "#faf7f0" : "none",
        border:       active
          ? "1.5px solid #1a1612"
          : "1.5px solid transparent",
        borderRadius: 4, padding: "4px 16px",
        cursor:       "pointer",
        boxShadow:    active ? "2px 2px 0 #1a1612" : "none",
        transition:   "all .12s",
      }}
    >
      {label}
    </button>
  );
}

function SortBtn({
  label, active, onClick,
}: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontFamily:   "'Caveat', cursive",
        fontSize:     12, fontWeight: 600,
        color:        active ? "#1a1612" : "#8a8070",
        background:   "none",
        border:       "none",
        cursor:       "pointer",
        padding:      "2px 8px",
        borderBottom: active
          ? "2px solid #1a1612"
          : "2px solid transparent",
      }}
    >
      {label}
    </button>
  );
}

const actionBtnStyle: React.CSSProperties = {
  border: "1.5px solid #1a1612",
  borderRadius: 4,
  background: "#1a1612",
  color: "#faf7f0",
  cursor: "pointer",
  padding: "6px 12px",
  fontFamily: "'Kalam', cursive",
  fontSize: 12,
};

const secondaryBtnStyle: React.CSSProperties = {
  border: "1.5px solid #1a1612",
  borderRadius: 4,
  background: "#faf7f0",
  color: "#1a1612",
  cursor: "pointer",
  padding: "6px 12px",
  fontFamily: "'Kalam', cursive",
  fontSize: 12,
};

const labelStyle: React.CSSProperties = {
  fontFamily: "'Kalam', cursive",
  fontSize: 11,
  color: "#8a8070",
};

const inputStyle: React.CSSProperties = {
  border: "1.5px solid #b0a898",
  borderRadius: 4,
  padding: "6px 8px",
  background: "#faf7f0",
  fontFamily: "'Kalam', cursive",
  fontSize: 12,
  color: "#1a1612",
};

export default function Library({
  libraryData,
  albumSongs,
  onLoadSongs,
  onLoadArtists,
  onLoadAlbums,
  onLoadAlbumSongs,
  onPlaySong,
  onPlayAlbum,
  onPlayAlbumTrack,
  onEditAlbumTags,
}: Props) {
  const [tab,     setTab]     = useState<Tab>("songs");
  const [sortBy,  setSortBy]  = useState<SortBy>("title");
  const [search,  setSearch]  = useState("");
  const [hovered, setHovered] = useState<string | null>(null);
  const [selectedAlbum, setSelectedAlbum] = useState<LibraryAlbum | null>(null);
  const [editTagsOpen, setEditTagsOpen] = useState(false);
  const [tagForm, setTagForm] = useState({
    album: "",
    artist: "",
    genre: "",
    year: "",
  });

  useEffect(() => {
    if (tab === "songs")   onLoadSongs(sortBy);
    if (tab === "artists") onLoadArtists();
    if (tab === "albums")  onLoadAlbums();
    setSearch("");
  }, [tab]);

  useEffect(() => {
    if (tab === "songs") onLoadSongs(sortBy);
  }, [sortBy]);

  useEffect(() => {
    if (selectedAlbum) {
      setTagForm({
        album: selectedAlbum.name,
        artist: selectedAlbum.artist,
        genre: "",
        year: selectedAlbum.year ? String(selectedAlbum.year) : "",
      });
    }
  }, [selectedAlbum]);

  const invokeAction = async (action: string, args: Record<string, string>) => {
    const { invoke } = await import("@tauri-apps/api/core");
    invoke(action, args).catch(console.error);
  };

  const filterSongs = (songs: LibrarySong[]) => {
    if (!search) return songs;
    const q = search.toLowerCase();
    return songs.filter(s =>
      s.title?.toLowerCase().includes(q)  ||
      s.artist?.toLowerCase().includes(q) ||
      s.album?.toLowerCase().includes(q)
    );
  };

  const filterArtists = (artists: LibraryArtist[]) => {
    if (!search) return artists;
    const q = search.toLowerCase();
    return artists.filter(a => a.name.toLowerCase().includes(q));
  };

  const filterAlbums = (albums: LibraryAlbum[]) => {
    if (!search) return albums;
    const q = search.toLowerCase();
    return albums.filter(a =>
      a.name.toLowerCase().includes(q) ||
      a.artist.toLowerCase().includes(q)
    );
  };

  const openAlbum = (album: LibraryAlbum) => {
    setSelectedAlbum(album);
    setEditTagsOpen(false);
    onLoadAlbumSongs(album.name, album.artist);
  };

  const handlePlayFirstTrack = () => {
    if (!selectedAlbum) return;
    // Start album playback from first track and enqueue all album songs
    onPlayAlbum(selectedAlbum.name, selectedAlbum.artist, false);
  };

  const handleShufflePlay = () => {
    if (!selectedAlbum) return;
    onPlayAlbum(selectedAlbum.name, selectedAlbum.artist, true);
  };
 
  const handlePlayAlbumTrack = (songId: string) => {
    if (!selectedAlbum) return;
    onPlayAlbumTrack(selectedAlbum.name, selectedAlbum.artist, songId);
  };
 
  const handleSaveTags = () => {
    if (!selectedAlbum) return;
    onEditAlbumTags(selectedAlbum.name, selectedAlbum.artist, {
      newAlbum: tagForm.album || selectedAlbum.name,
      newArtist: tagForm.artist || selectedAlbum.artist,
      genre: tagForm.genre || undefined,
      year: tagForm.year || undefined,
    });
    setSelectedAlbum(null);
    setEditTagsOpen(false);
  };

  const rowStyle = (id: string): React.CSSProperties => ({
    display:      "flex",
    alignItems:   "center",
    gap:          10,
    padding:      "6px 12px",
    cursor:       "pointer",
    background:   hovered === id ? "#ede8dc" : "transparent",
    borderBottom: "0.5px solid #e8e3d8",
    transition:   "background .1s",
  });

  return (
    <div style={{
      flex:          1,
      display:       "flex",
      flexDirection: "column",
      overflow:      "hidden",
      position:      "relative",
      background:    "#f5f0e6",
    }}>

      {/* HEADER */}
      <div style={{
        padding:      "14px 20px 0",
        borderBottom: "1.5px solid #b0a898",
        background:   "#ede8dc",
        flexShrink:   0,
      }}>
        {/* Tabs */}
        <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
          <TabBtn
            label="Songs"
            active={tab === "songs"}
            onClick={() => setTab("songs")}
          />
          <TabBtn
            label="Artists"
            active={tab === "artists"}
            onClick={() => setTab("artists")}
          />
          <TabBtn
            label="Albums"
            active={tab === "albums"}
            onClick={() => setTab("albums")}
          />
        </div>

        {/* Search + sort row */}
        <div style={{
          display:       "flex",
          alignItems:    "center",
          gap:           12,
          paddingBottom: 12,
        }}>
          <div style={{
            flex:         1, maxWidth: 320,
            display:      "flex", alignItems: "center", gap: 8,
            background:   "#faf7f0",
            border:       "1.5px solid #1a1612",
            borderRadius: 4, padding: "5px 10px",
            boxShadow:    "2px 2px 0 #1a1612",
          }}>
            <i
              className="ti ti-search"
              style={{ color: "#b0a898", fontSize: 13 }}
              aria-hidden="true"
            />
            <input
              type="text"
              placeholder={`Search ${tab}...`}
              value={search}
              onChange={e => setSearch(e.target.value)}
              aria-label={`Search ${tab}`}
              style={{
                border: "none", background: "none", outline: "none",
                fontFamily: "'Kalam', cursive", fontSize: 13,
                color: "#1a1612", width: "100%",
              }}
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                style={{
                  background: "none", border: "none",
                  cursor: "pointer", color: "#8a8070", fontSize: 14,
                }}
              >
                ×
              </button>
            )}
          </div>

          {tab === "songs" && (
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{
                fontFamily: "'Kalam', cursive",
                fontSize: 11, color: "#8a8070",
              }}>
                Sort:
              </span>
              <SortBtn
                label="Title"
                active={sortBy === "title"}
                onClick={() => setSortBy("title")}
              />
              <SortBtn
                label="Artist"
                active={sortBy === "artist"}
                onClick={() => setSortBy("artist")}
              />
              <SortBtn
                label="Album"
                active={sortBy === "album"}
                onClick={() => setSortBy("album")}
              />
              <SortBtn
                label="Played"
                active={sortBy === "play_count"}
                onClick={() => setSortBy("play_count")}
              />
            </div>
          )}

          <div style={{
            marginLeft: "auto",
            fontFamily: "'Kalam', cursive",
            fontSize:   11, color: "#8a8070",
          }}>
            {tab === "songs"   &&
              `${filterSongs(libraryData.songs).length} songs`}
            {tab === "artists" &&
              `${filterArtists(libraryData.artists).length} artists`}
            {tab === "albums"  &&
              `${filterAlbums(libraryData.albums).length} albums`}
          </div>
        </div>
      </div>

      {/* CONTENT */}
      <div style={{ flex: 1, overflowY: "auto" }}>

        {/* ── SONGS TAB ── */}
        {tab === "songs" && filterSongs(libraryData.songs).map(song => (
          <div
            key={song.id}
            onMouseEnter={() => setHovered(song.id)}
            onMouseLeave={() => setHovered(null)}
            // FIX: row used to fire onPlaySong on a single click, which
            // meant any click anywhere in the row — including misclicks
            // while just browsing — started playback. Play now only
            // triggers from the dedicated hover play-icon button (below)
            // or an explicit double-click on the row.
            onDoubleClick={() => onPlaySong(song.id)}
            style={rowStyle(song.id)}
          >
            <div style={{ width: 36, height: 36, flexShrink: 0 }}>
              <AlbumArt
                artworkPath={song.artwork_path}
                artist={song.artist}
                isPlaying={false}
              />
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontFamily:   "'Caveat', cursive",
                fontSize:     13, fontWeight: 700,
                color:        "#1a1612",
                whiteSpace:   "nowrap", overflow: "hidden",
                textOverflow: "ellipsis",
              }}>
                {song.title}
              </div>
              <div style={{
                fontFamily: "'Kalam', cursive",
                fontSize:   11, color: "#8a8070",
              }}>
                {song.artist}
              </div>
            </div>

            <div style={{
              fontFamily:   "'Kalam', cursive",
              fontSize:     11, color: "#8a8070",
              flexShrink:   0, minWidth: 140,
              whiteSpace:   "nowrap", overflow: "hidden",
              textOverflow: "ellipsis",
            }}>
              {song.album}
            </div>

            <div style={{
              fontFamily: "'Kalam', cursive",
              fontSize:   11, color: "#8a8070",
              flexShrink: 0, width: 36, textAlign: "right",
            }}>
              {fmt(song.duration_ms)}
            </div>

            {hovered === song.id && (
              <button
                onClick={e => { e.stopPropagation(); onPlaySong(song.id); }}
                aria-label="Play"
                style={{
                  width:          28, height: 28,
                  border:         "1.5px solid #1a1612",
                  borderRadius:   4,
                  background:     "#1a1612", color: "#faf7f0",
                  display:        "flex", alignItems: "center",
                  justifyContent: "center",
                  cursor:         "pointer", fontSize: 12,
                  flexShrink:     0,
                }}
              >
                <i className="ti ti-player-play" aria-hidden="true" />
              </button>
            )}
          </div>
        ))}

        {/* ── ARTISTS TAB ── */}
        {tab === "artists" && (
          <div style={{
            display:             "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
            gap:                 12,
            padding:             16,
          }}>
            {filterArtists(libraryData.artists).map(artist => (
              <div
                key={artist.name}
                onClick={() =>
                  invokeAction("get_artist_songs", { artist: artist.name })
                }
                style={{
                  background:   "#faf7f0",
                  border:       "1.5px solid #1a1612",
                  borderRadius: 5,
                  overflow:     "hidden",
                  cursor:       "pointer",
                  boxShadow:    "2px 2px 0 #1a1612",
                  transition:   "all .12s",
                }}
              >
                <AlbumArt
                  artworkPath={artist.artwork_path}
                  artist={artist.name}
                  isPlaying={false}
                />
                <div style={{ padding: "6px 8px" }}>
                  <div style={{
                    fontFamily:   "'Caveat', cursive",
                    fontSize:     13, fontWeight: 700,
                    color:        "#1a1612",
                    whiteSpace:   "nowrap", overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}>
                    {artist.name}
                  </div>
                  <div style={{
                    fontFamily: "'Kalam', cursive",
                    fontSize:   11, color: "#8a8070",
                  }}>
                    {artist.song_count} songs
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── ALBUMS TAB ── */}
        {tab === "albums" && (
          <div style={{
            display:             "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
            gap:                 12,
            padding:             16,
          }}>
            {filterAlbums(libraryData.albums).map(album => (
              <div
                key={`${album.name}-${album.artist}`}
                onClick={() => openAlbum(album)}
                style={{
                  background:   "#faf7f0",
                  border:       "1.5px solid #1a1612",
                  borderRadius: 5,
                  overflow:     "hidden",
                  cursor:       "pointer",
                  boxShadow:    "2px 2px 0 #1a1612",
                  transition:   "all .12s",
                }}
              >
                <AlbumArt
                  artworkPath={album.artwork_path}
                  artist={album.artist}
                  isPlaying={false}
                />
                <div style={{ padding: "6px 8px" }}>
                  <div style={{
                    fontFamily:   "'Caveat', cursive",
                    fontSize:     13, fontWeight: 700,
                    color:        "#1a1612",
                    whiteSpace:   "nowrap", overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}>
                    {album.name}
                  </div>
                  <div style={{
                    fontFamily: "'Kalam', cursive",
                    fontSize:   11, color: "#8a8070",
                  }}>
                    {album.artist}
                  </div>
                  <div style={{
                    fontFamily: "'Kalam', cursive",
                    fontSize:   10, color: "#b0a898",
                  }}>
                    {album.track_count} tracks
                    {album.year ? ` · ${album.year}` : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>

      {selectedAlbum && (
        <div style={{
          position: "absolute",
          inset: 0,
          background: "rgba(26,22,18,0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 24,
          zIndex: 20,
        }} onClick={() => setSelectedAlbum(null)}>
          <div
            onClick={e => e.stopPropagation()}
            style={{
              width: "min(720px, 100%)",
              maxHeight: "80vh",
              overflow: "hidden",
              background: "#faf7f0",
              border: "2px solid #1a1612",
              borderRadius: 8,
              boxShadow: "6px 6px 0 #1a1612",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "14px 16px",
              borderBottom: "1.5px solid #b0a898",
              background: "#ede8dc",
            }}>
              <div>
                <div style={{
                  fontFamily: "'Caveat', cursive",
                  fontSize: 16,
                  fontWeight: 700,
                  color: "#1a1612",
                }}>{selectedAlbum.name}</div>
                <div style={{
                  fontFamily: "'Kalam', cursive",
                  fontSize: 12,
                  color: "#8a8070",
                }}>{selectedAlbum.artist} · {selectedAlbum.track_count} tracks</div>
              </div>
              <button
                onClick={() => setSelectedAlbum(null)}
                style={{
                  border: "1.5px solid #1a1612",
                  borderRadius: 4,
                  background: "#faf7f0",
                  color: "#1a1612",
                  cursor: "pointer",
                  width: 28,
                  height: 28,
                }}
                aria-label="Close album actions"
              >×</button>
            </div>

            <div style={{
              display: "flex",
              gap: 10,
              padding: "12px 16px",
              borderBottom: "1.5px solid #e8e3d8",
            }}>
              <button onClick={handlePlayFirstTrack} aria-label="Play album" style={{
                width: 40, height: 40, borderRadius: 20,
                display: "flex", alignItems: "center", justifyContent: "center",
                border: "1.5px solid #1a1612", background: "#faf7f0", cursor: "pointer"
              }}>
                <i className="ti ti-player-play" aria-hidden="true" style={{ color: "#1a1612" }} />
              </button>

              <button onClick={handleShufflePlay} aria-label="Shuffle album" style={{
                width: 40, height: 40, borderRadius: 20,
                display: "flex", alignItems: "center", justifyContent: "center",
                border: "1.5px solid #1a1612", background: "#faf7f0", cursor: "pointer"
              }}>
                <i className="ti ti-shuffle" aria-hidden="true" style={{ color: "#1a1612" }} />
              </button>

              <button onClick={() => setEditTagsOpen(!editTagsOpen)} aria-label="Edit tags" style={{
                width: 40, height: 40, borderRadius: 20,
                display: "flex", alignItems: "center", justifyContent: "center",
                border: "1.5px solid #1a1612", background: "#faf7f0", cursor: "pointer"
              }}>
                <i className="ti ti-edit" aria-hidden="true" style={{ color: "#1a1612" }} />
              </button>
            </div>

            {editTagsOpen ? (
              <div style={{ padding: 16, display: "grid", gap: 10, borderBottom: "1.5px solid #e8e3d8" }}>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={labelStyle}>Album title</label>
                  <input value={tagForm.album} onChange={e => setTagForm(s => ({...s, album: e.target.value}))} style={inputStyle} />
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={labelStyle}>Artist</label>
                  <input value={tagForm.artist} onChange={e => setTagForm(s => ({...s, artist: e.target.value}))} style={inputStyle} />
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={labelStyle}>Genre</label>
                  <input value={tagForm.genre} onChange={e => setTagForm(s => ({...s, genre: e.target.value}))} style={inputStyle} />
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={labelStyle}>Year</label>
                  <input value={tagForm.year} onChange={e => setTagForm(s => ({...s, year: e.target.value}))} style={inputStyle} />
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={handleSaveTags} style={actionBtnStyle}>Save</button>
                  <button onClick={() => setEditTagsOpen(false)} style={secondaryBtnStyle}>Cancel</button>
                </div>
              </div>
            ) : (
              <div style={{ padding: 16, overflowY: "auto" }}>
                {albumSongs.length === 0 ? (
                  <div style={{ fontFamily: "'Kalam', cursive", color: "#8a8070" }}>No tracks loaded yet.</div>
                ) : (
                  albumSongs.map(song => (
                    <div
                      key={song.id}
                      onMouseEnter={() => setHovered(song.id)}
                      onMouseLeave={() => setHovered(null)}
                      // FIX: same issue as the Songs tab — a single click
                      // anywhere on the row used to start album playback
                      // from that track. Now only the hover play icon
                      // (single click) or an explicit double-click on the
                      // row triggers playback.
                      onDoubleClick={() => handlePlayAlbumTrack(song.id)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: 12,
                        padding: "8px 0",
                        borderBottom: "0.5px solid #e8e3d8",
                        cursor: "pointer",
                        background: hovered === song.id ? "#ede8dc" : "transparent",
                        transition: "background .1s",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                        <div style={{ width: 20, textAlign: "center", color: "#1a1612" }}>
                          {hovered === song.id ? (
                            <i className="ti ti-player-play" aria-hidden="true" />
                          ) : (
                            <span style={{ width: 20, display: "inline-block" }} />
                          )}
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontFamily: "'Caveat', cursive", fontWeight: 700, color: "#1a1612", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {song.title}
                          </div>
                          <div style={{ fontFamily: "'Kalam', cursive", fontSize: 12, color: "#8a8070", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {song.artist}
                          </div>
                        </div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
                        <div style={{ fontFamily: "'Kalam', cursive", fontSize: 11, color: "#8a8070" }}>
                          {fmt(song.duration_ms)}
                        </div>
                        {hovered === song.id && (
                          <button
                            onClick={e => {
                              e.stopPropagation();
                              handlePlayAlbumTrack(song.id);
                            }}
                            aria-label="Play from here"
                            style={{
                              width: 28,
                              height: 28,
                              borderRadius: 6,
                              border: "1.5px solid #1a1612",
                              background: "#faf7f0",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              cursor: "pointer",
                              fontSize: 14,
                            }}
                          >
                            <i className="ti ti-player-play" aria-hidden="true" />
                          </button>
                        )}
                      </div>
                    </div>                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}