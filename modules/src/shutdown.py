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
    "menu_shortcut": "h",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.21",
        "requires": "v0.0.76",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True          # Sets availability for cloud installation/use
    },
    "autostart": False,            # Manually loaded via workspace hotkey selections
    "defaults": {
        "default_timer_minutes": "5",
        "safety_trigger_count": "3",
        "safety_trigger_shortcut": "s",
    }
}

def register_module_callbacks(server_reference=None):
    """Hooks into daemon server traffic if autostart is True."""
    pass

def execute_interactive_menu(cli_dict, app_version, port_num):
    """
    Fired instantly when the user hits 'M' -> selects 'shutdown', 
    or strikes the direct shortcut key 'H' inside the main menu.
    """
    import project_saver_config
    import project_saver_ui

    cli_dict, app_version, port_num = module_library.bootstrap_session(cli_dict, app_version, port_num)
    is_windows = os.name == 'nt'
    safety_counter = 0
    status_message = "Awaiting input command option..."

    while True:
        # 1. Clear terminal screen platform-natively
        os.system('cls' if is_windows else 'clear')

        # 2. Dynamically extract live config parameters with safe fallbacks
        timer_min_str = project_saver_config.SYSTEM_CONFIG.get("shutdown_default_timer_minutes", "5")
        safety_max_str = project_saver_config.SYSTEM_CONFIG.get("shutdown_safety_trigger_count", "3")
        
        try: timer_minutes = int(timer_min_str)
        except: timer_minutes = 5
        
        try: safety_max = int(safety_max_str)
        except: safety_max = 3

        # 3. Build the clean terminal panel UI overview
        shutdown_panel = [
            f"   Active Module Name:  {MODULE_MANIFEST['display_name']}",
            f"   Module Author:       {MODULE_MANIFEST['meta']['author']} ({MODULE_MANIFEST['meta']['version']})",
            "---",
            f"   [C] Cancel:          Aborts any currently active scheduled countdowns.",
            f"   [T] Timed:           Schedules machine shutdown sequence in {timer_minutes} minutes.",
            f"   [S] Shutdown Now:    Triggers instant system power-down routine.",
            f"                        (Requires {safety_max} presses. Current progress: [{safety_counter}/{safety_max}])",
            "---",
            f"   Status Indicator:    {status_message}",
            "---",
            "   [-] Press [Minus Key] to drop back out to Main Menu..."
        ]

        # 4. Render via your native box utility layout engine
        project_saver_ui.render_better_box(
            shutdown_panel, 
            title_str="Shutdown Controller", 
            box_width_override=72
        )

        # 5. Non-blocking keyboard state capture
        sys.stdout.write("\x1b[2K\r[Power] Ready for key: ")
        sys.stdout.flush()

        user_input = module_library.get_keystroke()
        if user_input != 's' and user_input != "":
            safety_counter = 0

        if user_input == "":
            time.sleep(0.05)
            continue        
        
        # ─── ACTION HOTKEY MATRIX DETECTIONS ───
        if user_input == '-':
            status_message = "Dropping out to main loop..."
            break

        elif user_input == 'c':
            try:
                if is_windows:
                    subprocess.Popen("shutdown /a", shell=True)
                else:
                    subprocess.Popen(["shutdown", "-c"])
                status_message = "🟢 SUCCESS: Active scheduled shutdowns cancelled successfully."
            except Exception as err:
                status_message = f"🔴 ERROR: Failed to execute cancel sequence -> {err}"

        elif user_input == 't':
            try:
                seconds_target = timer_minutes * 60
                if is_windows:
                    subprocess.Popen(f"shutdown /s /t {seconds_target}", shell=True)
                else:
                    subprocess.Popen(["shutdown", "-h", f"+{timer_minutes}"])
                status_message = f"🟢 SUCCESS: Scheduled system power down sequence active (+{timer_minutes}m)."
            except Exception as err:
                status_message = f"🔴 ERROR: Failed to execute timed trigger -> {err}"

        elif user_input == 's':
            safety_counter += 1
            # * [FIXED] SHIFT CONDITION MATRIX TO EXECUTE POWER DOWN ON THE EXACT TARGET COUNT VALUE MATCH
            if safety_counter >= safety_max:
                status_message = "🔥 CRITICAL: Safety limit cleared! Booting power-down loop..."
                os.system('cls' if is_windows else 'clear')
                print("\n[!] Initializing forced machine power-down sequence now...")
                
                try:
                    if is_windows: subprocess.Popen("shutdown /s /t 0", shell=True)
                    else: subprocess.Popen(["shutdown", "-h", "now"])
                except:
                    pass
                sys.exit(0)
            else:
                status_message = f"⚠️ WARNING: Verification captured! Strike key [{safety_counter}/{safety_max}] times to confirm powerdown down switch."

        # Throttles execution slightly to protect raw processor cycle usages
        time.sleep(0.05)
        
if __name__ == "__main__":
    import sys
    print(f"\n[+] Project Saver Extension.")
    sys.exit(0)
