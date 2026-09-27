import abc
import codecs
from dataclasses import dataclass
import glob
import logging
import os
import re
import subprocess
import time
from typing import Any, List, Optional, Tuple, Union
from urllib.parse import urlparse

import requests

from define import FORMAT_MAX_LENGTH, IN_MEMORY_MARKER, TITLE_MAX_LENGTH
import models
from utils import is_course_complete, mkdir_p, normalize_path

# --- filtering (merged from filtering.py) ---

VALID_FORMATS = r"""^mp4$|
                    ^pdf$|
                    ^.?.?\.?txt$|
                    ^.?.?\.?srt$|
                    .*txt$|
                    .*srt$|
                    ^html?$|
                    ^zip$|
                    ^rar$|
                    ^[ct]sv$|
                    ^xlsx$|
                    ^ipynb$|
                    ^json$|
                    ^pptx?$|
                    ^docx?$|
                    ^xls$|
                    ^py$|
                    ^Rmd$|
                    ^Rdata$|
                    ^wf1$"""
NON_SIMPLE_FORMAT = r".*[^a-zA-Z0-9_-]"
RE_VALID_FORMATS = re.compile(VALID_FORMATS, re.VERBOSE)
RE_NON_SIMPLE_FORMAT = re.compile(NON_SIMPLE_FORMAT)


def skip_format_url(format_, url):
    if format_ == "":
        return True
    if ("mailto:" in url) and ("@" in url):
        return True
    parsed = urlparse(url)
    if parsed.hostname == "localhost":
        return True
    if RE_VALID_FORMATS.match(format_):
        return False
    if RE_NON_SIMPLE_FORMAT.match(format_):
        return True
    if parsed.path in ("", "/"):
        return True
    return False


def find_resources_to_get(lecture, file_formats, resource_filter, ignored_formats=None):
    resources_to_get = []
    if ignored_formats is None:
        ignored_formats = []
    if len(ignored_formats):
        logging.info(
            "The following file formats will be ignored: " + ",".join(ignored_formats)
        )
    for fmt, resources in lecture.items():
        fmt0 = fmt
        short_fmt = None
        if "." in fmt:
            short_fmt = fmt.split(".")[1]
        if fmt in ignored_formats or (
            short_fmt is not None and short_fmt in ignored_formats
        ):
            continue
        if (
            fmt in file_formats
            or (short_fmt is not None and short_fmt in file_formats)
            or "all" in file_formats
        ):
            for r in resources:
                if resource_filter and r[1] and not re.search(resource_filter, r[1]):
                    logging.debug("Skipping b/c of rf: %s %s", resource_filter, r[1])
                    continue
                resources_to_get.append((fmt0, r[0], r[1]))
        else:
            logging.debug("Skipping b/c format %s not in %s", fmt, file_formats)
    return resources_to_get


# --- formatting (merged from formatting.py) ---


def format_section(num, section, class_name, verbose_dirs):
    sec = "%02d_%s" % (num, section)
    if verbose_dirs:
        sec = class_name.upper() + "_" + sec
    return sec


def format_resource(num, name, title, fmt):
    if title:
        title = "_" + title
    return "%02d_%s%s.%s" % (num, name, title, fmt)


def format_combine_number_resource(secnum, lecnum, lecname, title, fmt):
    if title:
        title = "_" + title
    return "%02d_%02d_%s%s.%s" % (secnum, lecnum, lecname, title, fmt)


def get_lecture_filename(
    combined_section_lectures_nums, section_dir, secnum, lecnum, lecname, title, fmt
):
    fmt = fmt[:FORMAT_MAX_LENGTH]
    title = title[:TITLE_MAX_LENGTH]
    if combined_section_lectures_nums:
        lecture_filename = os.path.join(
            section_dir,
            format_combine_number_resource(secnum + 1, lecnum + 1, lecname, title, fmt),
        )
    else:
        lecture_filename = os.path.join(
            section_dir, format_resource(lecnum + 1, lecname, title, fmt)
        )
    return lecture_filename


