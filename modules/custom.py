# ==========================================================================
# Project Saver Module: Custom User Extension Template (custom.py)
# Instructions: Copy this file, adjust manifests, and append custom loops.
# ==========================================================================
import os
import sys
import time

# ─── MODULE SYSTEM MANIFEST REGISTRY ───
MODULE_MANIFEST = {
    "name": "custom",
    "display_name": "User Defined Extension",
    "display_menu": "[C]ustom Extension",
    "menu_shortcut": "c",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.5",
        "requires": "v0.0.78",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True          # Sets availability for cloud installation/use
    },
    "autostart": False,            # Set to True if it needs to run background tasks on boot
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

def execute_interactive_menu(cli_dict, app_version, port_num):
    """
    Fired instantly when the user hits 'M' -> selects 'custom', 
    or strikes the direct shortcut key 'C' inside the main menu.
    """
    import project_saver_config
    import project_saver_ui

    status_message = "Custom skeleton module active. Ready for user scripts."

    while True:
        # 1. Clear terminal screen platform-natively
        os.system('cls' if os.name == 'nt' else 'clear')

        # 2. Extract user configuration parameters safely out of the section block
        user_str = project_saver_config.SYSTEM_CONFIG.get("custom_custom_string_setting", "hello_world")
        user_int = project_saver_config.SYSTEM_CONFIG.get("custom_custom_integer_flag", "10")

        # 3. Build terminal box UI display list
        custom_panel = [
            f"   Active Module Name:  {MODULE_MANIFEST['display_name']}",
            f"   Module Version:      {MODULE_MANIFEST['meta']['version']} by {MODULE_MANIFEST['meta']['author']}",
            "---",
            f"   Parsed String Setting: {user_str}",
            f"   Parsed Integer Flag  : {user_int}",
            "---",
            f"   Status Indicator:    {status_message}",
            "---",
            "   [A] Action Trigger:  Execute your custom script payload loop.",
            "   [-] Press [Minus Key] to drop back out to Main Menu..."
        ]

        # 4. Render via your native box utility layout engine
        project_saver_ui.render_better_box(
            custom_panel, 
            title_str="User Custom Extension Workspace", 
            box_width_override=72
        )

        # 5. Non-blocking keyboard state monitoring
        sys.stdout.write("\x1b[2K\r[🛠️ Custom] Ready for key: ")
        sys.stdout.flush()

        user_input = ""
        if os.name == 'nt':
            import msvcrt
            if msvcrt.kbhit():
                user_input = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            else:
                time.sleep(0.05)
                continue
        else:
            import select
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not ready:
                continue
            user_input = sys.stdin.readline().strip().lower()

        if user_input == "":
            time.sleep(0.05)
            continue        
        
        # ─── HOTKEY MATRIX ACTIONS ───
        if user_input == '-':
            break
            
        elif user_input == 'a':
            # Place your custom processing routines right here!
            status_message = f"🟢 SUCCESS: Action triggered at {time.strftime('%H:%M:%S')}!"
            time.sleep(1.0)
            
        time.sleep(0.05)
