from dataclasses import asdict, dataclass, is_dataclass
from types import FrameType
from typing import Any, Literal, Optional
import json
import runpy
import sys
import time
import pathlib

__version__ = '0.0.3'


@dataclass(slots=True, frozen=True)
class Frame:
    name: str
    file: Optional[str]
    line: Optional[int]


@dataclass(slots=True, frozen=True)
class FrameEvent:
    type: Literal['O', 'C']
    frame: int
    at: float


@dataclass(slots=True, frozen=True)
class Shared:
    frames: list[Frame]


@dataclass(slots=True, frozen=True)
class EventedProfile:
    type: Literal['evented']
    name: str
    unit: str
    startValue: float
    endValue: Optional[float]
    events: list[FrameEvent]


@dataclass(slots=True, frozen=True)
class File:
    schema: str
    shared: Shared
    profiles: list[EventedProfile]
    name: Optional[str]
    activeProfileIndex: Optional[int]
    exporter: Optional[str]


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, File):
            d = asdict(o)
            d['$schema'] = d.pop('schema')
            return d
        elif is_dataclass(o):
            return asdict(o)
        return super().default(o)


# key: id(frame), value: (index, frame)
frames: dict[str, tuple[int, Frame]] = {}
events: list[FrameEvent] = []

# filters used to filter out frames by matching filenames.
filters: list[str] = []


profiling_offset = 0
waiting_to_enter_mainpyfile = True


def profilefunc(frame: FrameType, event: str, arg: Any) -> object:
    t = time.perf_counter()
    global profiling_offset
    try:
        filename, fnname, lineno = frame.f_code.co_filename, frame.f_code.co_name, frame.f_lineno

        # Ignore everything until after we call `runpy._run_code()`.
        global waiting_to_enter_mainpyfile
        if waiting_to_enter_mainpyfile:
            if filename.endswith('runpy.py') and fnname == '_run_code':
                waiting_to_enter_mainpyfile = False
            return

        if event != 'call' and event != 'return':
            return

        if len(filters) > 0 and not any(f in filename for f in filters):
            return

        if event == 'call':
            event_type = 'O'
            key = id(frame)
            if key not in frames:
                idx = len(frames)
                frames[key] = idx, Frame(fnname, filename, lineno)
            else:
                idx, _ = frames[key]
        if event == 'return':
            event_type = 'C'
            key = id(frame)
            if key not in frames:
                return
            idx, _ = frames[key]

        events.append(FrameEvent(event_type, idx, t - profiling_offset))
    finally:
        profiling_offset += (time.perf_counter() - t)


def write_pttp_profile_to_file(mainpyfile: str):
    if len(events) <= 1:
        return

    sys.setprofile(None)
    # Drop last event if it's this function.
    if frames:
        _, lastframe = next(reversed(frames.values()))
        if lastframe.name == 'write_pttp_profile_to_file':
            events.pop()
            frames.popitem()

    filename = pathlib.Path(mainpyfile).with_suffix('.speedscope.json')
    profile = EventedProfile(
        type='evented',
        name=str(filename),
        unit='seconds',
        startValue=events[0].at,
        endValue=None,
        events=events,
    )
    file = File(
        schema="https://www.speedscope.app/file-format-schema.json",
        shared=Shared(frames=[f for _, f in frames.values()]),
        profiles=[profile],
        name=str(filename),
        activeProfileIndex=0,
        exporter='pttp',
    )
    with open(file.name, 'w') as f:
        json.dump(file, f, indent=2, cls=EnhancedJSONEncoder)


_usage = """\
usage: pttp.py [OPTIONS] [-m module | pyfile]

Trace the Python program given by pyfile or -m module.

Options:
  --filter TEXT     Only include frames whose filenames contain this string.
  -h, --help        Show this help message and exit.
"""


def main():
    # Mostly copied from https://github.com/python/cpython/blob/8c4cf96a06e2483a11a4cb34c550df5bd22f990b/Lib/pdb.py#L1878

    import getopt

    opts, args = getopt.getopt(sys.argv[1:], 'mhf=', ['help', 'filter='])

    if not args:
        print(_usage)
        sys.exit(2)

    if any(opt in ['-h', '--help'] for opt, optarg in opts):
        print(_usage)
        sys.exit()

    if any(opt in ['-f', '--filter'] for opt, optarg in opts):
        global filters
        filters = [optarg for opt, optarg in opts if opt in ['-f', '--filter']]

    # Hide "pttp.py" and options from argument list
    sys.argv[:] = args

    sys.setprofile(profilefunc)
    try:
        module_indicated = any(opt in ['-m'] for opt, optarg in opts)
        mainpyfile = args[0]

        if module_indicated:
            runpy._run_module_as_main(mainpyfile, alter_argv=False)
        else:
            runpy.run_path(mainpyfile, run_name='__main__')
    finally:
        write_pttp_profile_to_file(mainpyfile)