# --- playlist (merged from playlist.py) ---


def create_m3u_playlist(section_dir):
    path_to_return = os.getcwd()
    for _path, subdirs, files in os.walk(section_dir):
        os.chdir(_path)
        globbed_videos = sorted(glob.glob("*.mp4"))
        m3u_name = os.path.split(_path)[1] + ".m3u"
        if len(globbed_videos):
            with open(m3u_name, "w") as m3u:
                for video in globbed_videos:
                    m3u.write(video + "\n")
            os.chdir(path_to_return)
    os.chdir(path_to_return)


def _iter_modules(modules, class_name, path, ignored_formats, args):
    """
    This huge function generates a hierarchy with hopefully more
    clear structure of modules/sections/lectures.
    """
    file_formats = args.file_formats
    lecture_filter = args.lecture_filter
    resource_filter = args.resource_filter
    section_filter = args.section_filter
    verbose_dirs = args.verbose_dirs
    combined_section_lectures_nums = args.combined_section_lectures_nums

    class IterModule:
        def __init__(self, index, module):
            self.index = index
            self.name = "%02d_%s" % (index + 1, module[0])
            self._module = module

        @property
        def sections(self):
            sections = self._module[1]
            for secnum, (section, lectures) in enumerate(sections):
                if section_filter and not re.search(section_filter, section):
                    logging.debug("Skipping b/c of sf: %s %s", section_filter, section)
                    continue

                yield IterSection(self, secnum, section, lectures)

    class IterSection:
        def __init__(self, module_iter, secnum, section, lectures):
            self.index = secnum
            self.name = "%02d_%s" % (secnum, section)
            self.dir = os.path.join(
                path,
                class_name,
                module_iter.name,
                format_section(secnum + 1, section, class_name, verbose_dirs),
            )
            self._lectures = lectures

        @property
        def lectures(self):
            for lecnum, (lecname, lecture) in enumerate(self._lectures):
                if lecture_filter and not re.search(lecture_filter, lecname):
                    logging.debug("Skipping b/c of lf: %s %s", lecture_filter, lecname)
                    continue

                yield IterLecture(self, lecnum, lecname, lecture)

    class IterLecture:
        def __init__(self, section_iter, lecnum, lecname, lecture):
            self.index = lecnum
            self.name = lecname
            self._lecture = lecture
            self._section_iter = section_iter

        def filename(self, fmt, title):
            lecture_filename = get_lecture_filename(
                combined_section_lectures_nums,
                self._section_iter.dir,
                self._section_iter.index,
                self.index,
                self.name,
                title,
                fmt,
            )
            return lecture_filename

        @property
        def resources(self):
            resources_to_get = find_resources_to_get(
                self._lecture, file_formats, resource_filter, ignored_formats
            )

            for fmt, url, title in resources_to_get:
                yield IterResource(fmt, url, title)

    class IterResource:
        def __init__(self, fmt, url, title):
            self.fmt = fmt
            self.url = url
            self.title = title

    for index, module in enumerate(modules):
        yield IterModule(index, module)


def _walk_modules(modules, class_name, path, ignored_formats, args):
    """
    Helper generator that traverses modules in returns a flattened
    iterator.
    """
    for module in _iter_modules(
        modules=modules,
        class_name=class_name,
        path=path,
        ignored_formats=ignored_formats,
        args=args,
    ):
        for section in module.sections:
            for lecture in section.lectures:
                for resource in lecture.resources:
                    yield module, section, lecture, resource


class CourseDownloader:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def download_modules(self, modules):
        pass


@dataclass(frozen=True)
class PlannedResource:
    """Resource planned for download with concrete target path."""

    url: str
    fmt: str
    filename: str
    title: str
    is_in_memory: bool = False


@dataclass(frozen=True)
class PlannedSection:
    """Section containing concrete target directory and planned resources."""

    index: int
    slug: str
    dir: str
    resources: Tuple[PlannedResource, ...] = ()


