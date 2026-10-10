# ==========================================================================
# Project Saver Core: Cross-Platform Unified Shared Framework (project_saver_x.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import re
import configparser

status_prompt  = "Awaiting Input..."

def print_startup_banner(version_str):
    """
    Natively renders a stylized high-visibility ASCII art title banner budgeted 
    to fit cleanly inside a standard 105-column terminal row configuration.
    """
    try:
        if os.name == 'nt':
            os.system('mode con: cols=105 lines=30')    
        banner = [
            r"    ____                _           _       ____      by Gunther Voet        ",
            r"   |  _ \ _ __ ___     (_) ___  ___| |_    / ___|  __ ___   _____ _ __       ",
            r"   | |_) | '__/ _ \ _  | |/ _ \/ __| __|   \___ \ / _` \ \ / / _ \ '__|      ",
            r"   |  __/| | | (_) | |_| |  __/ (__| |_     ___) | (_| |\ V /  __/ |         ",
            r"   |_|   |_|  \___/ \___/ \___|\___|\__|   |____/ \__,_| \_/ \___|_|         "
        ]
    except:
        pass
    print("\n" + "═" * 94)
    for line in banner:
        print(line)
    print(" " * 40 + f"\nProject Saver {version_str}")
    print("═" * 94 + "\n")

def render_better_box(raw_lines_list: list, title_str: str = "Project Saver", box_width_override: int = 0):
    def get_visual_width(text_line: str) -> int:
        clean = re.sub(r'\033\[[0-9;]*m', '', str(text_line))
        width = 0
        for char in clean:
            o = ord(char)
            if o in (0xfe0f, 0x200d): continue
            if (0x1f300 <= o <= 0x1f9ff) or (0x2600 <= o <= 0x27bf) or (0x2b50 <= o <= 0x2b55): width += 2
            elif 0x4e00 <= o <= 0x9fff: width += 2
            else: width += 1
        return width

    print() 
    filtered_lines = [line for line in raw_lines_list if str(line).strip() != "---"]
    max_len = max((get_visual_width(line) for line in filtered_lines), default=len(title_str))
    target_width = box_width_override if box_width_override > 0 else 76
    box_width = max(target_width, max_len + 4)

    header_left = f"──┤ {title_str} ├"
    header_dash_fill = max(4, box_width - get_visual_width(header_left))
    print(f"┌{header_left}{'─' * header_dash_fill}┐")
    for line in raw_lines_list:
        clean_line = str(line).rstrip()
        if clean_line.strip() == "---":
            print(f"├{'─' * box_width}┤")
        else:
            current_width = get_visual_width(clean_line)
            padding_spaces = " " * (box_width - current_width - 2)
            print(f"│ {clean_line}{padding_spaces} │")
    print("└" + "─" * box_width + "┘")


def get_native_setting(module_name, key, default_value=""):
    """
    Natively parses the project_saver.cfg INI database directly from disk,
    allowing standalone compiled binary processes to securely map settings.
    """
    try:
        base_path = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        if base_path.lower().endswith("modules"):
            base_path = os.path.dirname(base_path)
            
        cfg_path = os.path.join(base_path, "project_saver.cfg")
        if not os.path.exists(cfg_path):
            return default_value
            
        config = configparser.ConfigParser()
        config.read(cfg_path, encoding="utf-8")
        
        section = module_name.lower()
        if config.has_option(section, key.lower()):
            return config.get(section, key.lower()).strip()
            
        if config.has_option("global", f"{section}_{key.lower()}"):
            return config.get("global", f"{section}_{key.lower()}").strip()
    except:
        pass
    return default_value

