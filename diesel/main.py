import dearpygui.dearpygui as dpg

dpg.create_context()
dpg.create_viewport(title='ViewportTitle', width=1000, height=1000)

with dpg.window(label='WindowName', width=950, height=950):
    dpg.add_text('Example Text')
    

with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255), category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 1, 1, category=dpg.mvThemeCat_Core)


dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui() # while dpg.is_dearpygui_running(): dpg.render_dearpygui_frame()
dpg.destroy_context()