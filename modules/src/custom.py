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
        "version": "v0.0.39",
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
        profile = mf.get("display_profile", {})
        
        if key == 'a':
            target_xy = "14,4"
            for option in mf.get("display_multi", []):
                if option.get("callback_key") == "custom_user_action":
                    target_xy = option.get("display_xy", "14,4")
            
            y_val, x_val = map(int, target_xy.split(","))
            
            new_val = project_saver_x.draw_bitmask_input_field(
                prompt="Enter String Setting", 
                y=y_val + 2, 
                x=x_val, 
                max_chars=20
            )
            if new_val:
                # Natively write straight to the shared INI via the cross-library!
                project_saver_x.set_native_setting("custom", "custom_string_setting", new_val)
                return f"🟢 SAVED: Updated setting to -> '{new_val}'!"
            return "⚠️ WARNING: Value empty. Skip save pass."

        elif key == 'e':
            try:
                import json
                export_dir = os.path.abspath(c_dict.get('export_folder') or "")
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir, exist_ok=True)
                
                backup_filename = f"manifest_backup_{mf.get('name', 'custom')}.json"
                backup_path = os.path.join(export_dir, backup_filename)
                
                with open(backup_path, "w", encoding="utf-8") as bf:
                    json.dump(mf, bf, indent=4)
                return f"🟢 EXPORTED: Manifest saved to {backup_filename}!"
            except Exception as err:
                return f"🔴 ERROR: Export profile failed -> {err}"

        elif key == 'i':
            try:
                import json
                export_dir = os.path.abspath(c_dict.get('export_folder') or "")
                backup_filename = f"manifest_backup_{mf.get('name', 'custom')}.json"
                backup_path = os.path.join(export_dir, backup_filename)
                
                if not os.path.exists(backup_path):
                    return f"⚠️ FAILED: Backup file not found at export destination."
                
                with open(backup_path, "r", encoding="utf-8") as bf:
                    loaded_manifest = json.load(bf)
                
                global MODULE_MANIFEST
                MODULE_MANIFEST.update(loaded_manifest)
                
                # Update persistent settings based on loaded values safely
                for opt in loaded_manifest.get("display_multi", []):
                    key_id = opt.get("callback_key")
                    if key_id:
                        val = loaded_manifest.get("defaults", {}).get(key_id, "")
                        project_saver_x.set_native_setting("custom", key_id, val)
                        
                return f"🟢 IMPORTED: Manifest state re-indexed successfully!"
            except Exception as err:
                return f"🔴 ERROR: Import profile failed -> {err}"
                
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
