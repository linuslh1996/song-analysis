from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
import requests
import difflib

import billboard
import lyricsgenius
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class SongInfo(object):
    artist: str
    title: str
    peak: int
    weeks: int
    start_date: datetime

@dataclass_json
@dataclass
class SongInfos:
    all_songs: Dict[str, SongInfo]

    @staticmethod
    def get_file_path() -> Path:
        return Path("songs_to_get_lyrics_for.json")

    @staticmethod
    def load(chart_file: Path) -> Dict[str, SongInfo]:
        songs_container: SongInfos = SongInfos.from_dict(json.load(chart_file.open()))
        return songs_container.all_songs

    def save(self, chart_file: Path):
        with chart_file.open("w+") as file:
            file.write(self.to_json(indent=4))

@dataclass_json
@dataclass
class SongLyric:
    song_info: SongInfo
    lyric: Optional[str]

@dataclass_json
@dataclass
class SongLyrics:
    all_lyrics: List[SongLyric]

    @staticmethod
    def get_file_path() -> Path:
        return Path("songs_with_lyrics.json")

    @staticmethod
    def load(file: Path) -> List[SongLyric]:
        all_lyrics: SongLyrics = SongLyrics.from_dict(json.load(file.open()))
        return all_lyrics.all_lyrics

    def save(self, file: Path):
        with file.open("w+") as file:
            file.write(self.to_json(indent=4))


def query_songs_from_billboard() -> Dict[str, SongInfo]:
    # Start To Search For All Songs Starting From 2000
    start_date: datetime = datetime(year=2000, month=1, day=1)
    current_date: datetime = start_date
    all_songs: Dict[str, SongInfo] = {}

    # For Every Two Months, Query the Charts and add all top 100 songs. If the song is already stored in the list, update its values.
    while current_date < datetime.now():
        chart_date: str = current_date.strftime("%Y-%m-%d")
        data: billboard.ChartData = billboard.ChartData("hot-100", date=chart_date)
        song: billboard.ChartEntry
        for song in data.entries[:100]:
            key: str = str(song)
            if key in list(all_songs.keys()):
                all_songs[key].weeks = song.weeks
                all_songs[key].peak = song.peakPos
            else:
                all_songs[key] = SongInfo(artist=song.artist, title=song.title, weeks=song.weeks, peak=song.peakPos,
                                          start_date=start_date)
        current_date += timedelta(days=60)

    # Filter: We only want to look at the popular songs.
    only_with_top_20_peak: Dict[str, SongInfo] = {key: value for key, value in all_songs.items() if value.peak < 20}
    only_with_16_weeks_running: Dict[str, SongInfo] = {key: value for key, value in only_with_top_20_peak.items() if
                                                        value.weeks > 16}
    return only_with_16_weeks_running

def get_lyrics_of_song(song: SongInfo, token: str) -> Optional[str]:
    url: Optional[str] = get_genius_url_of_song(song, token)
    if not url:
        return None
    return get_lyrics_from_url(url, token)


def get_genius_url_of_song(song: SongInfo, token: str) -> Optional[str]:
    # Search For the Song in Genius
    search_url: str = "http://api.genius.com/search"
    song_stringified: str = f"{song.title} by {song.artist}"
    parameters: Dict[str, str] = {"q": f"{song_stringified}"}
    headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
    search_results: List = requests.get(search_url, params=parameters, headers=headers).json()["response"]["hits"]

    # Since Geniuses Result Order is not very good, find the fitting result by ourselves
    results_stringified: List[str] = [f"{hit['result']['title']} by {hit['result']['primary_artist']['name']}"
                                    for hit in search_results]
    matches: List[str] = difflib.get_close_matches(song_stringified, results_stringified, n=1)
    if len(matches) == 0:
        return None
    closest_genius_result: str = matches[0]

    # Return API Path of this result
    index_of_closes_genius_result: int = results_stringified.index(closest_genius_result)
    best_result = search_results[index_of_closes_genius_result]
    return best_result["result"]["url"]


def get_lyrics_from_url(url: str, token: str) -> str:
    genius: lyricsgenius.Genius = lyricsgenius.Genius(token)
    song_lyrics: str = genius._scrape_song_lyrics_from_url(url)
    return song_lyrics


token: str = os.environ["GENIUS_TOKEN"]
all_songs: List[SongInfo] = list(SongInfos.load(SongInfos.get_file_path()).values())
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(lambda song: get_lyrics_of_song(song, token), all_songs))
songs_with_lyrics = [SongLyric(info, results[i]) for i,info in enumerate(all_songs)]
SongLyrics(songs_with_lyrics).save(SongLyrics.get_file_path())
