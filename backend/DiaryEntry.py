import os
import json
import yt_dlp

def get_user_diary_path(username):
    os.makedirs("database", exist_ok=True)
    safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-')).lower()
    return f"database/diary_{safe_username}.txt"

def fetch_song_title(url):
    """Automatically extracts the song/video title using yt-dlp without downloading."""
    ydl_opts = {'extract_flat': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', url)
    except Exception:
        return url

def get_audio_stream_url(youtube_url):
    """Extracts the direct streaming audio URL using yt-dlp for in-app VLC playback."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url', None)
    except Exception as e:
        print("Stream Extraction Error:", e)
        return None

def load_entries(username):
    path = get_user_diary_path(username)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_entry(username, title, url, description, artist="Unknown", album="Unknown", date="Oct 10, 2026"):
    path = get_user_diary_path(username)
    data = load_entries(username)
    
    new_entry = {
        "title": title,
        "url": url,
        "description": description,
        "artist": artist,
        "album": album,
        "date": date
    }
    
    data.insert(0, new_entry)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def delete_entry(username, url_to_delete):
    path = get_user_diary_path(username)
    data = load_entries(username)
    updated_data = [entry for entry in data if entry["url"] != url_to_delete]
    
    with open(path, "w") as f:
        json.dump(updated_data, f, indent=4)