@dataclass(frozen=True)
class PlannedModule:
    """Module containing planned sections."""

    index: int
    slug: str
    name: str
    sections: Tuple[PlannedSection, ...] = ()


def plan_downloads(
    modules: Union[List, Tuple, models.CourseManifest],
    class_name: str,
    path: str = "",
    ignored_formats: Optional[List[str]] = None,
    args: Optional[Any] = None,
) -> List[PlannedModule]:
    """Pure planning function: maps CourseManifest or legacy tuples to planned modules.

    Does no I/O, network requests, or filesystem writes.
    """
    if isinstance(modules, models.CourseManifest):
        manifest = modules
    else:
        manifest = models.legacy_to_manifest(modules, class_name=class_name)

    file_formats = getattr(args, "file_formats", ["all"])
    lecture_filter = getattr(args, "lecture_filter", None)
    resource_filter = getattr(args, "resource_filter", None)
    section_filter = getattr(args, "section_filter", None)
    verbose_dirs = getattr(args, "verbose_dirs", False)
    combined_section_lectures_nums = getattr(args, "combined_section_lectures_nums", False)
    ignored_formats = ignored_formats or []

    if len(ignored_formats):
        logging.info("The following file formats will be ignored: " + ",".join(ignored_formats))

    planned_modules: List[PlannedModule] = []
    for mod in manifest.modules:
        mod_name = "%02d_%s" % (mod.index + 1, mod.slug)
        planned_sections: List[PlannedSection] = []

        for sec in mod.sections:
            if section_filter and not re.search(section_filter, sec.slug):
                logging.debug("Skipping b/c of sf: %s %s", section_filter, sec.slug)
                continue

            sec_dir = os.path.join(
                path,
                class_name,
                mod_name,
                format_section(sec.index + 1, sec.slug, class_name, verbose_dirs),
            )
            planned_resources: List[PlannedResource] = []

            for lec in sec.lectures:
                if lecture_filter and not re.search(lecture_filter, lec.slug):
                    logging.debug("Skipping b/c of lf: %s %s", lecture_filter, lec.slug)
                    continue

                for res in lec.resources:
                    fmt = res.format
                    short_fmt = fmt.split(".")[1] if "." in fmt else None
                    if fmt in ignored_formats or (short_fmt is not None and short_fmt in ignored_formats):
                        continue
                    if not (
                        fmt in file_formats
                        or (short_fmt is not None and short_fmt in file_formats)
                        or "all" in file_formats
                    ):
                        logging.debug("Skipping b/c format %s not in %s", fmt, file_formats)
                        continue
                    if resource_filter and res.title and not re.search(resource_filter, res.title):
                        logging.debug("Skipping b/c of rf: %s %s", resource_filter, res.title)
                        continue

                    filename = get_lecture_filename(
                        combined_section_lectures_nums,
                        sec_dir,
                        sec.index,
                        lec.index,
                        lec.slug,
                        res.title,
                        fmt,
                    )
                    planned_resources.append(
                        PlannedResource(
                            url=res.legacy_url,
                            fmt=fmt,
                            filename=normalize_path(filename),
                            title=res.title,
                            is_in_memory=res.is_in_memory,
                        )
                    )

            planned_sections.append(
                PlannedSection(
                    index=sec.index,
                    slug=sec.slug,
                    dir=normalize_path(sec_dir),
                    resources=tuple(planned_resources),
                )
            )

        planned_modules.append(
            PlannedModule(
                index=mod.index,
                slug=mod.slug,
                name=mod_name,
                sections=tuple(planned_sections),
            )
        )

    return planned_modules


