import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
import json
import os

import billboard
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
class Container:
    all_songs: Dict[str, SongInfo]

def get_file_path() -> Path:
    return Path("filtered.json")

def save_data(all_songs: Dict[str, SongInfo], chart_file: Path):
    with chart_file.open("w+") as file:
        file.write((Container(all_songs).to_json(indent=4)))

def load_data(chart_file: Path) -> Dict[str, SongInfo]:
    chart_file = get_file_path()
    songs_container: Container = Container.from_dict(json.load(chart_file.open()))
    return songs_container.all_songs

def query_songs_from_billboard() -> Dict[str, SongInfo]:
    start_date: datetime = datetime(year=2000, month=1, day=1)
    current_date: datetime = start_date
    all_songs: Dict[str, SongInfo] = {}
    while current_date < datetime.now():
        print(current_date)
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
    only_with_top_50_peak: Dict[str, SongInfo] = {key: value for key, value in all_songs.items() if value.peak < 50}
    only_with_ten_weeks_running: Dict[str, SongInfo] = {key: value for key, value in only_with_top_50_peak.items() if
                                                        value.weeks > 10}
    return only_with_ten_weeks_running


token: str = os.environ["GENIUS_TOKEN"]
FILE_PATH: Path = get_file_path()
all_songs: Dict[str, SongInfo] = load_data(FILE_PATH)
only_with_top_20_peak = {key:value for key,value in all_songs.items() if value.peak < 20}
only_with_more_than_16_weeks = {key:value for key,value in only_with_top_20_peak.items() if value.weeks > 16}


save_data(only_with_more_than_16_weeks, Path("filtered.json"))
