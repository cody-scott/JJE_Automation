# generated by datamodel-codegen:
#   filename:  player_data.json
#   timestamp: 2022-01-23T20:31:15+00:00

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel


class Name(BaseModel):
    full: str
    first: str
    last: str
    ascii_first: str
    ascii_last: str


class Headshot(BaseModel):
    url: str
    size: str


class EligiblePositions(BaseModel):
    position: Union[str, List[str]]


class StatItem(BaseModel):
    stat_id: str
    value: str


class Stats(BaseModel):
    stat: List[StatItem]


class PlayerStats(BaseModel):
    coverage_type: str
    season: str
    stats: Stats

class PlayerAdvancedStats(BaseModel):
    coverage_type: str
    season: str
    stats: Stats


class PlayerModel(BaseModel):
    player_key: str
    player_id: str
    name: Name
    editorial_player_key: str
    editorial_team_key: str
    editorial_team_full_name: str
    editorial_team_abbr: str
    uniform_number: Optional[str] = None
    display_position: Optional[str] = None
    headshot: Optional[Headshot]
    image_url: str
    is_undroppable: str
    position_type: str
    primary_position: str
    eligible_positions: EligiblePositions
    has_player_notes: Optional[str] = None
    player_notes_last_timestamp: Optional[str] = None
    player_stats: PlayerStats
    player_advanced_stats: Optional[PlayerAdvancedStats] = None
    has_recent_player_notes: Optional[str] = None
    status: Optional[str] = None
    status_full: Optional[str] = None
    injury_note: Optional[str] = None
    on_disabled_list: Optional[str] = None


class PlayersModel(BaseModel):
    __root__: List[PlayerModel]
