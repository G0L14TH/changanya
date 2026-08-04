// src/screens/Home.tsx

import { useEffect } from "react";
import SongCard      from "../components/SongCard";
import { HomeSong, HomeData } from "../hooks/useEngine";

interface Props {
  homeData:       HomeData | null;
  onLoadData:     () => void;
  onPlaySong:     (song: HomeSong) => void;
  onOpenNowPlaying: () => void;
}

const moodColours: Record<string, string> = {
  heart:       "#7a1a1a",
  moon:        "#2d1b69",
  microphone:  "#1a1a2e",
  stars:       "#1a2a4a",
  coffee:      "#3a2010",
  bolt:        "#4a3a00",
  sun:         "#4a2000",
  headphones:  "#0a2a2a",
  wave:        "#0a2a1a",
  clock:       "#2a2a2a",
};

function SectionHeader({
  title, subtitle, actions,
}: {
  title:    string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div style={{
      display:        "flex",
      alignItems:     "baseline",
      justifyContent: "space-between",
      marginBottom:   14,
    }}>
      <div>
        <span style={{
          fontFamily: "'Caveat', cursive",
          fontSize:   20, fontWeight: 700,
          color:      "#1a1612",
        }}>
          {title}
        </span>
        {subtitle && (
          <span style={{
            fontFamily: "'Kalam', cursive",
            fontSize:   11, color: "#8a8070",
            marginLeft: 12,
          }}>
            {subtitle}
          </span>
        )}
      </div>
      {actions}
    </div>
  );
}

function SecBtn({ label, onClick }: { label: string; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontFamily:   "'Caveat', cursive",
        fontSize:     12, fontWeight: 700,
        color:        "#1a1612", background: "#faf7f0",
        border:       "1.5px solid #1a1612",
        borderRadius: 3, padding: "3px 12px",
        cursor:       "pointer",
        boxShadow:    "2px 2px 0 #1a1612",
      }}
    >
      {label}
    </button>
  );
}

