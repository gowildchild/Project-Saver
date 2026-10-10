# ==========================================================================
# Project Saver Module: Pluggable System Power Controller (shutdown.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import time
import subprocess
import module_library

# ─── MODULE SYSTEM MANIFEST REGISTRY ───
MODULE_MANIFEST = {
    "name": "shutdown",
    "display_name": "Shutdown Controller",
    "display_menu": "S[H]utdown Controller",
    "display_desc": "Manage machine shutdown state",
    "menu_shortcut": "h",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.30",
        "requires": "v0.0.76",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True,         # Sets availability for cloud installation/use
        "menu": 3
    },
    "autostart": False,            # Manually loaded via workspace hotkey selections
    "display_multi": [
        {
            "callback_key": "cancel_shutdown",
            "menu_shortcut": "c",
            "display_menu": "   [C] Cancel:",
            "display_desc": "Aborts any currently active scheduled countdowns.",
            "mask_bits": 3,
            "main_menu": False     # Hides this individual sub-command from cluttering the master root menu!
        },
        {
            "callback_key": "timed_shutdown",
            "menu_shortcut": "t",
            "display_menu": "   [T] Timed:",
            "display_desc": "Schedules machine shutdown sequence in minutes.",
            "mask_bits": 5,        # Bit 1 (Title) + Bit 4 (Live Value)
            "main_menu": False     # Keeps this option internal to the local power panel!
        },
        {
            "callback_key": "instant_shutdown",
            "menu_shortcut": "s",
            "menu_toggles": 3,
            "display_menu": "   [S] Shutdown Now:",
            "display_desc": "Triggers instant system power-down routine.",
            "mask_bits": 5,        # Bit 1 (Title) + Bit 4 (Live value tracking progress counts)
            "main_menu": False     # Isolated strictly inside the sub-menu environment!
        }
    ],
    "defaults": {
        "default_timer_minutes": "5",
        "safety_trigger_count": "3",
        "safety_trigger_shortcut": "s",
    }
}

STRIKE_STATE = {"current_count": 0}

def register_module_callbacks(server_reference=None):
    pass

# --- TARGET CODE MODIFICATION BLOCK ---
def get_live_display_value(callback_key, cli_dict=None):
    """
    Resolves active local runtime parameters dynamically on every frame pass, 
    feeding live string counters directly into the centralized workspace loop.
    """
    if callback_key == "timed_shutdown":
        timer_min = module_library.get_setting("shutdown", "default_timer_minutes", "5")
        return f"{timer_min} minutes"
        
    elif callback_key == "instant_shutdown":
        max_toggles = 3
        for opt in MODULE_MANIFEST.get("display_multi", []):
            if opt.get("callback_key") == "instant_shutdown":
                max_toggles = int(opt.get("menu_toggles", 3))
                
        current_progress = STRIKE_STATE["current_count"]
        return f"Requires {max_toggles} presses. Progress: [{current_progress}/{max_toggles}]"
    return ""

def handle_local_keyboard_action(user_input, cli_dict, manifest):
    """Executes target system command functions natively based on captured hotkeys."""
    global STRIKE_STATE
    is_windows = os.name == 'nt'
    
    if user_input != 's':
        STRIKE_STATE["current_count"] = 0

    if user_input == 'c':
        try:
            if is_windows: subprocess.Popen("shutdown /a", shell=True)
            else: subprocess.Popen(["shutdown", "-c"])
            return "🟢 SUCCESS: Active scheduled shutdowns cancelled successfully."
        except Exception as err:
            return f"🔴 ERROR: Failed to execute cancel sequence -> {err}"

    elif user_input == 't':
        try:
            timer_min_str = module_library.get_setting("shutdown", "default_timer_minutes", "5")
            timer_minutes = int(timer_min_str) if timer_min_str.isdigit() else 5
            seconds_target = timer_minutes * 60
            
            if is_windows: subprocess.Popen(f"shutdown /s /t {seconds_target}", shell=True)
            else: subprocess.Popen(["shutdown", "-h", f"+{timer_minutes}"])
            return f"🟢 SUCCESS: Scheduled system power down sequence active (+{timer_minutes}m)."
        except Exception as err:
            return f"🔴 ERROR: Failed to execute timed trigger -> {err}"

    elif user_input == 's':
        target_limit = 3
        for opt in manifest.get("display_multi", []):
            if opt.get("callback_key") == "instant_shutdown":
                target_limit = int(opt.get("menu_toggles", 3))

        STRIKE_STATE["current_count"] += 1
        if STRIKE_STATE["current_count"] >= target_limit:
            print("\n[!] Initializing forced machine power-down sequence now...")
            try:
                if is_windows: subprocess.Popen("shutdown /s /t 0", shell=True)
                else: subprocess.Popen(["shutdown", "-h", "now"])
            except: pass
            sys.exit(0)
        else:
            return f"⚠️ WARNING: Verification captured! Strike key [{STRIKE_STATE['current_count']}/{target_limit}] times to confirm powerdown down switch."
            
    return "Awaiting input power command option..."

def execute_interactive_menu(cli_dict, app_version, port_num):
    """Routes execution straight down into the centralized framework orchestrator loop."""
    import project_saver_x
    project_saver_x.run_interactive_workspace_loop(
        MODULE_MANIFEST, __file__, cli_dict, 
        get_live_display_value, handle_local_keyboard_action, 
        box_title="Shutdown Controller"
    )
        
if __name__ == "__main__":
    module_library.run_standalone_safely(MODULE_MANIFEST, execute_interactive_menu)
