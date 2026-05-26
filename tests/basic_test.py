# tests/basic_test.py
import diesel as dsl

dsl.create_context()
dsl.create_viewport(title='ViewportTitle', width=1000, height=1000)

with dsl.window(label='WindowName', width=950, height=950):
    dsl.add_text('Example Text')
    

with dsl.theme() as global_theme:
    with dsl.theme_component(dsl.mvAll):
        dsl.add_theme_color(dsl.mvThemeCol_Text, (255, 255, 255, 255), category=dsl.mvThemeCat_Core)
        dsl.add_theme_style(dsl.mvStyleVar_WindowPadding, 1, 1, category=dsl.mvThemeCat_Core)

dsl.setup_dearpygui()
dsl.show_viewport()
dsl.start_dearpygui() # while dsl.is_dearpygui_running(): dsl.render_dearpygui_frame()
dsl.destroy_context()