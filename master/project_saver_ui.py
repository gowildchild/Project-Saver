# project_saver_ui.py
import os
import sys
import re
import time
import subprocess
import project_saver_config
import project_saver_modules

def set_terminal_title(title_text, run_version, run_text):
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(f"{title_text} {run_version} - {run_text}")
    else:
        sys.stdout.write(f"\x1b]2;{title_text} {run_version} - {run_text}\x07")
        sys.stdout.flush()

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

def refresh_dashboard_view(cli_dict, app_version, port_num):
    """
    Clears the screen and renders the standard startup box with the most up-to-date active settings.
    """
    import os
    import sys
    import project_saver_config

    # Clear terminal window platform-natively (cls for Windows, clear for Linux/macOS)
    os.system('cls' if os.name == 'nt' else 'clear')

    def clean_ver(v_str):
        return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', str(v_str).lower())]	
	
    latest_available_version = project_saver_config.SYSTEM_CONFIG.get("update_version_newest") or "" 
    if latest_available_version and clean_ver(latest_available_version) > clean_ver(app_version):
        update_menu_string = f"💡 [U]pdate Available:  Verify integrity hash and update to {latest_available_version}."
    else:
        update_menu_string = f"   [U]pdate:            Verify integrity hash and update application (1x=check, 2x=update)."

    raw_folder_path = cli_dict.get('export_folder') or ""
    resolved_display_path = os.path.abspath(raw_folder_path) if raw_folder_path else "Initializing path.."		
	
    startup_log = [
        f"   Server Details:      http://localhost:{port_num} (Token: {project_saver_config.EXPECTED_TOKEN})",
        "---",
        f"⚙️ [P]rofile Mode:      {str(cli_dict.get('export_type') or 'AUTO').upper()}",
        f"🗒️ [F]ormats Enabled:   {str(cli_dict.get('export_format') or 'MARKDOWN').upper()}",
        "---",
        f"📂 [E]xport Folder:     {resolved_display_path}",
        f"   [I]mport Config:     Open folder containing singlefile-project-saver-config.json configuration.",
        f"   [R]enew Token:       Regenerate randomized API access authorization key.",
        "---"
    ]

# --- TARGET CODE MODIFICATION BLOCK ---
    # 🎈 [CHANGED]: Dynamically evaluates both standard single menus and multi-menu bitmask arrays with zero hardcoded core values
    if hasattr(project_saver_modules, 'ACTIVE_MODULES') and project_saver_modules.ACTIVE_MODULES:
        for mod_key, mod_ref in sorted(project_saver_modules.ACTIVE_MODULES.items()):
            mod_obj = mod_ref["mock"] if isinstance(mod_ref, dict) and mod_ref.get("type") == "binary" else mod_ref
            manifest = getattr(mod_obj, "MODULE_MANIFEST", {})
            
            # CASE 1: Process Advanced Multi-Menu Configurations (e.g., archiver.py)
            if "display_multi" in manifest:
                for option in manifest.get("display_multi", []):
                    bits = int(option.get("mask_bits", 0))
                    if not bits:
                        continue
                        
                    # Main Menu Visibility Constraints Pass: Title flags (1, 8, 32, 128) | Desc flags (2, 16, 64, 256)
                    show_title_main = bool(bits & 1) or bool(bits & 8) or bool(bits & 32) or bool(bits & 128)
                    show_desc_main  = bool(bits & 2) or bool(bits & 16) or bool(bits & 64) or bool(bits & 256)
                    show_value_main = bool(bits & 4) or bool(bits & 4) # Evaluates the live value substitution mask toggle
                    
                    if not (show_title_main or show_desc_main):
                        continue # Skip drawing this specific sub-row completely if no main menu bits are targeted
                        
                    display_m = option.get("display_menu", "")
                    display_d = option.get("display_desc", "")
                    
                    # Safely look up local module default definitions fallback
                    defaults_dict = manifest.get("defaults", {})
                    call_id = option.get("callback_key", "")
                    fallback_val = defaults_dict.get(call_id, "")
                    
                    live_val = ""
                    if show_value_main and hasattr(mod_obj, "get_live_display_value"):
                        try:
                            live_val = mod_obj.get_live_display_value(call_id, cli_dict)
                        except:
                            pass
                    if not live_val:
                        live_val = fallback_val

                    # Compile display layout based on active value presence
                    if show_value_main and live_val:
                        parenthesis_part = f" ({fallback_val})" if fallback_val and live_val != fallback_val else ""
                        description_content = f"{live_val}{parenthesis_part}"
                    else:
                        description_content = display_d

                    if show_title_main and show_desc_main:
                        startup_log.append(f"   {display_m:<24}{description_content}")
                    elif show_title_main:
                        startup_log.append(f"   {display_m}")
                    elif show_desc_main:
                        startup_log.append(f"   {description_content}")
                continue
            
            # CASE 2: Process Clean Backward-Compatible Single Menu Structures (manager, menu, custom, debug)
            meta_menu = int(manifest.get("meta", {}).get("menu", 0))
            if not meta_menu:
                continue
                
            display_m = manifest.get("display_menu", "")
            display_d = manifest.get("display_desc", "")
            
            # Standard main menu bitmask calculations check
            show_title = bool(meta_menu & 1)
            show_desc = bool(meta_menu & 2)
            
            if show_title and show_desc:
                startup_log.append(f"   {display_m:<24}{display_d}")
            elif show_title:
                startup_log.append(f"   {display_m}")
            elif show_desc:
                startup_log.append(f"   {display_d}")

# --- 8 lines of original context code AFTER ---
    startup_log.extend([
        update_menu_string,
        f"❌ [Q]uit Application:  Requires 3 consecutive taps with the shoes to escape Kansas."
    ])
    render_better_box(startup_log, title_str=f"Project Saver {app_version}", box_width_override=65)





def log_debug(msg):
    """Prints immediately to the terminal screen AND appends to debug.log natively."""
    try:
        with open("debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {str(msg)}\n")
        print(f"\n\033[95m[DEBUG]\033[0m {str(msg)}")
    except:
        pass
