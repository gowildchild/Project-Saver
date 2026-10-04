# ==========================================================================
# Project Saver: Modular System to (currently) archive sites and (AI) code.
# Copyright (c) 2002-2026 by Gunther Voet (GoWildchild) All Rights Reserved. 
# Released under strict Non-Commercial Open-Source License terms.   (beta4)
# ==========================================================================
import os
import re
import sys
import time
import json
import secrets
import argparse
import threading
import platform
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.parser import BytesParser
from bs4 import BeautifulSoup

from project_saver_archive import process_html_content
from project_saver_update import check_for_startup_update_and_run, check_and_perform_update
import project_saver_config
import project_saver_ui
import project_saver_daemon
import project_saver_modules

VERSION = "v0.0.81-alpha"
PORT = 19763
EXPECTED_TOKEN = ""
CONSOLE_LOCK = threading.Lock()
REPO_OWNER = "gowildchild"
REPO_NAME = "Project-Saver"
ALLOWED_PROFILES = ["Auto","code_dev","web_article"]
ALLOWED_FORMATS = ["Markdown","HTML","PDF"]
LATEST_AVAILABLE_VERSION = None
	
def execute_interactive_dashboard_monitor(httpd_server_reference):
    """Processes server traffic and terminal hotkeys sequentially without high-speed loop cascades."""
    import sys
    import os
    import subprocess
    import time

    global VERSION, LATEST_AVAILABLE_VERSION, REPO_OWNER, REPO_NAME, CLI_ARGS

    quit_press_counter = 0
    update_press_counter = 0
    latest_discovered_version = None
    
    prompt_visible = False
    
    cli_dict = vars(CLI_ARGS)
    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

    while True:
        try:
            # 1. Non-blocking network check. Timeout = 0.1 prevents a frozen interface.
            httpd_server_reference.timeout = 0.1
            httpd_server_reference.handle_request()

            # 2. Render the static interface status line exactly ONCE
            if not prompt_visible:
                if quit_press_counter > 0:
                    sys.stdout.write(f"\x1b[2K\r⚠️ Press [Q]uit again [{quit_press_counter}/3] times to escape Kansas...")
                elif update_press_counter == 1:
                    v_msg = f" {latest_discovered_version}" if latest_discovered_version else ""
                    sys.stdout.write(f"\x1b[2K\rPress [U]pdate again to execute automated upgrade to{v_msg}...")
                else:
                    sys.stdout.write("\x1b[2K\r[?] Ready for hotkey: ")
                sys.stdout.flush()
                prompt_visible = True

            # 3. Non-blocking keyboard hardware capture loop
            user_triggered_key = ""
            if os.name == 'nt':
                import msvcrt
                if msvcrt.kbhit():
                    user_triggered_key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    while msvcrt.kbhit():
                        msvcrt.getch()
                else:
                    # Throttles loop execution when completely idle to protect CPU cores
                    time.sleep(0.05)
                    continue
            else:
                import select
                ready, _, _ = select.select([sys.stdin], [], [], 0.05)
                if not ready:
                    continue
                user_triggered_key = sys.stdin.readline().strip().lower()

            # Reset prompt state on any key interaction to allow message repainting
            if user_triggered_key != "":
                prompt_visible = False

            # ─── HOTKEY MATRIX ACTIONS ───
            if user_triggered_key == 'e':
                # * [FIXED] Converted to underscore lookup to read configuration folder path
                export_path = os.path.abspath(cli_dict.get('export_folder') or "")
                print(f"\n[E] Export folder opened: {export_path}")
                if not os.path.exists(export_path):
                    os.makedirs(export_path, exist_ok=True)
                if os.name == 'nt': subprocess.Popen(f'explorer.exe "{export_path}"')
                elif sys.platform == 'darwin': subprocess.Popen(['open', export_path])
                else: subprocess.Popen(['xdg-open', export_path])

            elif user_triggered_key == 'i':
                print(f"\n[I] Import SingleFile JSON config folder opened: {script_base_dir}")
                if os.name == 'nt': subprocess.Popen(f'explorer.exe "{script_base_dir}"')
                elif sys.platform == 'darwin': subprocess.Popen(['open', script_base_dir])
                else: subprocess.Popen(['xdg-open', script_base_dir])

            elif user_triggered_key == 'r':
                check_and_perform_update(
                    VERSION, REPO_OWNER, REPO_NAME,
                    mode_override=8, 
                    resolve_token_callback=lambda path: project_saver_config.resolve_or_create_security_token(PORT, path)
                )
                cli_dict['token'] = project_saver_config.EXPECTED_TOKEN
                project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)

            elif user_triggered_key == 'f':
                current_fmt = cli_dict.get('export_format', 'markdown').lower()
                formats_lower = [f.lower() for f in ALLOWED_FORMATS]
                if current_fmt not in formats_lower:
                    current_fmt = "markdown"
                current_idx = formats_lower.index(current_fmt)
                next_idx = (current_idx + 1) % len(formats_lower)
                cli_dict['export_format'] = formats_lower[next_idx]

                if project_saver_config.SYSTEM_CONFIG.get("save_export_format_autosave") == "yes":
                    project_saver_config.save_config_file("project_saver.cfg", CLI_ARGS, VERSION, LATEST_AVAILABLE_VERSION)
                project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)

            elif user_triggered_key == 'p':
                current_prof = cli_dict.get('export_type', 'auto').lower()
                profiles_lower = [p.lower() for p in ALLOWED_PROFILES]
                if current_prof not in profiles_lower:
                    current_prof = "auto"
                current_idx = profiles_lower.index(current_prof)
                next_idx = (current_idx + 1) % len(profiles_lower)
                cli_dict['export_type'] = profiles_lower[next_idx]
                if project_saver_config.SYSTEM_CONFIG.get("save_export_type_autosave") == "yes":
                    project_saver_config.save_config_file("project_saver.cfg", CLI_ARGS, VERSION, LATEST_AVAILABLE_VERSION)
                project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)

            elif user_triggered_key == 'u':
                update_press_counter += 1
                if update_press_counter == 1:
                    latest_discovered_version = check_and_perform_update(
                        VERSION, REPO_OWNER, REPO_NAME,
                        mode_override=1
                    )
                    if not latest_discovered_version or latest_discovered_version == VERSION:
                        update_press_counter = 0
                elif update_press_counter >= 2:
                    print("\n[*] Update Started: Initializing secure system upgrade sequence...")
                    check_and_perform_update(
                        VERSION, REPO_OWNER, REPO_NAME,
                        mode_override=4
                    )
                    os._exit(0)
                continue

            elif user_triggered_key == 'q':
                quit_press_counter += 1
                if quit_press_counter >= 3:
                    print("\n[-] Shutting down: Project Saver API Server Daemon. Goodbye!")
                    os._exit(0)
                continue

            elif user_triggered_key == 's':
                print("\n[S] Manual Save: Writing current dashboard settings out to profile file...")
                project_saver_config.save_config_file("project_saver.cfg", CLI_ARGS, VERSION, LATEST_AVAILABLE_VERSION)
                project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)

            elif user_triggered_key == 'l':
                # * [ADDED] MANUAL PROFILE STATE RE-LOADER
                print("\n[L] Manual Load: Discarding active session drafts and re-indexing configuration...")
                project_saver_config.load_config_file("project_saver.cfg")
                if project_saver_config.SYSTEM_CONFIG.get("global_export-format"):
                    cli_dict['export_format'] = project_saver_config.SYSTEM_CONFIG["global_export-format"]
                if project_saver_config.SYSTEM_CONFIG.get("global_export-type"):
                    cli_dict['export_type'] = project_saver_config.SYSTEM_CONFIG["global_export-type"]
                project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)			

            elif user_triggered_key == 'm':
                manager_mod = project_saver_modules.ACTIVE_MODULES.get("manager")
                
                # ─── CASE A: COMPILED STANDALONE BINARY MANAGER OFFLOAD ───
                if isinstance(manager_mod, dict) and manager_mod.get("type") == "binary":
                    import subprocess
                    try:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"[*] Sub-process offload: Executing standalone binary -> MANAGER")
                        # Launch binary cleanly and block parent thread execution until sub-process exits cleanly
                        subprocess.run([manager_mod["path"]], check=True)
                    except Exception as bin_err:
                        print(f"\n[-] Standalone extension binary engine execution crashed: {bin_err}")
                        time.sleep(2)
                
                # ─── CASE B: FALLBACK FOR RAW PYTHON SCRIPT HANDLERS ───
                elif manager_mod and hasattr(manager_mod, "execute_interactive_menu"):
                    print("\n[*] Initializing Pluggable Package Manager sub-workspace panel...")
                    time.sleep(0.3)
                    try:
                        manager_mod.execute_interactive_menu(cli_dict, VERSION, PORT)
                    except Exception as err:
                        print(f"\n[-] Execution failed inside package manager framework: {err}")
                        time.sleep(2)
                else:
                    print("\n⚠️ WARNING: Manager module extension asset not found or disabled.")
                    time.sleep(1.5)
                
                # * [FIXED] REALIGNED REDRAW METHOD CALL TO PREVENT ATTRIBUTE LOOKUP CRASHES
                project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)
				
            if user_triggered_key not in ['q', 'u'] and user_triggered_key != "":
                quit_press_counter = 0
                update_press_counter = 0

        except KeyboardInterrupt:
            print("\n[-] Shutting down Project Saver API Server Daemon cleanly.")
            os._exit(0)


