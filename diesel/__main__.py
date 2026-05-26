# diesel/__main__.py
"""
Stable local test entry point.

Run from project root:

    python ./diesel

Examples:

    python ./diesel
    python ./diesel --output uuid
    python ./diesel --output none
    python ./diesel --cache off
    python ./diesel --cache create
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


# NOTE: Keep this because `python ./diesel` puts diesel/ on sys.path.
from builder.aggregator import aggregate
from engine.engine import run_engine_direct
from tools import save_json, hex_uuid, PadLvlWithFormatter

from config import (
    DEFAULT_CACHE_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_AGGREGATOR_OUTPUT_PATH,
)

# PACKAGE_DIR = Path(__file__).resolve().parent
# PROJECT_ROOT = PACKAGE_DIR.parent

# DEFAULT_CACHE_DIR = PROJECT_ROOT / "cache"
# DEFAULT_INPUT_DIR = PROJECT_ROOT / "input"
# DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
# DEFAULT_STATIC_OUTPUT_PATH = DEFAULT_OUTPUT_DIR / "aggregator.json"

# # === DEVELOPER DEBUG MODES ===
# PATH_DEBUG_MODE = False      # Path DEBUG mode that outputs OS paths and exits

@dataclass(frozen=True)
class RunConfig:
    target: str = "aggregate"          # "aggregate", "engine"
    cache_mode: str = "required"       # "off"  , "required" , "create"
    output_mode: str = "static"        # "none" , "static"   , "uuid"

    cache_dir: Path = DEFAULT_CACHE_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    static_output_path: Path = DEFAULT_AGGREGATOR_OUTPUT_PATH

    print_timing: bool = True
    json_indent: int = 2


@dataclass(frozen=True)
class RunResult:
    elapsed_seconds: float
    data: Any
    output_path: Optional[Path] = None


def parse_args() -> RunConfig:
    parser = argparse.ArgumentParser(
        prog="python ./diesel",
        description="Run the Diesel aggregator through a stable local entry point.",
    )

    parser.add_argument(
        "target",
        choices=("aggregate", "engine"),
        nargs="?",
        default="aggregate",
        help="What to run.",
    )
    
    parser.add_argument(
        "--cache",
        choices=("off", "required", "create"),
        default="required",
        help=(
            "Cache handling mode. "
            "'off' passes no cache dir, "
            "'required' requires the cache dir to already exist, "
            "'create' creates it if missing."
        ),
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Directory used for aggregator cache files.",
    )

    parser.add_argument(
        "--output",
        choices=("none", "static", "uuid"),
        default="static",
        help=(
            "Output handling mode. "
            "'none' does not write a file, "
            "'static' writes to a fixed path, "
            "'uuid' writes to output-dir/<uuid>.json."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory used for generated output files.",
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_AGGREGATOR_OUTPUT_PATH,
        help="Static output file path used when --output static.",
    )

    parser.add_argument(
        "--no-timing",
        action="store_true",
        help="Do not print elapsed runtime.",
    )

    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level for saved output.",
    )

    args = parser.parse_args()

    return RunConfig(
        target=args.target,
        cache_mode=args.cache,
        output_mode=args.output,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        static_output_path=args.output_path,
        print_timing=not args.no_timing,
        json_indent=args.indent,
    )


def resolve_cache_dir(config: RunConfig) -> Optional[Path]:
    if config.cache_mode == "off":
        return None

    cache_dir = config.cache_dir

    if cache_dir.exists() and not cache_dir.is_dir():
        raise NotADirectoryError(cache_dir)

    if not cache_dir.exists():
        if config.cache_mode == "create":
            cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            raise FileNotFoundError(cache_dir)

    return cache_dir


def resolve_output_path(config: RunConfig) -> Optional[Path]:
    if config.output_mode == "none":
        return None

    if config.output_mode == "static":
        output_path = config.static_output_path
    elif config.output_mode == "uuid":
        output_path = config.output_dir / f"{hex_uuid()}.json"
    else:
        raise ValueError(f"Unsupported output mode: {config.output_mode!r}")

    output_dir = output_path.parent

    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    return output_path


def run_timed(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[float, Any]:
    start_time = time.perf_counter()
    data = func(*args, **kwargs)
    elapsed_seconds = time.perf_counter() - start_time

    return elapsed_seconds, data


def run_aggregator(config: RunConfig) -> RunResult:
    cache_dir = resolve_cache_dir(config)
    output_path = resolve_output_path(config)

    elapsed_seconds, data = run_timed(
        aggregate,
        cache_dir=str(cache_dir) if cache_dir is not None else None,
    )

    if output_path is not None:
        save_json(
            str(output_path),
            data,
            indent=config.json_indent,
        )

    return RunResult(
        elapsed_seconds=elapsed_seconds,
        data=data,
        output_path=output_path,
    )

def run_engine(config: RunConfig) -> RunResult:
    elapsed_seconds, data = run_timed(run_engine_direct)

    return RunResult(
        elapsed_seconds=elapsed_seconds,
        data=data,
        output_path=None,
    )

def report_result(config: RunConfig, result: RunResult) -> None:
    if config.print_timing:
        print(f"Result took: {result.elapsed_seconds:.2f} seconds")

    if result.output_path is not None:
        print(f"Saved output to: {result.output_path}")

# def path_debug_mode() -> None:
#     colors, reset = PadLvlWithFormatter.COLORS, PadLvlWithFormatter.RESET
#     cprint1 = lambda text, **kwargs: print(f"{colors['ERROR']}{str(text)}{reset}", **kwargs)
#     cprint2 = lambda text, **kwargs: print(f"{colors['DEBUG']}{str(text)}{reset}", **kwargs)
#     print(("="*35) + "[ PATH DEBUG MODE ]" + ("="*35))
#     cprint1("                PACKAGE_DIR ",end="");cprint2(PACKAGE_DIR)
#     cprint1("               PROJECT_ROOT ",end="");cprint2(PROJECT_ROOT)
#     cprint1("          DEFAULT_CACHE_DIR ",end="");cprint2(DEFAULT_CACHE_DIR)
#     cprint1("          DEFAULT_INPUT_DIR ",end="");cprint2(DEFAULT_INPUT_DIR)
#     cprint1("         DEFAULT_OUTPUT_DIR ",end="");cprint2(DEFAULT_OUTPUT_DIR)
#     cprint1(" DEFAULT_STATIC_OUTPUT_PATH ",end="");cprint2(DEFAULT_STATIC_OUTPUT_PATH)
#     print("="*89)
#     exit(0)

def main() -> int:

    config = parse_args()

    if config.target == "aggregate":
        result = run_aggregator(config)
    elif config.target == "engine":
        result = run_engine(config)
    else:
        raise ValueError(f"Unknown target: {config.target!r}")

    report_result(config, result)

    return 0


if __name__ == "__main__":
    # if PATH_DEBUG_MODE:
    #     path_debug_mode()
    main()
    #raise SystemExit(main())




# # Shell Entry Point for Testing Script
# # WARNING: CONTAINS RE-USED CODE, DO NOT EXECUTE UNTIL LINKED PROPERLY!
# from typing import Any
# import os, time
# from pathlib import Path
# # from modules.builder.old_builder import autobuilder
# # from modules.builder.old_builder_v2 import builder
# from builder.aggregator import aggregate

# from tools import save_json, hex_uuid
# global result
# MAIN_FILE  = os.path.abspath(__file__)   # The `__main__.py` absolute file path
# MAIN_DIR   = os.path.dirname(MAIN_FILE)  # The parent directory path of this file (diesel/)

# FLAGS = {
#     "cache_files": True  ,    # Should we use the /cache directory to store file caches?
#     "does_output": True  ,    # Does the result get output to an output directory?
#     "fix_missing": False ,    # Should missing directories (ie. cache and output) be created?
#     "print_timed": True  ,    # Do we print the time it took for the function to run?
#     "alt_caching": True  ,    # Should we use the cache parent path BUILD option?
#     "using_fname": False ,    # Should the output use the output_fname_func?
#     "fout_static": True  ,    # Should the output use the static_save_fpath?
# }
# BUILD = {
#     "cache_parent_path": os.path.dirname(MAIN_DIR),     # Alternate parent directory for the cache to be located in
#     "f_out_parent_path": os.path.dirname(MAIN_DIR),     # Alternate parent directory for the file output to be located
#     "output_fname_func": lambda : f"{hex_uuid()}.json", # Callable used to generate the output filename
#     "extra_save_kwargs": {'indent': 2},                 # Extra kwargs to pass to the `save_json` function
#     "static_save_fpath": "/Users/greysonturner/2026_code/diesel/output/aggregator.json"
# }


# def run_aggregator(cache_dir=None) -> tuple[float, Any]:
#     _time_start = time.time()
#     aggr_results = aggregate(cache_dir=cache_dir)
#     time_diff = time.time() - _time_start
    
#     return time_diff, aggr_results







# # if __name__ == "__main__":
# #     cache_dir       = None 
# #     output_dir      = Path("")






# if __name__ == "__main__":
#     # Checks with FLAGS
#     cache_dir = None
#     if FLAGS["cache_files"]:
#         if FLAGS["alt_caching"]:
#             cache_dir = os.path.join(BUILD["cache_parent_path"], "cache")
#         else: 
#             cache_dir = os.path.join(MAIN_DIR, "cache")
#         if not os.path.exists(cache_dir):
#             if not FLAGS["fix_missing"]: 
#                 raise FileNotFoundError(cache_dir)
#             os.mkdir(cache_dir)
#         if not os.path.isdir(cache_dir):
#             raise NotADirectoryError(cache_dir)
    
#     output_dir = os.path.join(MAIN_DIR, "output")

#     if FLAGS["does_output"]:
#         if FLAGS["fout_static"]:
#             output_dir = os.path.dirname(BUILD["static_save_fpath"])
        
#         if not os.path.exists(output_dir):
#             if not FLAGS["fix_missing"]:
#                 raise FileNotFoundError(output_dir)
#             os.mkdir(output_dir)
#         if not os.path.isdir(output_dir):
#             raise NotADirectoryError(output_dir)

    
#     aggr_time, aggr_results = run_aggregator(cache_dir=cache_dir)

#     if FLAGS["print_timed"]:
#         print(f"Aggregation took: {aggr_time:.2f} seconds")
        
#     if FLAGS["does_output"]:
#         if FLAGS["using_fname"]:
#             fout_path = os.path.join(output_dir, BUILD["output_fname_func"]())
#         else:
#             fout_path = BUILD["static_save_fpath"]
#         save_json(fout_path, aggr_results, **BUILD["extra_save_kwargs"])
#         print(f"Saved output to: '{fout_path}'")
#     else:
#         pass # result holds the data


# # ---  DOCUMENT STATUS ---
# # XXX: HEAVY WIP




#     # _timestart = time.time()
#     # #result = auto_aggregate(cache_dir=cache_dir)
#     # result = aggregate(cache_dir=cache_dir)
#     # _timestop  = time.time()
#     # print(f"Finished in: {_timestop - _timestart} seconds")