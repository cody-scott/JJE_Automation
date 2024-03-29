# generated by datamodel-codegen:
#   filename:  data.json
#   timestamp: 2022-01-24T21:18:19+00:00

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field


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


class SelectedPosition(BaseModel):
    coverage_type: str
    date: str
    position: str
    is_flex: str


class PlayerItem(BaseModel):
    player_key: str
    player_id: str
    name: Name
    editorial_player_key: str
    editorial_team_key: str
    editorial_team_full_name: str
    editorial_team_abbr: str
    uniform_number: str
    display_position: str
    headshot: Headshot
    image_url: str
    is_undroppable: str
    position_type: str
    primary_position: str
    eligible_positions: EligiblePositions
    has_player_notes: Optional[str] = None
    player_notes_last_timestamp: Optional[str] = None
    selected_position: SelectedPosition
    is_editable: Optional[str] = 'false'
    status: Optional[str] = None
    status_full: Optional[str] = None
    injury_note: Optional[str] = None
    on_disabled_list: Optional[str] = None
    has_recent_player_notes: Optional[str] = None


class Players(BaseModel):
    _count: str = Field(..., alias='@count')
    player: List[PlayerItem]


class RosterModel(BaseModel):
    coverage_type: str
    date: str
    is_editable: str
    players: Players
