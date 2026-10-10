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
        "version": "v0.0.34",
        "requires": "v0.0.76",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True,         # Sets availability for cloud installation/use
        "menu": 3
    },
    "autostart": False,            # Set to True if it needs to run background tasks on boot
    "display_multi": [
        {
            "callback_key": "custom_string_setting",
            "menu_shortcut": "",
            "display_menu": "Parsed String Setting:",
            "display_desc": "Active user string parameter text string",
            "mask_bits": 5,         # Bit 1 (Title) + Bit 4 (Live Value)
            "action_type": "custom"
        },
        {
            "callback_key": "custom_integer_flag",
            "menu_shortcut": "",
            "display_menu": "Parsed Integer Flag:",
            "display_desc": "Active numeric iteration count limit",
            "mask_bits": 5,         # Bit 1 (Title) + Bit 4 (Live Value)
            "action_type": "custom"
        },
        {
            "callback_key": "custom_user_action",
            "menu_shortcut": "a",
            "display_menu": "   [A] Action Trigger:",
            "display_desc": "Execute your custom script routine workspace.",
            "mask_bits": 3,         # Bit 1 (Title) + Bit 2 (Desc)
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
    
    # 1. First hand off standard behaviors (folder openings, global keys) to the core cross-library
    def execute_custom_template_triggers(key, c_dict, mf):
        if key == 'a':
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"\n[+] Executing custom module pipeline...")
            time.sleep(1.2)
            return f"🟢 SUCCESS: Action triggered at {time.strftime('%H:%M:%S')}!"
        return "Custom skeleton module active. Ready for user scripts."

    return project_saver_x.handle_unified_keyboard_routing(
        user_input, cli_dict, manifest,
        get_live_display_value, local_custom_callback=execute_custom_template_triggers
    )

def execute_interactive_menu(cli_dict, app_version, port_num):
    """Routes execution straight down into the centralized framework orchestrator loop."""
    import project_saver_x
    project_saver_x.run_interactive_workspace_loop(
        MODULE_MANIFEST, __file__, cli_dict, 
        get_live_display_value, handle_local_keyboard_action, 
        box_title="Custom Module"
    )
        
if __name__ == "__main__":
    module_library.run_standalone_safely(MODULE_MANIFEST, execute_interactive_menu)
