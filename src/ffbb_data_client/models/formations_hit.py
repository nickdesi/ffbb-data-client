from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ..utils.converter_utils import (
    from_datetime,
    from_duration,
    from_int,
    from_list,
    from_str,
    from_uuid,
    to_dict_set,
)
from .formation_session import FormationSession
from .hit import Hit


@dataclass
class FormationsHit(Hit):
    id: str | None = None
    title: str | None = None
    type: str | None = None
    mode: str | None = None
    domain: str | None = None
    theme: str | None = None
    description: str | None = None
    goals: str | None = None
    public: str | None = None
    prerequisites: str | None = None
    content: str | None = None
    pedagogy: str | None = None
    certification: str | None = None
    results: str | None = None
    modalities: str | None = None
    level: str | None = None
    reference: str | None = None
    program_id_fbi: str | None = None
    duration_hours: timedelta | None = None
    sessions: list[FormationSession] | None = None
    files: list[Any] | None = None
    image: str | None = None
    thumbnail: str | None = None
    mode_hidden: str | None = None
    postal_codes: list[str] | None = None
    places: list[str] | None = None
    id_origin_hash: str | None = None
    date_end: datetime | None = None
    date_end_formatted: int | None = None
    date_start: datetime | None = None
    date_start_formatted: int | None = None
    entity: str | None = None
    formation_domain: str | None = None
    formation_duration_hours: str | None = None
    formation_id: UUID | None = None
    formation_image: str | None = None
    formation_mode: str | None = None
    formation_theme: str | None = None
    formation_thumbnail: str | None = None
    formation_title: str | None = None
    place: str | None = None
    postal_code: str | None = None
    reference_hidden: str | None = None
    subscribe_btn: str | None = None
    subscribe_button: str | None = None

    lower_title: str | None = field(init=False, default=None, repr=False)
    lower_domain: str | None = field(init=False, default=None, repr=False)
    lower_theme: str | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        self.lower_title = self.title.lower() if self.title else None
        self.lower_domain = self.domain.lower() if self.domain else None
        self.lower_theme = self.theme.lower() if self.theme else None

    @staticmethod
    def from_dict(obj: Any) -> FormationsHit:
        if not isinstance(obj, dict):
            raise TypeError(f"Expected dict, got {obj.__class__.__name__}")
        id = from_str(obj, "id")
        title = from_str(obj, "title")
        type = from_str(obj, "type")
        mode = from_str(obj, "mode")
        domain = from_str(obj, "domain")
        theme = from_str(obj, "theme")
        description = from_str(obj, "description")
        goals = from_str(obj, "goals")
        public = from_str(obj, "public")
        prerequisites = from_str(obj, "prerequisites")
        content = from_str(obj, "content")
        pedagogy = from_str(obj, "pedagogy")
        certification = from_str(obj, "certification")
        results = from_str(obj, "results")
        modalities = from_str(obj, "modalities")
        level = from_str(obj, "level")
        reference = from_str(obj, "reference")
        program_id_fbi = from_str(obj, "programIdFbi")
        duration_hours = from_duration(obj, "duration_hours")
        sessions = from_list(FormationSession.from_dict, obj, "sessions")
        files = from_list(lambda x: x, obj, "files")
        image = from_str(obj, "image")
        thumbnail = from_str(obj, "thumbnail")
        mode_hidden = from_str(obj, "mode_hidden")
        postal_codes = from_list(str, obj, "postal_codes")
        places = from_list(str, obj, "places")
        id_origin_hash = from_str(obj, "id_origin_hash")
        date_end = from_datetime(obj, "date_end")
        date_end_formatted = from_int(obj, "date_end_formatted")
        date_start = from_datetime(obj, "date_start")
        date_start_formatted = from_int(obj, "date_start_formatted")
        entity = from_str(obj, "entity")
        formation_domain = from_str(obj, "formation_domain")
        formation_duration_hours = from_str(obj, "formation_duration_hours")
        formation_id = from_uuid(obj, "formation_id")
        formation_image = from_str(obj, "formation_image")
        formation_mode = from_str(obj, "formation_mode")
        formation_theme = from_str(obj, "formation_theme")
        formation_thumbnail = from_str(obj, "formation_thumbnail")
        formation_title = from_str(obj, "formation_title")
        place = from_str(obj, "place")
        postal_code = from_str(obj, "postal_code")
        reference_hidden = from_str(obj, "reference_hidden")
        subscribe_btn = from_str(obj, "subscribeBtn")
        subscribe_button = from_str(obj, "subscribe_button")
        return FormationsHit(
            id=id,
            title=title,
            type=type,
            mode=mode,
            domain=domain,
            theme=theme,
            description=description,
            goals=goals,
            public=public,
            prerequisites=prerequisites,
            content=content,
            pedagogy=pedagogy,
            certification=certification,
            results=results,
            modalities=modalities,
            level=level,
            reference=reference,
            program_id_fbi=program_id_fbi,
            duration_hours=duration_hours,
            sessions=sessions,
            files=files,
            image=image,
            thumbnail=thumbnail,
            mode_hidden=mode_hidden,
            postal_codes=postal_codes,
            places=places,
            id_origin_hash=id_origin_hash,
            date_end=date_end,
            date_end_formatted=date_end_formatted,
            date_start=date_start,
            date_start_formatted=date_start_formatted,
            entity=entity,
            formation_domain=formation_domain,
            formation_duration_hours=formation_duration_hours,
            formation_id=formation_id,
            formation_image=formation_image,
            formation_mode=formation_mode,
            formation_theme=formation_theme,
            formation_thumbnail=formation_thumbnail,
            formation_title=formation_title,
            place=place,
            postal_code=postal_code,
            reference_hidden=reference_hidden,
            subscribe_btn=subscribe_btn,
            subscribe_button=subscribe_button,
        )

    def to_dict(self) -> dict:
        result: dict = {}
        to_dict_set(result, "id", self.id)
        to_dict_set(result, "title", self.title)
        to_dict_set(result, "type", self.type)
        to_dict_set(result, "mode", self.mode)
        to_dict_set(result, "domain", self.domain)
        to_dict_set(result, "theme", self.theme)
        to_dict_set(result, "description", self.description)
        to_dict_set(result, "goals", self.goals)
        to_dict_set(result, "public", self.public)
        to_dict_set(result, "prerequisites", self.prerequisites)
        to_dict_set(result, "content", self.content)
        to_dict_set(result, "pedagogy", self.pedagogy)
        to_dict_set(result, "certification", self.certification)
        to_dict_set(result, "results", self.results)
        to_dict_set(result, "modalities", self.modalities)
        to_dict_set(result, "level", self.level)
        to_dict_set(result, "reference", self.reference)
        to_dict_set(result, "programIdFbi", self.program_id_fbi)
        if self.duration_hours is not None:
            total_seconds = int(self.duration_hours.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60
            result["duration_hours"] = f"{hours}h{minutes:02d}"
        if self.sessions is not None:
            result["sessions"] = [s.to_dict() for s in self.sessions]
        to_dict_set(result, "files", self.files)
        to_dict_set(result, "image", self.image)
        to_dict_set(result, "thumbnail", self.thumbnail)
        to_dict_set(result, "mode_hidden", self.mode_hidden)
        to_dict_set(result, "postal_codes", self.postal_codes)
        to_dict_set(result, "places", self.places)
        to_dict_set(result, "id_origin_hash", self.id_origin_hash)
        if self.date_end is not None:
            result["date_end"] = self.date_end.isoformat()
        to_dict_set(result, "date_end_formatted", self.date_end_formatted)
        if self.date_start is not None:
            result["date_start"] = self.date_start.isoformat()
        to_dict_set(result, "date_start_formatted", self.date_start_formatted)
        to_dict_set(result, "entity", self.entity)
        to_dict_set(result, "formation_domain", self.formation_domain)
        to_dict_set(result, "formation_duration_hours", self.formation_duration_hours)
        if self.formation_id is not None:
            result["formation_id"] = str(self.formation_id)
        to_dict_set(result, "formation_image", self.formation_image)
        to_dict_set(result, "formation_mode", self.formation_mode)
        to_dict_set(result, "formation_theme", self.formation_theme)
        to_dict_set(result, "formation_thumbnail", self.formation_thumbnail)
        to_dict_set(result, "formation_title", self.formation_title)
        to_dict_set(result, "place", self.place)
        to_dict_set(result, "postal_code", self.postal_code)
        to_dict_set(result, "reference_hidden", self.reference_hidden)
        to_dict_set(result, "subscribeBtn", self.subscribe_btn)
        to_dict_set(result, "subscribe_button", self.subscribe_button)
        return result

    def is_valid_for_query(self, query: str) -> bool:
        return bool(
            not query
            or (self.lower_title and query in self.lower_title)
            or (self.lower_domain and query in self.lower_domain)
            or (self.lower_theme and query in self.lower_theme)
        )
