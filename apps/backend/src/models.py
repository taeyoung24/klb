from typing import Optional
from sqlmodel import SQLModel, Field, JSON

class League(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str

class Club(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    league_id: int = Field(foreign_key="league.id")

class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    club_id: int = Field(foreign_key="club.id")
    personality: list[int] = Field(sa_type=JSON)
    speed: int        = Field(ge=1, le=1000)
    control: int      = Field(ge=1, le=1000)
    power: int        = Field(ge=1, le=1000)
    flexibility: int  = Field(ge=1, le=1000)
    focus: int        = Field(ge=1, le=1000)
    