class CourseraDownloader(CourseDownloader):
    def __init__(
        self,
        downloader,
        commandline_args,
        class_name,
        path="",
        ignored_formats=None,
        disable_url_skipping=False,
    ):
        super().__init__()

        self._downloader = downloader
        self._args = commandline_args
        self._class_name = class_name
        self._path = path
        self._ignored_formats = ignored_formats
        self._disable_url_skipping = disable_url_skipping

        self.skipped_urls = None if disable_url_skipping else []
        self.failed_urls = []

    def download_modules(self, modules):
        completed = True
        planned_modules = plan_downloads(
            modules=modules,
            class_name=self._class_name,
            path=self._path,
            ignored_formats=self._ignored_formats,
            args=self._args,
        )

        for module in planned_modules:
            last_update = -1
            for section in module.sections:
                if not os.path.exists(section.dir):
                    mkdir_p(normalize_path(section.dir))

                for resource in section.resources:
                    lecture_filename = normalize_path(resource.filename)
                    last_update = self._handle_resource(
                        resource.url,
                        resource.fmt,
                        lecture_filename,
                        self._download_completion_handler,
                        last_update,
                    )

                # After fetching resources, create a playlist in M3U format with the
                # videos downloaded.
                if getattr(self._args, "playlist", False):
                    create_m3u_playlist(section.dir)

                if getattr(self._args, "hooks", None):
                    self._run_hooks(section, self._args.hooks)

            # if we haven't updated any files in 1 month, we're probably
            # done with this course
            completed = completed and is_course_complete(last_update)

        if completed:
            logging.info("COURSE PROBABLY COMPLETE: " + self._class_name)

        # Wait for all downloads to complete
        self._downloader.join()
        return completed

    def download_manifest(self, manifest: models.CourseManifest):
        """Download a CourseManifest directly (shared seam for future providers)."""
        return self.download_modules(manifest)

    def _download_completion_handler(self, url, result):
        if isinstance(result, requests.exceptions.RequestException):
            logging.error(
                "The following error has occurred while " "downloading URL %s: %s",
                url,
                str(result),
            )
            self.failed_urls.append(url)
        elif isinstance(result, Exception):
            logging.error("Unknown exception occurred: %s", result)
            self.failed_urls.append(url)
        elif result is False:
            logging.error("Download failed and was skipped for URL %s", url)
            self.failed_urls.append(url)

    def _handle_resource(self, url, fmt, lecture_filename, callback, last_update):
        """
        Handle resource. This function builds up resource file name and
        downloads it if necessary.

        @param url: URL of the resource.
        @type url: str

        @param fmt: Format of the resource (pdf, csv, etc)
        @type fmt: str

        @param lecture_filename: File name of the lecture.
        @type lecture_filename: str

        @param callback: Callback that will be called when file has been
            downloaded. It will be called even if exception occurred.
        @type callback: callable(url, result) where result may be Exception

        @param last_update: Timestamp of the newest file so far.
        @type last_update: int

        @return: Updated latest mtime.
        @rtype: int
        """
        overwrite = self._args.overwrite
        resume = self._args.resume
        skip_download = self._args.skip_download

        # Decide whether we need to download it
        if overwrite or not os.path.exists(lecture_filename) or resume:
            if not skip_download:
                if url.startswith(IN_MEMORY_MARKER):
                    page_content = url[len(IN_MEMORY_MARKER) :]
                    logging.info("Saving page contents to: %s", lecture_filename)
                    with codecs.open(lecture_filename, "w", "utf-8") as file_object:
                        file_object.write(page_content)
                else:
                    if self.skipped_urls is not None and skip_format_url(fmt, url):
                        self.skipped_urls.append(url)
                    else:
                        logging.info("Downloading: %s", lecture_filename)
                        self._downloader.download(
                            callback, url, lecture_filename, resume=resume
                        )
            else:
                open(lecture_filename, "w").close()  # touch
            last_update = time.time()
        else:
            logging.info("%s already downloaded", lecture_filename)
            # if this file hasn't been modified in a long time,
            # record that time
            last_update = max(last_update, os.path.getmtime(lecture_filename))
        return last_update

    def _run_hooks(self, section, hooks):
        original_dir = os.getcwd()
        for hook in hooks:
            logging.info("Running hook %s for section %s.", hook, section.dir)
            os.chdir(section.dir)
            subprocess.call(hook)
        os.chdir(original_dir)
