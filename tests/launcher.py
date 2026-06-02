# tests/launcher.py
import dearpygui.dearpygui as dpg
from diesel import config
import os
# Keep track of which input button opened the file browser
active_path_tag = None

def dropdown_callback(sender, app_data):
    """Triggered whenever a dropdown selection changes."""
    print(f"Dropdown '{sender}' changed value to: {app_data}")

def open_browser(sender, app_data, user_data):
    """Opens the directory browser and remembers which input requested it."""
    global active_path_tag
    active_path_tag = user_data  # This holds the tag of the matching input box
    dpg.show_item("directory_picker")

def path_selected_callback(sender, app_data):
    """Triggered when the user clicks 'OK' in the directory selector window."""
    global active_path_tag
    if active_path_tag and "file_path_name" in app_data:
        selected_path = app_data["file_path_name"]
        # Update the specific input box with the selected directory path
        dpg.set_value(active_path_tag, selected_path)
        print(f"Set {active_path_tag} to: {selected_path}")

def run_process():
    """Reads all input configurations when the submit button is clicked."""
    
    target_module = dpg.get_value("dropdown_1")
    cache_mode = dpg.get_value("dropdown_2")
    output_mode = dpg.get_value("dropdown_3")

    cache_dir = dpg.get_value("cache-dir")
    output_dir = dpg.get_value("output-dir")
    output_file = dpg.get_value("output-file")

    do_timing = dpg.get_value("do-timing")
    json_indent = dpg.get_value("json-indent")
    
    if cache_dir == str(config.DEFAULT_CACHE_DIR): 
        cache_dir = ""
    else: cache_dir = f"--cache-dir {cache_dir} "
    
    if output_dir == str(config.DEFAULT_OUTPUT_DIR): 
        output_dir = ""
    else: output_dir = f"--output-dir {output_dir} "

    if output_mode == "static":
        if target_module == "engine":
            if output_file == str(config.DEFAULT_ENGINE_OUTPUT_PATH):
                output_file = ""
            else:
                if os.path.exists(output_file):
                    output_file = f"--output-path {output_file} "
                else:
                    output_file = ""
        elif target_module == "aggregate":
            if output_file == str(config.DEFAULT_AGGREGATOR_OUTPUT_PATH): 
                output_file = ""
            else:
                if os.path.exists(output_file):
                    output_file = f"--output-path {output_file} "
                else:
                    output_file = ""
    else:
        output_file = ""

    if do_timing:
        do_timing = ""
    else:
        do_timing = " --no-timing"
    cmd = f"python ./diesel {target_module} --cache {cache_mode} {cache_dir}--output {output_mode} {output_file}--indent {json_indent}{do_timing}"
    print(f"RUNNING: `{cmd}`")
    os.system(
        cmd
    )



# 1. Initialize Dear PyGui Engine Context
dpg.create_context()

# 2. Define the Directory Selector Window Modal (Kept hidden until active)
dpg.add_file_dialog(
    directory_selector=True,
    show=False,
    id="directory_picker",
    callback=path_selected_callback,
    width=600,
    height=400
)

# 3. Construct Main Application Workspace Window
with dpg.window(label="Configuration Hub", width=625, height=500, no_close=True, tag="window-config",
                no_resize=True, no_move=True):
    
    # --- Section A: Dropdown Selection Menus ---
    dpg.add_text("Drop-down Configurations", color=[0, 180, 255])
    
    dpg.add_combo(
        label="Target Module", 
        items=["aggregate", "engine"], 
        tag="dropdown_1", 
        default_value="aggregate",
        callback=dropdown_callback
    )
    dpg.add_combo(
        label="Cache Mode", 
        items=["required", "create", "off"], 
        tag="dropdown_2", 
        default_value="required",
        callback=dropdown_callback
    )
    dpg.add_combo(
        label="Output Mode", 
        items=["static", "uuid", "none"], 
        tag="dropdown_3", 
        default_value="static",
        callback=dropdown_callback
    )
    
    dpg.add_spacer(height=15)
    dpg.add_separator()
    dpg.add_spacer(height=15)
    
    # --- Section B: Path Inputs with Browse Buttons ---
    dpg.add_text("File Path Configurations", color=[0, 180, 255])
    
    # Generate 5 clean rows containing an input field and a browse directory button side-by-side
    with dpg.group(horizontal=True):
        dpg.add_text("Cache Directory:  ")
        dpg.add_input_text(width=275, tag="cache-dir", hint="/path/to/folder...", 
                           default_value=str(config.DEFAULT_CACHE_DIR))
        dpg.add_button(label="Browse Path", callback=open_browser, user_data="cache-dir")
    with dpg.group(horizontal=True):
        dpg.add_text("Output Directory: ")
        dpg.add_input_text(width=275, tag="output-dir", hint="/path/to/folder...", 
                           default_value=str(config.DEFAULT_OUTPUT_DIR))
        dpg.add_button(label="Browse Path", callback=open_browser, user_data="output-dir")
    with dpg.group(horizontal=True):
        dpg.add_text("Output File Path: ")
        dpg.add_input_text(width=275, tag="output-file", hint="/path/to/a/file...", 
                           default_value="")
        dpg.add_button(label="Browse Path", callback=open_browser, user_data="output-file")

    dpg.add_spacer(height=15)
    dpg.add_separator()
    dpg.add_spacer(height=15)
    
    # --- Section B: Path Inputs with Browse Buttons ---
    dpg.add_text("Simple Configurations", color=[0, 180, 255])

    with dpg.group(horizontal=True):
        dpg.add_text("Timing Output: ")
        dpg.add_checkbox(default_value=True, tag="do-timing")
    
    with dpg.group(horizontal=True):
        dpg.add_text("JSON Indentation Level: ")
        dpg.add_input_int(default_value=2, tag="json-indent", min_clamped=True, min_value=0)
    
    dpg.add_spacer(height=20)
    # --- Section C: Global Action ---
    dpg.add_button(label="Process Configurations", width=-1, height=35, callback=run_process)

# 4. Finalize Window Viewport Configurations & Loop Ignition
dpg.create_viewport(title="Dear PyGui Custom Panel", width=650, height=570)
dpg.set_primary_window("window-config", False)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
