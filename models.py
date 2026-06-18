"""
models.py — Data models and local JSON persistence for Karate Manager
"""
 
import json
import uuid
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
 
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "competitions.json")
 
 
@dataclass
class Athlete:
    id: str
    name: str
    dojo: str
    members: list = field(default_factory=list)
 
    def display(self):
        return f"{self.name} ({self.dojo})"
 
 
@dataclass
class MatchResult:
    winner_id: Optional[str] = None          # athlete id
    aka_flags: int = 0
    ao_flags: int = 0
    aka_penalties: int = 0
    ao_penalties: int = 0
    is_draw: bool = False
    disqualified_id: Optional[str] = None
    aka_sub_wins: int = 0
    ao_sub_wins: int = 0
    sub_matches: list = field(default_factory=list)
    current_aka_member: Optional[str] = None
    current_ao_member: Optional[str] = None
 
 
@dataclass
class Match:
    id: str
    round_index: int       # 0 = first round
    match_index: int       # position within round
    aka_id: Optional[str] = None
    ao_id: Optional[str] = None
    result: Optional[MatchResult] = None
    is_bye: bool = False   # auto-advance, no opponent
 
    def is_complete(self):
        return (self.result is not None and self.result.winner_id is not None) or self.is_bye
 
 
@dataclass
class Competition:
    id: str
    name: str
    tatami: str
    category: str
    date: str
    athletes: list = field(default_factory=list)    # list of Athlete dicts
    matches: list = field(default_factory=list)      # list of Match dicts
    rounds: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_team: bool = False
 
    def get_athlete(self, athlete_id: str) -> Optional[Athlete]:
        for a in self.athletes:
            d = a if isinstance(a, dict) else asdict(a)
            if d["id"] == athlete_id:
                return Athlete(
                    id=d["id"],
                    name=d["name"],
                    dojo=d["dojo"],
                    members=d.get("members", [])
                )
        return None
 
    def get_match(self, match_id: str) -> Optional[Match]:
        for m in self.matches:
            d = m if isinstance(m, dict) else asdict(m)
            if d["id"] == match_id:
                result = None
                if d.get("result"):
                    res_dict = d["result"]
                    result = MatchResult(
                        winner_id=res_dict.get("winner_id"),
                        aka_flags=res_dict.get("aka_flags", 0),
                        ao_flags=res_dict.get("ao_flags", 0),
                        aka_penalties=res_dict.get("aka_penalties", 0),
                        ao_penalties=res_dict.get("ao_penalties", 0),
                        is_draw=res_dict.get("is_draw", False),
                        disqualified_id=res_dict.get("disqualified_id"),
                        aka_sub_wins=res_dict.get("aka_sub_wins", 0),
                        ao_sub_wins=res_dict.get("ao_sub_wins", 0),
                        sub_matches=res_dict.get("sub_matches", []),
                        current_aka_member=res_dict.get("current_aka_member"),
                        current_ao_member=res_dict.get("current_ao_member")
                    )
                return Match(
                    id=d["id"],
                    round_index=d["round_index"],
                    match_index=d["match_index"],
                    aka_id=d.get("aka_id"),
                    ao_id=d.get("ao_id"),
                    result=result,
                    is_bye=d.get("is_bye", False)
                )
        return None
 
    def update_match(self, updated: Match):
        for i, m in enumerate(self.matches):
            d = m if isinstance(m, dict) else asdict(m)
            if d["id"] == updated.id:
                self.matches[i] = asdict(updated)
                return
 
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tatami": self.tatami,
            "category": self.category,
            "date": self.date,
            "athletes": [a if isinstance(a, dict) else asdict(a) for a in self.athletes],
            "matches": [m if isinstance(m, dict) else asdict(m) for m in self.matches],
            "rounds": self.rounds,
            "created_at": self.created_at,
            "is_team": self.is_team
        }

    def get_winner_info(self) -> Optional[tuple[str, str]]:
        if self.rounds <= 0:
            return None
        # Find the final match (round_index == self.rounds - 1, match_index == 0)
        for m in self.matches:
            d = m if isinstance(m, dict) else asdict(m)
            if d.get("round_index") == self.rounds - 1 and d.get("match_index") == 0:
                result_dict = d.get("result")
                if result_dict:
                    winner_side = result_dict.get("winner_id")
                    if winner_side == "aka":
                        winner_id = d.get("aka_id")
                    elif winner_side == "ao":
                        winner_id = d.get("ao_id")
                    else:
                        winner_id = None
                    if winner_id:
                        ath = self.get_athlete(winner_id)
                        if ath:
                            return (ath.name, ath.dojo)
        return None
 
 
