import dearpygui.dearpygui as dpg
import yaml
import os
from ..tools import *
# # Check the package name used for relative resolutions
# print(f"Current Package: {__package__}")

# # Check the physical location of this file
# print(f"File Directory: {os.path.dirname(os.path.abspath(__file__))}")


INPUT  = "/Users/greysonturner/2026_code/diesel/input/test.yml"
OUTPUT = "/Users/greysonturner/2026_code/diesel/output/engine.txt"

fdata = read_file(INPUT)

data = yaml.safe_load(fdata)
save_json(OUTPUT, data, indent=2)

# NOTE: MUST VALIDATE DATA VIA JSON_SCHEMA BEFOREHAND



def item_type_lookup():
    pass



dpg.theme_component()


for instruction in data.keys():
    if instruction[0] == "$":
        instruction = instruction[1:]
    match instruction:
        case "themes":
            theme_dict = {
                identifier: {
                    
                } for identifier, data in (data[instruction].items())
            }


            for theme_identifier in (data[instruction]).keys():   # identifiers
                theme_dict[theme_identifier] = {
                    key: value for key, value in data[instruction][theme_identifier].items()
                }
                
                
                
                FLAG_is_global = False
                if theme_identifier[0] == "$":
                    if theme_identifier == "$global": FLAG_is_global = True
                    else: print("(LOGGING_INDEV)WARNING: A $ was PREFIXED incorrectly!")
                


