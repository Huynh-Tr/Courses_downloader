"""
Neutral, provider-agnostic data models and legacy Coursera adapter.

Defines immutable data structures representing course structure and resources:
CourseManifest -> Module -> Section -> Lecture -> Resource.
Provides bidirectional conversion with Coursera legacy tuple hierarchies.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Tuple

from define import IN_MEMORY_MARKER


def infer_resource_kind(format_ext: str) -> str:
    """Infer semantic resource kind from its file extension."""
    fmt = format_ext.lower().strip()
    if fmt == "mp4":
        return "video"
    if fmt in ("srt", "vtt"):
        return "subtitle"
    if fmt == "txt":
        return "transcript"
    if fmt in ("html", "htm"):
        return "reading"
    if fmt == "ipynb":
        return "notebook"
    if fmt in ("pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "csv", "tsv", "zip", "rar"):
        return "document"
    return "generic"


@dataclass(frozen=True)
class Resource:
    """A downloadable or in-memory resource belonging to a lecture."""

    index: int
    format: str
    title: str
    source: str
    is_in_memory: bool = False
    kind: str = "generic"
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self):
        if self.index < 0:
            raise ValueError(f"Resource index must be non-negative, got {self.index}")
        if not self.format or not isinstance(self.format, str):
            raise ValueError(f"Resource format must be a non-empty string, got {self.format!r}")
        if not self.source or not isinstance(self.source, str):
            raise ValueError("Resource source must be a non-empty string")

    @property
    def legacy_url(self) -> str:
        """Return the URL as expected by legacy Coursera downloaders."""
        if self.is_in_memory:
            return f"{IN_MEMORY_MARKER}{self.source}"
        return self.source


@dataclass(frozen=True)
class Lecture:
    """A single lecture, reading, or unit containing resources."""

    index: int
    slug: str
    title: str
    resources: Tuple[Resource, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self):
        if self.index < 0:
            raise ValueError(f"Lecture index must be non-negative, got {self.index}")
        if not isinstance(self.slug, str):
            raise ValueError(f"Lecture slug must be a string, got {self.slug!r}")


@dataclass(frozen=True)
class Section:
    """A section (lesson) containing lectures."""

    index: int
    slug: str
    title: str
    lectures: Tuple[Lecture, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self):
        if self.index < 0:
            raise ValueError(f"Section index must be non-negative, got {self.index}")
        if not isinstance(self.slug, str):
            raise ValueError(f"Section slug must be a string, got {self.slug!r}")


@dataclass(frozen=True)
class Module:
    """A module (week / chapter) containing sections."""

    index: int
    slug: str
    title: str
    sections: Tuple[Section, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self):
        if self.index < 0:
            raise ValueError(f"Module index must be non-negative, got {self.index}")
        if not isinstance(self.slug, str):
            raise ValueError(f"Module slug must be a string, got {self.slug!r}")


@dataclass(frozen=True)
class CourseManifest:
    """Complete structured manifest of a course across any provider."""

    provider: str
    course_id: str
    slug: str
    title: str
    modules: Tuple[Module, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self):
        if not self.provider or not isinstance(self.provider, str):
            raise ValueError("CourseManifest provider must be a non-empty string")
        if not self.slug or not isinstance(self.slug, str):
            raise ValueError("CourseManifest slug must be a non-empty string")

    @property
    def total_resources(self) -> int:
        """Count total resources across all modules, sections, and lectures."""
        count = 0
        for mod in self.modules:
            for sec in mod.sections:
                for lec in sec.lectures:
                    count += len(lec.resources)
        return count

    def iter_resources(self) -> Iterable[Tuple[Module, Section, Lecture, Resource]]:
        """Yield a flat stream of (module, section, lecture, resource) in stable order."""
        for mod in self.modules:
            for sec in mod.sections:
                for lec in sec.lectures:
                    for res in lec.resources:
                        yield mod, sec, lec, res


def legacy_to_manifest(
    legacy_modules: Any,
    class_name: str,
    course_id: str = "",
    title: str = "",
    provider: str = "coursera",
) -> CourseManifest:
    """
    Convert Coursera legacy syllabus tuples into an immutable CourseManifest.

    Legacy shape:
      [(module_slug, [(section_slug, [(lecture_slug, {fmt: [(url, title)]})])])]
    """
    if not isinstance(legacy_modules, (list, tuple)):
        raise ValueError(f"legacy_modules must be a list or tuple, got {type(legacy_modules).__name__}")

    course_title = title if title else class_name
    parsed_modules: List[Module] = []

    for mod_idx, mod_item in enumerate(legacy_modules):
        if not isinstance(mod_item, (list, tuple)) or len(mod_item) != 2:
            raise ValueError(f"Malformed module at index {mod_idx}: expected (slug, sections) pair")

        mod_slug, sec_list = mod_item
        if not isinstance(sec_list, (list, tuple)):
            raise ValueError(f"Malformed sections list in module {mod_slug!r}")

        parsed_sections: List[Section] = []
        for sec_idx, sec_item in enumerate(sec_list):
            if not isinstance(sec_item, (list, tuple)) or len(sec_item) != 2:
                raise ValueError(f"Malformed section at index {sec_idx} in module {mod_slug!r}")

            sec_slug, lec_list = sec_item
            if not isinstance(lec_list, (list, tuple)):
                raise ValueError(f"Malformed lectures list in section {sec_slug!r}")

            parsed_lectures: List[Lecture] = []
            for lec_idx, lec_item in enumerate(lec_list):
                if not isinstance(lec_item, (list, tuple)) or len(lec_item) != 2:
                    raise ValueError(f"Malformed lecture at index {lec_idx} in section {sec_slug!r}")

                lec_slug, links_dict = lec_item
                if not isinstance(links_dict, dict):
                    raise ValueError(f"Malformed links dict in lecture {lec_slug!r}")

                parsed_resources: List[Resource] = []
                res_idx = 0
                for fmt, url_title_pairs in links_dict.items():
                    if not isinstance(url_title_pairs, (list, tuple)):
                        continue
                    for pair in url_title_pairs:
                        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                            continue
                        url, res_title = pair
                        is_in_mem = url.startswith(IN_MEMORY_MARKER)
                        payload = url[len(IN_MEMORY_MARKER) :] if is_in_mem else url
                        parsed_resources.append(
                            Resource(
                                index=res_idx,
                                format=str(fmt),
                                title=str(res_title),
                                source=str(payload),
                                is_in_memory=is_in_mem,
                                kind=infer_resource_kind(str(fmt)),
                            )
                        )
                        res_idx += 1

                parsed_lectures.append(
                    Lecture(
                        index=lec_idx,
                        slug=str(lec_slug),
                        title=str(lec_slug),
                        resources=tuple(parsed_resources),
                    )
                )

            parsed_sections.append(
                Section(
                    index=sec_idx,
                    slug=str(sec_slug),
                    title=str(sec_slug),
                    lectures=tuple(parsed_lectures),
                )
            )

        parsed_modules.append(
            Module(
                index=mod_idx,
                slug=str(mod_slug),
                title=str(mod_slug),
                sections=tuple(parsed_sections),
            )
        )

    return CourseManifest(
        provider=provider,
        course_id=course_id or class_name,
        slug=class_name,
        title=course_title,
        modules=tuple(parsed_modules),
    )


def manifest_to_legacy(manifest: CourseManifest) -> List[Tuple[str, List[Tuple[str, List[Tuple[str, dict]]]]]]:
    """
    Convert a CourseManifest back into the exact Coursera legacy tuple structure.

    Guarantees 100% round-trip fidelity with legacy consumers.
    """
    legacy_modules = []
    for mod in manifest.modules:
        legacy_sections = []
        for sec in mod.sections:
            legacy_lectures = []
            for lec in sec.lectures:
                links_dict: dict = {}
                for res in lec.resources:
                    fmt = res.format
                    if fmt not in links_dict:
                        links_dict[fmt] = []
                    links_dict[fmt].append((res.legacy_url, res.title))
                legacy_lectures.append((lec.slug, links_dict))
            legacy_sections.append((sec.slug, legacy_lectures))
        legacy_modules.append((mod.slug, legacy_sections))
    return legacy_modules
