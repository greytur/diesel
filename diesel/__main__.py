# diesel/__main__.py
# Shell Entry Point for Testing Script
# WARNING: CONTAINS RE-USED CODE, DO NOT EXECUTE UNTIL LINKED PROPERLY!

import os, time
# from modules.builder.old_builder import autobuilder
# from modules.builder.old_builder_v2 import builder
from build.aggregator import builder, autobuilder

from .tools import save_json, hex_uuid

MAIN_FILE = os.path.abspath(__file__)   # The `__main__.py` absolute file path
MAIN_DIR  = os.path.dirname(MAIN_FILE)  # The parent directory path of this file


FLAGS = {
    "cache_files": True, # Should we use the /cache directory to store file caches?
    "does_output": False, # Does the result get output to an output directory?
    "fix_missing": False, # Should missing directories (ie. cache and output) be created?
    "print_timed": True, # Do we print the time it took for the function to run?
}
BUILD = {
    "output_fname_func": lambda : f"{hex_uuid()}.json",
    "extra_save_kwargs": {'indent': 2}
}


if __name__ == "__main__":
    # Checks with FLAGS
    cache_dir  = None
    if FLAGS["cache_files"]:
        cache_dir  = os.path.join(MAIN_DIR, "cache")
        if not os.path.exists(cache_dir):
            if not FLAGS["fix_missing"]: 
                raise FileNotFoundError(cache_dir)
            os.mkdir(cache_dir)
        if not os.path.isdir(cache_dir):
            raise NotADirectoryError(cache_dir)
    
    output_dir = os.path.join(MAIN_DIR, "output")
    if FLAGS["does_output"]:
        if not os.path.exists(output_dir):
            if not FLAGS["fix_missing"]:
                raise FileNotFoundError(output_dir)
            os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            raise NotADirectoryError(output_dir)
    _timestart = time.time()
    #result = autobuilder(cache_dir=cache_dir)
    result = builder(cache_dir=cache_dir)
    _timestop  = time.time()
    if FLAGS["print_timed"]:
        print(f"Finished in: ({_timestop - _timestart})")
    if FLAGS["does_output"]:
        fout_path = os.path.join(output_dir, BUILD["output_fname_func"]())
        save_json(fout_path, result, **BUILD["extra_save_kwargs"])
        print(f"Saved output to: '{fout_path}'")
    else:
        pass # result holds the data


# ---  DOCUMENT STATUS ---
# XXX: HEAVY WIP