if __name__ == "__main__":
    print(f"\n[*] Project Saver {VERSION} Starting up, Please wait for system to be ready...")
    if os.name == 'nt':
        os.system('mode con: cols=105 lines=30')
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

    parser = argparse.ArgumentParser(
        description="Project Saver Server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    if platform.system().lower() == "windows":
        default_export_dir = os.path.join(os.environ["USERPROFILE"], "Documents", "Project-Saver", "export")
    else:
        default_export_dir = os.path.join(os.path.expanduser("~"), "Documents", "Project-Saver", "export")

    parser.add_argument("--export-folder", default=default_export_dir, help=f"Target base folder path where files will be written. (Default: {default_export_dir})")
    parser.add_argument("--export-format", default="markdown", help="Comma-separated dumping targets: markdown, html, pdf. (Default: markdown)")
    parser.add_argument("--export-type", default="auto", choices=["auto", "code", "web"], help="Parsing layout configuration profile strategy. (Default: auto)")
    parser.add_argument("--remote-address", default="", help="Turns runtime engine into proxy router. (Default: None)")
    parser.add_argument("--auto", type=int, nargs='?', const=5, default=None, help="Enables automated execution timeout duration.")
    parser.add_argument("--config", default="", help="Load options from a custom configuration text file.")
    parser.add_argument("--config-save", default="", help="Save setup flags into configuration profile text file.")
    parser.add_argument("--about", action="store_true", help="Displays developer credits and exit.")
    parser.add_argument("--update", action="store_true", help="Queries GitHub downloads update binary and exit.")
    parser.add_argument("--chosen-editor", default="system_default", choices=["system_default", "obsidian", "vscode", "marktext"], help="Preferred markdown viewer/editor launcher link tool. (Default: system_default)")
    parser.add_argument("--module", nargs='+', help="Executes pluggable extension sub-commands layout routing entries.")
    temp_args = sys.argv[1:]
    
    # ─── 2. DYNAMICALLY ISOLATE THE ACTIVE CONFIGURATION FILENAME ───
    active_cfg_profile = "project_saver.cfg"
    if "--config" in temp_args:
        try:
            c_idx = temp_args.index("--config")
            if c_idx + 1 < len(temp_args):
                active_cfg_profile = temp_args[c_idx + 1]
        except Exception:
            pass

    # ─── 3. COMBINE ARRAYS IN CORRECT OVERRIDE PRIORITY LAYER ORDER ───
    # Configuration options are evaluated first, terminal entries come LAST to explicitly override them
    loaded_file_args = project_saver_config.load_config_file(active_cfg_profile) if os.path.exists(active_cfg_profile) else []
    combined_args = loaded_file_args + temp_args
    CLI_ARGS = parser.parse_args(combined_args)
    cli_dict = vars(CLI_ARGS)

    # ─── 4. Add Modules ───
    project_saver_modules.bootstrap_and_discover_modules(cli_dict, VERSION, PORT)
    if cli_dict.get("module"):
        project_saver_modules.handle_module_cli_commands(cli_dict["module"], cli_dict, VERSION, PORT)
        sys.exit(0)

    # ─── 5. EXECUTE OPERATIONAL TASKS USING SAFE DIRECTORY LOOKUPS ───
    if cli_dict.get("about"):
        about_data = [
            f"Project Saver {VERSION} - Local & Remote Web Scraping Daemon",
            "---",
            "🛠️ Developer: Gunther Voet",
            "📜 License: Open Source (AGPL-3.0 license)",
            "🌐 Repository: https://github.com/gowildchild/Project-Saver/",
            "---",
            "Designed to cleanly archive browser sessions, code repositories",
            "and web documentation directly into structured Markdown files,",
            "raw backups, or professional PDF layouts."
        ]
        project_saver_ui.render_better_box(about_data, title_str="About \"Project Saver\"", box_width_override=70)
        sys.exit(0)

    if cli_dict.get("update"):
        check_and_perform_update(VERSION, REPO_OWNER, REPO_NAME, mode_override=7)
        sys.exit(0)

    if cli_dict.get("config_save"):
        project_saver_config.save_config_file(
            cli_dict["config_save"], 
            CLI_ARGS, 
            VERSION, 
            latest_version=None
        )
        sys.exit(0)

    project_saver_config.resolve_or_create_security_token(config_path=active_cfg_profile, port_num=PORT)
    LATEST_AVAILABLE_VERSION = check_and_perform_update(VERSION, REPO_OWNER, REPO_NAME, mode_override=1) or "v0.0.76-gunther"
    project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)
    check_for_startup_update_and_run(VERSION, REPO_OWNER, REPO_NAME, check_and_perform_update)
    project_saver_daemon.PORT = PORT
    project_saver_daemon.VERSION = VERSION
    project_saver_daemon.CLI_ARGS = CLI_ARGS
    project_saver_daemon.LATEST_AVAILABLE_VERSION = LATEST_AVAILABLE_VERSION
    project_saver_daemon.execute_interactive_dashboard_monitor = execute_interactive_dashboard_monitor
    project_saver_daemon.run_server()