# ─── Persistence ──────────────────────────────────────────────────────────────
 
def _load_db() -> dict:
    if not os.path.exists(DB_FILE):
        return {"competitions": []}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"competitions": []}
            return data
    except (json.JSONDecodeError, ValueError):
        return {"competitions": []}
 
 
def _save_db(db: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
 
 
def save_competition(comp: Competition):
    db = _load_db()
    existing = [c for c in db["competitions"] if c["id"] != comp.id]
    existing.append(comp.to_dict())
    db["competitions"] = existing
    _save_db(db)
 
 
def load_all_competitions() -> list[Competition]:
    db = _load_db()
    result = []
    for c in db["competitions"]:
        result.append(Competition(
            id=c["id"], name=c["name"], tatami=c["tatami"],
            category=c["category"], date=c["date"],
            athletes=c.get("athletes", []),
            matches=c.get("matches", []),
            rounds=c.get("rounds", 0),
            created_at=c.get("created_at", ""),
            is_team=c.get("is_team", False)
        ))
    return result
 
 
def load_competition(comp_id: str) -> Optional[Competition]:
    for c in load_all_competitions():
        if c.id == comp_id:
            return c
    return None
 
 
def delete_competition(comp_id: str):
    db = _load_db()
    db["competitions"] = [c for c in db["competitions"] if c["id"] != comp_id]
    _save_db(db)
 
 
# ─── Bracket builder ──────────────────────────────────────────────────────────
 
def next_power_of_2(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p
 
 
def build_bracket(athletes: list[Athlete], competition_id: str) -> tuple[list[Match], int]:
    """
    Build an empty single-elimination bracket tree.
    Returns (matches, rounds_count).
    """
    n = len(athletes)
    size = next_power_of_2(n)
    rounds = 0
    tmp = size
    while tmp > 1:
        rounds += 1
        tmp //= 2
 
    matches = []
    # Round 0: first round slots
    slots = size // 2
    for i in range(slots):
        m = Match(
            id=str(uuid.uuid4()),
            round_index=0,
            match_index=i,
        )
        matches.append(m)
 
    # Remaining rounds — empty until winners advance
    current_slots = slots
    for r in range(1, rounds):
        current_slots //= 2
        if current_slots < 1:
            current_slots = 1
        for i in range(current_slots):
            m = Match(
                id=str(uuid.uuid4()),
                round_index=r,
                match_index=i,
            )
            matches.append(m)
 
    return matches, rounds
 
 
def new_competition(name, tatami, category, date, athletes_data: list[dict], is_team: bool = False) -> Competition:
    comp_id = str(uuid.uuid4())
    athletes = [Athlete(id=str(uuid.uuid4()), name=a["name"], dojo=a["dojo"], members=a.get("members", []))
                for a in athletes_data]
    matches, rounds = build_bracket(athletes, comp_id)
    comp = Competition(
        id=comp_id, name=name, tatami=tatami,
        category=category, date=date,
        athletes=[asdict(a) for a in athletes],
        matches=[asdict(m) for m in matches],
        rounds=rounds,
        is_team=is_team
    )
    save_competition(comp)
    return comp