export default function Home({
  homeData, onLoadData, onPlaySong, onOpenNowPlaying,
}: Props) {

  useEffect(() => {
    onLoadData();

    const retry = setTimeout(() => {
      onLoadData();
    }, 3000);

    return () => clearTimeout(retry);
  }, []);

  const recently = homeData?.recently_played ?? [];
  const recommended = homeData?.recommended ?? [];
  const moods = homeData?.mood_playlists ?? [];
  const favourites = homeData?.favorites ?? [];

  return (
    <div style={{
      flex:       1,
      overflowY:  "auto",
      padding:    "22px 24px 0",
      background: "#f5f0e6",
    }}>

      {/*NOW PLAYING BUTTON - top left*/}
        <div style={{ display: "flex", justifyContent: "flext-end", marginBottom: 16}}>
            <button
                onClick={onOpenNowPlaying}
                style={{
                    fontFamily:     "'Caveat', cursive",
                    fontSize:       12, fontWeight: 700,
                    color:          "#1a1612", background: "#faf7f0",
                    border:         "1.5px solid #1a1612",
                    borderRadius:   3, padding: "3px 12px",
                    cursor:         "pointer",
                    boxShadow:       "2px 2px 0 #1a1612",
                }}
            >
                Now Playing 
            </button>
        </div>
      {/* ── RECENTLY PLAYED ── */}
      <section style={{ marginBottom: 28 }}>
        <SectionHeader
          title="Recently Played"
          actions={
            <div style={{ display: "flex", gap: 6 }}>
              <SecBtn label="View All" />
              <SecBtn label="Shuffle" />
            </div>
          }
        />
        {recently.length === 0 ? (
          <div style={{
            fontFamily: "'Kalam', cursive",
            fontSize:   13, color: "#8a8070",
            padding:    "20px 0",
          }}>
            Start listening — your recent songs will appear here
          </div>
        ) : (
          <div style={{
            display:             "grid",
            gridTemplateColumns: `1fr ${recently.slice(1).map(() => "0.65fr").join(" ")}`,
            gap:                 10,
          }}>
            {recently[0] && (
              <SongCard
                song={recently[0]}
                featured={true}
                onClick={onPlaySong}
              />
            )}
            {recently.slice(1, 4).map(song => (
              <SongCard
                key={song.id}
                song={song}
                featured={false}
                onClick={onPlaySong}
              />
            ))}
          </div>
        )}
      </section>

      {/* ── MOOD PLAYLISTS ── */}
      {moods.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <SectionHeader
            title="Tonight's Mood"
            subtitle="AI-generated session playlists"
          />
          <div style={{ display: "flex", gap: 10, overflowX: "auto", paddingBottom: 4 }}>
            {moods.map(mood => (
              <div
                key={mood.id}
                style={{
                  flexShrink:   0,
                  width:        140,
                  background:   "#faf7f0",
                  border:       "1.5px solid #1a1612",
                  borderRadius: 5,
                  padding:      "10px 12px",
                  cursor:       "pointer",
                  boxShadow:    "2px 2px 0 #1a1612",
                }}
              >
                <div style={{
                  width:        8, height: 8,
                  borderRadius: "50%",
                  background:   moodColours[mood.icon] ?? "#1a1612",
                  marginBottom: 8,
                }} />
                <div style={{
                  fontFamily: "'Caveat', cursive",
                  fontSize:   14, fontWeight: 700,
                  color:      "#1a1612", marginBottom: 3,
                }}>
                  {mood.name}
                </div>
                <div style={{
                  fontFamily: "'Kalam', cursive",
                  fontSize:   11, color: "#8a8070",
                }}>
                  {mood.count} songs
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── RECOMMENDED ── */}
      {recommended.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <SectionHeader
            title="Recommended for You"
            subtitle="Curated picks based on listening habits"
          />
          <div style={{
            display:             "grid",
            gridTemplateColumns: `0.9fr ${recommended.slice(1).map(() => "0.65fr").join(" ")}`,
            gap:                 10,
          }}>
            {recommended[0] && (
              <SongCard
                song={recommended[0]}
                featured={true}
                onClick={onPlaySong}
              />
            )}
            {recommended.slice(1).map(song => (
              <SongCard
                key={song.id}
                song={song}
                featured={false}
                onClick={onPlaySong}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── PLAYLISTS ── */}
      <section style={{ marginBottom: 28 }}>
        <SectionHeader
          title="Your Playlists"
          subtitle="Manage and play your saved collections"
        />
        <div style={{
          display:             "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap:                 12,
        }}>

          {/* Favorites playlist */}
          <div style={{
            background:   "#faf7f0",
            border:       "1.5px solid #1a1612",
            borderRadius: 5,
            overflow:     "hidden",
            boxShadow:    "2px 2px 0 #1a1612",
          }}>
            <div style={{
              display:         "flex",
              alignItems:      "center",
              gap:             10,
              padding:         "10px 12px",
              borderBottom:    "1px solid #b0a898",
              background:      "#ede8dc",
            }}>
              <div style={{
                width:          36, height: 36,
                background:     "#ddd7cc",
                border:         "1px solid #b0a898",
                borderRadius:   4,
                display:        "flex",
                alignItems:     "center",
                justifyContent: "center",
                fontSize:       16, color: "#8a8070",
              }}>
                <i className="ti ti-heart" aria-hidden="true" />
              </div>
              <div>
                <div style={{
                  fontFamily: "'Caveat', cursive",
                  fontSize:   14, fontWeight: 700, color: "#1a1612",
                }}>
                  Favorites
                </div>
                <div style={{
                  fontFamily: "'Kalam', cursive",
                  fontSize:   10, color: "#8a8070",
                }}>
                  {favourites.length} tracks
                </div>
              </div>
            </div>
            <div>
              {favourites.slice(0, 3).map(song => (
                <div
                  key={song.id}
                  style={{
                    display:    "flex",
                    alignItems: "center",
                    gap:        8,
                    padding:    "5px 10px",
                    cursor:     "pointer",
                  }}
                >
                  <div style={{
                    width:          26, height: 26,
                    background:     "#ddd7cc",
                    border:         "1px solid #b0a898",
                    borderRadius:   3,
                    display:        "flex",
                    alignItems:     "center",
                    justifyContent: "center",
                    fontSize:       10, color: "#b0a898",
                  }}>
                    <i className="ti ti-music" aria-hidden="true" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontFamily:   "'Caveat', cursive",
                      fontSize:     12, fontWeight: 600,
                      color:        "#1a1612",
                      whiteSpace:   "nowrap", overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}>
                      {song.title || "Unknown"}
                    </div>
                    <div style={{
                      fontFamily: "'Kalam', cursive",
                      fontSize:   10, color: "#8a8070",
                    }}>
                      {song.artist || "Unknown"}
                    </div>
                  </div>
                  <div style={{
                    fontFamily: "'Kalam', cursive",
                    fontSize:   10, color: "#8a8070",
                    flexShrink: 0,
                  }}>
                    {song.duration_ms
                      ? `${Math.floor(song.duration_ms / 60000)}:${String(
                          Math.floor((song.duration_ms % 60000) / 1000)
                        ).padStart(2, "0")}`
                      : "—"}
                  </div>
                </div>
              ))}
              {favourites.length === 0 && (
                <div style={{
                  fontFamily: "'Kalam', cursive",
                  fontSize:   12, color: "#8a8070",
                  padding:    "10px 12px",
                }}>
                  Like songs to add them here
                </div>
              )}
            </div>
          </div>

        </div>
      </section>

      <div style={{ height: 16 }} />
    </div>
  );
}