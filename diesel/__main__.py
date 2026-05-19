# diesel/__main__.py
# Shell Entry Point for Testing Script
# WARNING: CONTAINS RE-USED CODE, DO NOT EXECUTE UNTIL LINKED PROPERLY!
from typing import Any
import os, time
from pathlib import Path
# from modules.builder.old_builder import autobuilder
# from modules.builder.old_builder_v2 import builder
from builder.aggregator import aggregate

from tools import save_json, hex_uuid
global result
MAIN_FILE  = os.path.abspath(__file__)   # The `__main__.py` absolute file path
MAIN_DIR   = os.path.dirname(MAIN_FILE)  # The parent directory path of this file (diesel/)

FLAGS = {
    "cache_files": True  ,    # Should we use the /cache directory to store file caches?
    "does_output": True  ,    # Does the result get output to an output directory?
    "fix_missing": False ,    # Should missing directories (ie. cache and output) be created?
    "print_timed": True  ,    # Do we print the time it took for the function to run?
    "alt_caching": True  ,    # Should we use the cache parent path BUILD option?
    "using_fname": False ,    # Should the output use the output_fname_func?
    "fout_static": True  ,    # Should the output use the static_save_fpath?
}
BUILD = {
    "cache_parent_path": os.path.dirname(MAIN_DIR),     # Alternate parent directory for the cache to be located in
    "f_out_parent_path": os.path.dirname(MAIN_DIR),     # Alternate parent directory for the file output to be located
    "output_fname_func": lambda : f"{hex_uuid()}.json", # Callable used to generate the output filename
    "extra_save_kwargs": {'indent': 2},                 # Extra kwargs to pass to the `save_json` function
    "static_save_fpath": "/Users/greysonturner/2026_code/diesel/output/aggregator.json"
}


def run_aggregator(cache_dir=None) -> tuple[float, Any]:
    _time_start = time.time()
    aggr_results = aggregate(cache_dir=cache_dir)
    time_diff = time.time() - _time_start
    
    return time_diff, aggr_results







# if __name__ == "__main__":
#     cache_dir       = None 
#     output_dir      = Path("")






if __name__ == "__main__":
    # Checks with FLAGS
    cache_dir = None
    if FLAGS["cache_files"]:
        if FLAGS["alt_caching"]:
            cache_dir = os.path.join(BUILD["cache_parent_path"], "cache")
        else: 
            cache_dir = os.path.join(MAIN_DIR, "cache")
        if not os.path.exists(cache_dir):
            if not FLAGS["fix_missing"]: 
                raise FileNotFoundError(cache_dir)
            os.mkdir(cache_dir)
        if not os.path.isdir(cache_dir):
            raise NotADirectoryError(cache_dir)
    
    output_dir = os.path.join(MAIN_DIR, "output")

    if FLAGS["does_output"]:
        if FLAGS["fout_static"]:
            output_dir = os.path.dirname(BUILD["static_save_fpath"])
        
        if not os.path.exists(output_dir):
            if not FLAGS["fix_missing"]:
                raise FileNotFoundError(output_dir)
            os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            raise NotADirectoryError(output_dir)

    
    aggr_time, aggr_results = run_aggregator(cache_dir=cache_dir)

    if FLAGS["print_timed"]:
        print(f"Aggregation took: {aggr_time:.2f} seconds")
        
    if FLAGS["does_output"]:
        if FLAGS["using_fname"]:
            fout_path = os.path.join(output_dir, BUILD["output_fname_func"]())
        else:
            fout_path = BUILD["static_save_fpath"]
        save_json(fout_path, aggr_results, **BUILD["extra_save_kwargs"])
        print(f"Saved output to: '{fout_path}'")
    else:
        pass # result holds the data


# ---  DOCUMENT STATUS ---
# XXX: HEAVY WIP




    # _timestart = time.time()
    # #result = auto_aggregate(cache_dir=cache_dir)
    # result = aggregate(cache_dir=cache_dir)
    # _timestop  = time.time()
    # print(f"Finished in: {_timestop - _timestart} seconds")