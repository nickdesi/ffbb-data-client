from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from ..utils.converter_utils import (
    from_datetime,
    from_enum,
    from_float,
    from_int,
    from_list,
    from_obj,
    from_str,
    from_uuid,
    to_dict_set,
)
from .document_flyer_type import DocumentFlyerType
from .facet_stats import FacetStats
from .folder import Folder
from .source import Source


@dataclass
class DocumentFlyer:
    id: UUID | None = None
    storage: str | None = None
    filename_disk: str | None = None
    filename_download: str | None = None
    title: str | None = None
    type: DocumentFlyerType | None = None
    uploaded_on: datetime | None = None
    modified_on: datetime | None = None
    charset: str | None = None
    filesize: int | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    embed: str | None = None
    description: str | None = None
    location: str | None = None
    tags: str | None = None
    metadata: FacetStats | None = None
    source: Source | None = None
    credits: str | None = None
    gradient_color: str | None = None
    md5: str | None = None
    newsbridge_media_id: str | None = None
    newsbridge_metadatas: str | None = None
    newsbridge_name: str | None = None
    newsbridge_recorded_at: datetime | None = None
    focal_point_x: float | None = None
    focal_point_y: float | None = None
    newsbridge_labels: list[Any] | None = None
    newsbridge_persons: list[Any] | None = None
    folder: Folder | None = None
    uploaded_by: UUID | None = None
    modified_by: UUID | None = None
    newsbridge_mission: str | None = None

    @staticmethod
    def from_dict(obj: Any) -> DocumentFlyer:
        assert isinstance(obj, dict)
        id = from_uuid(obj, "id")
        storage = from_str(obj, "storage")
        filename_disk = from_str(obj, "filename_disk")
        filename_download = from_str(obj, "filename_download")
        title = from_str(obj, "title")
        type = from_enum(DocumentFlyerType, obj, "type")
        uploaded_on = from_datetime(obj, "uploaded_on")
        modified_on = from_datetime(obj, "modified_on")
        charset = from_str(obj, "charset")
        filesize = from_int(obj, "filesize")
        width = from_int(obj, "width")
        height = from_int(obj, "height")
        duration = from_int(obj, "duration")
        embed = from_str(obj, "embed")
        description = from_str(obj, "description")
        location = from_str(obj, "location")
        tags = from_str(obj, "tags")
        metadata = from_obj(FacetStats.from_dict, obj, "metadata")
        source = from_enum(Source, obj, "source")
        credits = from_str(obj, "credits")
        gradient_color = from_str(obj, "gradient_color")
        md5 = from_str(obj, "md5")
        newsbridge_media_id = from_str(obj, "newsbridge_media_id")
        newsbridge_metadatas = from_str(obj, "newsbridge_metadatas")
        newsbridge_name = from_str(obj, "newsbridge_name")
        newsbridge_recorded_at = from_datetime(obj, "newsbridge_recorded_at")
        focal_point_x = from_float(obj, "focal_point_x")
        focal_point_y = from_float(obj, "focal_point_y")
        newsbridge_labels = from_list(lambda x: x, obj, "newsbridge_labels")
        newsbridge_persons = from_list(lambda x: x, obj, "newsbridge_persons")
        folder = from_obj(Folder.from_dict, obj, "folder")
        uploaded_by = from_uuid(obj, "uploaded_by")
        modified_by = from_uuid(obj, "modified_by")
        newsbridge_mission = from_str(obj, "newsbridge_mission")
        return DocumentFlyer(
            id=id,
            storage=storage,
            filename_disk=filename_disk,
            filename_download=filename_download,
            title=title,
            type=type,
            uploaded_on=uploaded_on,
            modified_on=modified_on,
            charset=charset,
            filesize=filesize,
            width=width,
            height=height,
            duration=duration,
            embed=embed,
            description=description,
            location=location,
            tags=tags,
            metadata=metadata,
            source=source,
            credits=credits,
            gradient_color=gradient_color,
            md5=md5,
            newsbridge_media_id=newsbridge_media_id,
            newsbridge_metadatas=newsbridge_metadatas,
            newsbridge_name=newsbridge_name,
            newsbridge_recorded_at=newsbridge_recorded_at,
            focal_point_x=focal_point_x,
            focal_point_y=focal_point_y,
            newsbridge_labels=newsbridge_labels,
            newsbridge_persons=newsbridge_persons,
            folder=folder,
            uploaded_by=uploaded_by,
            modified_by=modified_by,
            newsbridge_mission=newsbridge_mission,
        )

    def to_dict(self) -> dict:
        result: dict = {}
        if self.id is not None:
            result["id"] = str(self.id)
        to_dict_set(result, "storage", self.storage)
        to_dict_set(result, "filename_disk", self.filename_disk)
        to_dict_set(result, "filename_download", self.filename_download)
        to_dict_set(result, "title", self.title)
        if self.type is not None:
            result["type"] = self.type.value
        if self.uploaded_on is not None:
            result["uploaded_on"] = self.uploaded_on.isoformat()
        if self.modified_on is not None:
            result["modified_on"] = self.modified_on.isoformat()
        if self.filesize is not None:
            result["filesize"] = str(self.filesize)
        to_dict_set(result, "width", self.width)
        to_dict_set(result, "height", self.height)
        if self.metadata is not None:
            result["metadata"] = self.metadata.to_dict()
        if self.source is not None:
            result["source"] = self.source.value
        to_dict_set(result, "gradient_color", self.gradient_color)
        to_dict_set(result, "md5", self.md5)
        to_dict_set(result, "newsbridge_labels", self.newsbridge_labels)
        to_dict_set(result, "newsbridge_persons", self.newsbridge_persons)
        if self.folder is not None:
            result["folder"] = self.folder.to_dict()
        to_dict_set(result, "charset", self.charset)
        to_dict_set(result, "duration", self.duration)
        to_dict_set(result, "embed", self.embed)
        to_dict_set(result, "description", self.description)
        to_dict_set(result, "location", self.location)
        to_dict_set(result, "tags", self.tags)
        to_dict_set(result, "credits", self.credits)
        to_dict_set(result, "newsbridge_media_id", self.newsbridge_media_id)
        to_dict_set(result, "newsbridge_metadatas", self.newsbridge_metadatas)
        to_dict_set(result, "newsbridge_name", self.newsbridge_name)
        if self.newsbridge_recorded_at is not None:
            result["newsbridge_recorded_at"] = self.newsbridge_recorded_at.isoformat()
        to_dict_set(result, "focal_point_x", self.focal_point_x)
        to_dict_set(result, "focal_point_y", self.focal_point_y)
        if self.uploaded_by is not None:
            result["uploaded_by"] = str(self.uploaded_by)
        if self.modified_by is not None:
            result["modified_by"] = str(self.modified_by)
        to_dict_set(result, "newsbridge_mission", self.newsbridge_mission)
        return result
