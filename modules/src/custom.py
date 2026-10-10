# ==========================================================================
# Project Saver Module: Custom User Extension Template (custom.py)
# Instructions: Copy this file, adjust manifests, and append custom loops.
# ==========================================================================
import os
import sys
import time
import module_library

MODULE_MANIFEST = {
    "name": "custom",
    "display_name": "User Custom Module",
    "display_menu": "[C]ustom Module",
    "menu_shortcut": "c",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.37",
        "requires": "v0.0.76",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True,         # Sets availability for cloud installation/use
        "menu": 3
    },
    "autostart": False,            # Set to True if it needs to run background tasks on boot
    "display_profile": {
        "box_style_mask": 1028,    # 1024 (Force 40-Col) + 4 (Teletext Mosaic Border Accent Profile)
        "align_mask": 0,           # Inline Default
        "fg_color": "FFFFFF",      # Teletext Foreground White
        "bg_color": "000000",      # Teletext Background Black
        "input_y": 12,             # Absolute Row placement coordinate for text boxes
        "input_x": 3,              # Absolute Column placement coordinate for text boxes
        "box_width": 40            # Fixed width target limit constraints
    },    
    "display_multi": [
        {
            "callback_key": "custom_string_setting",
            "menu_shortcut": "",
            "display_menu": "Parsed String Setting:",
            "display_desc": "Active user string parameter text string",
            "mask_bits": 5,         # Bit 1 (Title) + Bit 4 (Live Value)
            "display_xy": "6,4", 
            "display_color": "e0",
            "action_type": "custom"
        },
        {
            "callback_key": "custom_integer_flag",
            "menu_shortcut": "",
            "display_menu": "Parsed Integer Flag:",
            "display_desc": "Active numeric iteration count limit",
            "mask_bits": 5,         # Bit 1 (Title) + Bit 4 (Live Value)
            "display_xy": "9,4",
            "display_color": "b0",
            "action_type": "custom"
        },
        {
            "callback_key": "custom_user_action",
            "menu_shortcut": "a",
            "display_menu": "   [A] Action Trigger:",
            "display_desc": "Execute your custom script routine workspace.",
            "mask_bits": 3,         # Bit 1 (Title) + Bit 2 (Desc)
            "display_xy": "12,4",
            "display_color": "c0",
            "action_type": "custom"
        }
    ],    
    "defaults": {
        "custom_string_setting": "hello_world",
        "custom_integer_flag": "10"
    }
}

def register_module_callbacks(server_reference=None):
    """
    Executed on boot if autostart is True.
    Allows pluggable extensions to hook into server traffic pipelines.
    """
    pass

def get_live_display_value(callback_key, cli_dict=None):
    """
    Resolves active local parameters dynamically for the centralized loop tracer.
    """
    if callback_key == "custom_string_setting":
        return module_library.get_setting("custom", "custom_string_setting", "hello_world")
    elif callback_key == "custom_integer_flag":
        return module_library.get_setting("custom", "custom_integer_flag", "10")
    return ""

def handle_local_keyboard_action(user_input, cli_dict, manifest):
    """
    Localized micro-callback managing only your custom user execution routines.
    """
    import project_saver_x
    
    def execute_custom_template_triggers(key, c_dict, mf):
        import project_saver_config
        
        if key == 'a':
            # Extract target coordinates directly out of our customized dictionary option mapping
            target_xy = "14,4"  # Default prompt position row boundary
            for option in mf.get("display_multi", []):
                if option.get("callback_key") == "custom_user_action":
                    target_xy = option.get("display_xy", "14,4")
            
            y_val, x_val = map(int, target_xy.split(","))
            
            new_val = project_saver_x.draw_bitmask_input_field(
                prompt="Enter String Setting", 
                y=y_val + 2, # Space offset underneath option text
                x=x_val, 
                max_chars=20
            )
            if new_val:
                project_saver_config.SYSTEM_CONFIG["custom_custom_string_setting"] = str(new_val)
                project_saver_config.save_config_file("project_saver.cfg", c_dict)
                return f"🟢 SAVED: Updated setting to -> '{new_val}'!"
            return "⚠️ WARNING: Value empty. Skip save pass."
        return "Custom skeleton module active. Ready for user scripts."

    return project_saver_x.handle_unified_keyboard_routing(
        user_input, cli_dict, manifest,
        get_live_display_value, local_custom_callback=execute_custom_template_triggers
    )

def execute_interactive_menu(cli_dict, app_version, port_num):
    """Routes execution straight down into the centralized framework orchestrator loop."""
    import project_saver_x
    # 1024 (Force 40-Col) + 4 (Teletext Mosaic Border Accent Profile) = 1028
    project_saver_x.run_interactive_workspace_loop(
        MODULE_MANIFEST, __file__, cli_dict, 
        get_live_display_value, handle_local_keyboard_action, 
        box_title="Custom Module"
    )

def execute_old_interactive_menu(cli_dict, app_version, port_num):
    """Routes execution straight down into the centralized framework orchestrator loop."""
    import project_saver_x
    project_saver_x.run_interactive_workspace_loop(
        MODULE_MANIFEST, __file__, cli_dict, 
        get_live_display_value, handle_local_keyboard_action, 
        box_title="Custom Module"
    )
        
if __name__ == "__main__":
    module_library.run_standalone_safely(MODULE_MANIFEST, execute_interactive_menu)
