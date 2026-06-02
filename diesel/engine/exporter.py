import pathlib

import dearpygui.dearpygui as dpg

# 1. Initialize the Dear PyGui context
def sample_program():

# 2. Main Window Structure
    with dpg.window(label="Sample Dashboard", width=500, height=550, no_close=True):
        
        # Text Widgets
        dpg.add_text("Welcome to Dear PyGui", color=[0, 255, 0])
        dpg.add_text("This is standard description text showing layout capability.")
        
        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=10)
        
        # Input Text Fields
        dpg.add_input_text(label="Input Box", default_value="Sample input text")
        dpg.add_input_text(label="Password Box", password=True, default_value="secret123")
        
        dpg.add_spacer(height=10)
        
        # Numeric Inputs & Sliders
        dpg.add_input_int(label="Integer Input", default_value=42)
        dpg.add_slider_float(label="Float Slider", default_value=75.5, min_value=0.0, max_value=100.0)
        
        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=10)
        
        # Selection & Choice Widgets
        dpg.add_checkbox(label="Toggle Option A", default_value=True)
        dpg.add_checkbox(label="Toggle Option B", default_value=False)
        
        dpg.add_spacer(height=5)
        
        dpg.add_radio_button(items=["First Choice", "Second Choice", "Third Choice"], default_value="First Choice")
        
        dpg.add_spacer(height=5)
        
        dpg.add_combo(
            label="Dropdown Menu", 
            items=["Selection 1", "Selection 2", "Selection 3"], 
            default_value="Selection 1"
        )
        
        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=10)
        
        # Action Buttons
        with dpg.group(horizontal=True):
            dpg.add_button(label="Left Action", width=120)
            dpg.add_button(label="Right Action", width=120)
            
        dpg.add_spacer(height=10)
        dpg.add_button(label="Global Submit Button", width=-1, height=35)

    # 3. Viewport and Main Loop Launch
    dpg.create_viewport(title="Basic Widget Reference", width=530, height=580)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

'''
NOTES:
    export role:
    diesel/diesel/engine/exporter.py
    
    package lives in .../diesel/diesel
    package must have stubs
    package stubs?
                    .../diesel/diesel-stubs

'''