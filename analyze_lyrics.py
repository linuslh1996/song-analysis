from typing import List, Dict, Optional
import logging
from query_lyrics import SongLyric, SongLyricsStorage

CHORUS_KEYS: List[str] = ["Hook", "Chorus"]


def find_all(string: str, substring: str) -> List[int]:
    start = 0
    indizes: List[int] = []
    while start != -1:
        substring_index = string.find(substring, start)
        if substring_index == -1:
            break
        indizes.append(substring_index)
        start = substring_index + 1
    return indizes

def get_lyrics_split_up_in_parts(song_lyric: str) -> Dict[str, str]:
    without_intro = song_lyric[song_lyric.find("["):]
    all_song_parts = without_intro.split("[")
    parts: Dict[str, str] = {}
    for song_part in all_song_parts:
        if song_part == "":
            continue
        song_part, lyrics = tuple(song_part.split("]"))
        if song_part not in parts.keys():
            parts[song_part] = lyrics
    return parts

def get_hook_lyrics(parts: Dict[str,str]) -> Optional[str]:
    try:
        hook_lyrics = [lyric for part,lyric in parts.items() if any([key in part for key in CHORUS_KEYS]) and not "Pre-Chorus" in part][0]
        return hook_lyrics
    except Exception:
        logging.exception("Something wrong, we just skip this")
        return None

def load_songs() -> List[SongLyric]:
    all_songs: List[SongLyric] = SongLyricsStorage.load()
    only_songs_with_lyrics = [song for song in all_songs if song.lyric is not None and song.lyric != ""]
    songs_with_relevant_tags: List[SongLyric] = [song for song in only_songs_with_lyrics
                                                 if any([key in song.lyric for key in CHORUS_KEYS])
                                                 and "[" in song.lyric]
    return songs_with_relevant_tags