def run_interactive_workspace_loop(manifest, caller_file, cli_dict, get_live_val_callback, handle_key_callback, box_title="Pluggable Extension"):
    """
    Centralized orchestration loop engine that handles terminal clearing, builds dynamic 
    panel contents via display_multi registries, captures inputs, and triggers callbacks.
    """
    import time
    import sys
    import module_library
    
    # Isolate parent bootstrap framework overrides if present
    import module_library
    cli_dict, _, _ = module_library.bootstrap_session(cli_dict, "v0.0.1", 19763)
    
    status_message = "Awaiting Input..."
    
    
    while True:
        # 1. Clear terminal screen platform-natively using your shared tracking routine
        module_library.clear_screen_with_trace(manifest, caller_file)

        # 2. Build the structural layout context arrays dynamically
        panel_content = [
            f"   Active Module Name:  {manifest['display_name']}",
            "---",
        ]

        # 3. Dynamic row mapping driven entirely by your display_multi metadata rules
        for option in manifest.get("display_multi", []):
            bits = int(option.get("mask_bits", 0))
            if not bits:
                continue
                
            show_title = bool(bits & 1)
            show_desc  = bool(bits & 2)
            show_value = bool(bits & 4)
            
            display_m = option.get("display_menu", "")
            display_d = option.get("display_desc", "")
            
            live_val = ""
            if show_value and get_live_val_callback:
                live_val = get_live_val_callback(option.get("callback_key", ""), cli_dict)

            if not live_val and show_value:
                live_val = manifest.get("defaults", {}).get(option.get("callback_key", ""), "")

            if show_value and live_val:
                description_content = f"{display_d} -> ({live_val})"
            else:
                description_content = display_d
                
            if show_title and show_desc:
                panel_content.append(f"   {display_m:<24}{description_content}")
            elif show_title:
                panel_content.append(f"   {display_m}")
            elif show_desc:
                panel_content.append(f"   {description_content}")

        panel_content.append("---")
        panel_content.append(f"   Status Indicator:    {status_message}")
        panel_content.append("---")
        panel_content.append("   [-] Return to Main Menu...")

        # 4. Render the gathered panels using your audited visual width calculation engine
        render_better_box(panel_content, title_str=box_title, box_width_override=74)

        # 5. Non-blocking keyboard hardware state monitoring
        sys.stdout.write(f"\x1b[2K\r[{manifest['name'].capitalize()}] Awaiting Input: ")
        sys.stdout.flush()

        user_input = module_library.get_keystroke()
        if user_input == "":
            time.sleep(0.05)
            continue        
        
        if user_input in ['-', ' ', '\r', '\n', 'enter']:
            if os.name == 'nt':
                import msvcrt
                while msvcrt.kbhit():
                    try: msvcrt.getch()
                    except: pass
            else:
                import sys
                import select
                while select.select([sys.stdin], [], [], 0.0)[0]:
                    sys.stdin.readline()
            break

        # 6. Hand off key captures directly to the module interior handler to execute routines
        if handle_key_callback:
            callback_response = handle_key_callback(user_input, cli_dict, manifest)
            if callback_response == "BREAK_LOOP":
                break
            elif callback_response:
                status_message = callback_response

        time.sleep(0.05)

def format_human_readable_bytes(num_bytes: int) -> str:
    """
    Converts raw integer byte capacities into a human-readable metric string
    (e.g., 15243 -> '15.24 KB') optimized for terminal row metrics layouts.
    """
    try:
        val = float(num_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(val) < 1000.0: # Matches your exact base-10 metrics tracking lookups
                if unit == 'B':
                    return f"{int(val)} B"
                return f"{val:.2f} {unit}"
            val /= 1000.0
        return f"{val:.2f} PB"
    except:
        return f"{num_bytes} B"

def handle_unified_keyboard_routing(user_input, cli_dict, manifest, get_live_val_func=None, local_custom_callback=None):
    """
    Abstract data-driven keyboard routing engine that executes shared behaviors 
    (folder loading, upstream bubbling) based strictly on manifest action types.
    """
    import os
    import sys
    import time
    import subprocess

    # 1. Dynamically match the pressed hotkey against the display_multi option entries
    matched_option = None
    for option in manifest.get("display_multi", []):
        if option.get("menu_shortcut", "").lower() == str(user_input).lower():
            matched_option = option
            break

    # 2. Process generic framework action behaviors without hardcoded module keys
    if matched_option:
        action_type = matched_option.get("action_type", "").lower()
        call_id = matched_option.get("callback_key", "")

        if action_type == "open_folder":
            target_path = ""
            if get_live_val_func:
                target_path = get_live_val_func(call_id, cli_dict)
            if not target_path:
                target_path = os.path.abspath(manifest.get("defaults", {}).get(call_id, ""))
                
            print(f"\n[*] Opening directory workspace: {target_path}")
            if not os.path.exists(target_path):
                os.makedirs(target_path, exist_ok=True)
                
            if os.name == 'nt': subprocess.Popen(f'explorer.exe "{target_path}"')
            elif sys.platform == 'darwin': subprocess.Popen(['open', target_path])
            else: subprocess.Popen(['xdg-open', target_path])
            time.sleep(1.2)
            return f"{status_prompt}"

        elif action_type == "forward_upstream":
            print(f"\n[*] Forwarding hotkey '{user_input.upper()}' upstream to parent monitor engine context...")
            time.sleep(0.2)
            
            main_module_ref = sys.modules.get('__main__')
            if main_module_ref:
                try:
                    if hasattr(main_module_ref, 'execute_interactive_dashboard_monitor'):
                        pass 
                except Exception as route_err:
                    print(f"[-] Upstream key injection routing failed: {route_err}")
                    time.sleep(1.5)
            return f"{status_prompt}"

    # 3. Process standard parent dashboard global fallback keys safely
    if user_input in ['i', 'r']:
        print(f"\n[*] Forwarding global override key '{user_input.upper()}' upstream...")
        time.sleep(0.2)
        return f"{status_prompt}"

    # 4. Offload custom logic execution threads straight to the localized module handler
    if local_custom_callback:
        return local_custom_callback(user_input, cli_dict, manifest)

    return f"{status_prompt}"
