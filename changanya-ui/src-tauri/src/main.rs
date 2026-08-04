// src-tauri/src/main.rs
//
// Tauri backend: launches the Python engine as a
// child process and bridges commands/events between
// the React frontend and the Python intelligence layer.
//
// This file is intentionally thin. All intelligence
// lives in Python. Rust just connects the pieces.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::{Path, PathBuf};
use std::io::{BufRead, BufReader, Read, Write};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use tauri::{AppHandle, Emitter, Manager, State};

// Shared state — the Python process and its stdin handle
// wrapped in Arc<Mutex<>> so multiple threads can access safely
struct EngineState {
    child: Option<Child>,
    stdin: Option<ChildStdin>,
}

type SharedEngine = Arc<Mutex<EngineState>>;

// Tauri commands: called from React via invoke() 

#[tauri::command]
fn send_command(
    command: String,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;

    if let Some(stdin) = engine.stdin.as_mut() {
        let line = format!("{}\n", command);
        stdin
            .write_all(line.as_bytes())
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn skip(state: State<SharedEngine>) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        stdin
            .write_all(b"{\"action\": \"skip\"}\n")
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn pause_resume(state: State<SharedEngine>) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        stdin
            .write_all(b"{\"action\": \"pause_resume\"}\n")
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn play_specific(
    song_id: String,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!("{{\"action\": \"play_specific\", \"song_id\": \"{}\"}}\n", song_id);
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn back(state: State<SharedEngine>) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        stdin
            .write_all(b"{\"action\": \"back\"}\n")
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_state(state: State<SharedEngine>) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        stdin
            .write_all(b"{\"action\": \"get_state\"}\n")
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn seek(
    position_ms: i64,
    state: State<SharedEngine>,
) -> Result<(), String>{
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut(){
        let cmd = format!(
            "{{\"action\": \"seek\", \"position_ms\": {}}}\n",
            position_ms
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn set_volume(
    volume: i64,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"set_volume\", \"volume\": {}}}\n",
            volume
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn like_song(
    song_id: String,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"like_song\", \"song_id\": \"{}\"}}\n",
            song_id
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn seek_relative(
    delta_ms: i64,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"seek_relative\", \"delta_ms\": {}}}\n",
            delta_ms
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_home_data(state: State<SharedEngine>) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        stdin
            .write_all(b"{\"action\": \"get_home_data\"}\n")
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_library_songs(
    sort_by: String,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"get_library_songs\", \"sort_by\": \"{}\"}}\n",
            sort_by
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_library_artists(state: State<SharedEngine>) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        stdin.write_all(b"{\"action\": \"get_library_artists\"}\n")
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_library_albums(state: State<SharedEngine>) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        stdin.write_all(b"{\"action\": \"get_library_albums\"}\n")
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_artist_songs(
    artist: String,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"get_artist_songs\", \"artist\": \"{}\"}}\n",
            artist.replace('"', "\\\"")
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_album_songs(
    album:  String,
    artist: String,
    state:  State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"get_album_songs\", \"album\": \"{}\", \"artist\": \"{}\"}}\n",
            album.replace('"', "\\\""),
            artist.replace('"', "\\\"")
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn play_album(
    album: String,
    artist: String,
    shuffle: bool,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"play_album\", \"album\": \"{}\", \"artist\": \"{}\", \"shuffle\": {}}}\n",
            album.replace('"', "\\\""),
            artist.replace('"', "\\\""),
            if shuffle { "true" } else { "false" }
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn set_global_shuffle(
    enabled: bool,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"set_shuffle\", \"enabled\": {}}}\n",
            if enabled { "true" } else { "false" }
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn set_album_shuffle(
    enabled: bool,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"set_album_shuffle\", \"enabled\": {}}}\n",
            if enabled { "true" } else { "false" }
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn play_album_track(
    album: String,
    artist: String,
    song_id: String,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"play_album_track\", \"album\": \"{}\", \"artist\": \"{}\", \"song_id\": \"{}\"}}\n",
            album.replace('"', "\\\""),
            artist.replace('"', "\\\""),
            song_id.replace('"', "\\\""),
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn edit_album_tags(
    album: String,
    artist: String,
    new_album: String,
    new_artist: String,
    genre: String,
    year: String,
    state: State<SharedEngine>,
) -> Result<(), String> {
    let mut engine = state.lock().map_err(|e| e.to_string())?;
    if let Some(stdin) = engine.stdin.as_mut() {
        let cmd = format!(
            "{{\"action\": \"edit_album_tags\", \"album\": \"{}\", \"artist\": \"{}\", \"new_album\": \"{}\", \"new_artist\": \"{}\", \"genre\": \"{}\", \"year\": \"{}\"}}\n",
            album.replace('"', "\\\""),
            artist.replace('"', "\\\""),
            new_album.replace('"', "\\\""),
            new_artist.replace('"', "\\\""),
            genre.replace('"', "\\\""),
            year.replace('"', "\\\"")
        );
        stdin.write_all(cmd.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}

// ──────────────────── Engine launcher ─────────────────────────

fn find_project_root() -> PathBuf {
    // In development: project root is two levels above src-tauri/
    // In production:  we'll bundle ipc.py alongside the binary
    let exe = std::env::current_exe()
        .expect("Cannot find executable path");

    // Development mode — climb up from target/debug/ to project root
    // exe: changanya-ui/src-tauri/target/debug/changanya-ui.exe
    // root: changanya/ (4 levels up)
    if let Some(p) = exe.ancestors().nth(5) {
        return p.to_path_buf();
    }

    // Fallback: current working directory
    std::env::current_dir().unwrap()
}

fn find_python(project_root: &Path) -> PathBuf {
    // Look for the venv Python in platform-specific locations
    if cfg!(target_os = "windows") {
        let p = project_root.join(".venv").join("Scripts").join("python.exe");
        if p.exists() { return p; }
    } else {
        // macOS and Linux both use bin/python3
        let p = project_root.join(".venv").join("bin").join("python3");
        if p.exists() { return p; }
        let p = project_root.join(".venv").join("bin").join("python");
        if p.exists() { return p; }
    }

    // Fallback: system Python
    if cfg!(target_os = "windows") {
        PathBuf::from("python.exe")
    } else {
        PathBuf::from("python3")
    }
}

fn find_vlc_path() -> Option<PathBuf> {
    if cfg!(target_os = "windows") {
        let p = PathBuf::from(r"C:\Program Files\VideoLAN\VLC");
        if p.exists() { return Some(p); }
        let p = PathBuf::from(r"C:\Program Files (x86)\VideoLAN\VLC");
        if p.exists() { return Some(p); }
    } else if cfg!(target_os = "macos") {
        let p = PathBuf::from("/Applications/VLC.app/Contents/MacOS/lib");
        if p.exists() { return Some(p); }
    }
    // Linux: VLC is on system PATH via package manager — no path needed
    None
}

fn launch_python_engine(app: AppHandle, state: SharedEngine) {
    let project_root = find_project_root();
    let python       = find_python(&project_root);
    let script       = project_root.join("ipc.py");

    println!("[tauri] Project root: {}", project_root.display());
    println!("[tauri] Python:       {}", python.display());
    println!("[tauri] Script:       {}", script.display());

    if !script.exists() {
        eprintln!("[tauri] ERROR: ipc.py not found at {}", script.display());
        return;
    }

    let mut cmd = Command::new(&python);
    cmd.arg(&script)
       .stdin(Stdio::piped())
       .stdout(Stdio::piped())
       .stderr(Stdio::inherit());

    // Set VLC path as environment variable for Python to pick up
    if let Some(vlc_path) = find_vlc_path() {
        cmd.env("VLC_PLUGIN_PATH", &vlc_path);
        cmd.env("CHANGANYA_VLC_PATH", vlc_path.to_str().unwrap_or(""));
    }

    let mut child = cmd.spawn()
        .unwrap_or_else(|e| panic!("Failed to launch Python: {}", e));

    let stdout = child.stdout.take()
        .expect("Failed to capture stdout");
    let stdin = child.stdin.take()
        .expect("Failed to capture stdin");

    {
        let mut engine = state.lock().unwrap();
        engine.stdin = Some(stdin);
        engine.child = Some(child);
    }

    thread::spawn(move || {
        let mut reader = BufReader::new(stdout);
        let mut line   = Vec::new();

        loop {
            line.clear();
            match reader.read_until(b'\n', &mut line) {
                Ok(0) => break,
                Ok(_) => {
                    let json = String::from_utf8_lossy(&line).trim().to_string();
                    if !json.is_empty() {
                        if let Err(e) = app.emit("engine-event", &json) {
                            eprintln!("[tauri] Emit error: {}", e);
                        }
                    }
                }
                Err(e) => {
                    eprintln!("[tauri] Read error: {}", e);
                }
            }
        }
    });
}

// ────────────────── Main entry point ────────────────────

fn main() {
    let engine_state: SharedEngine = Arc::new(Mutex::new(EngineState {
        child: None,
        stdin: None,
    }));

    let state_for_launch = engine_state.clone();

    tauri::Builder::default()
        .manage(engine_state)
        .invoke_handler(tauri::generate_handler![
            send_command,
            skip,
            pause_resume,
            get_state,
            play_specific,
            back,
            seek,
            set_volume,
            like_song,
            get_home_data,
            get_library_songs,
            get_library_artists,
            get_library_albums,
            get_artist_songs,
            get_album_songs,
            play_album,
            set_global_shuffle,
            set_album_shuffle,
            play_album_track,
            edit_album_tags,
        ])
        .setup(move |app| {
            let app_handle = app.handle().clone();
            // Launch Python engine after Tauri window is ready
            thread::spawn(move || {
                launch_python_engine(app_handle, state_for_launch);
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}