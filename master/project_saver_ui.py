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
    """
    Transparently forwards visual raw line list packets directly 
    down into your cross-platform unified project_saver_x library file.
    """
    import project_saver_x
    project_saver_x.render_better_box(raw_lines_list, title_str, box_width_override)


def refresh_dashboard_view(cli_dict, app_version, port_num):
    """
    Clears the screen and renders the standard startup box with the most up-to-date active settings.
    """
    import os
    import sys
    import project_saver_config
    import project_saver_modules
    os.system('cls' if os.name == 'nt' else 'clear')
    update_menu_string = None

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

    if hasattr(project_saver_modules, 'ACTIVE_MODULES') and project_saver_modules.ACTIVE_MODULES:
        for mod_key, mod_ref in sorted(project_saver_modules.ACTIVE_MODULES.items()):
            if isinstance(mod_ref, dict):
                manifest = mod_ref.get("MODULE MANIFEST", {})
                mod_obj = mod_ref.get("instance") if mod_ref.get("type") == "script" else None
            else:
                manifest = getattr(mod_ref, "MODULE_MANIFEST", {})
                mod_obj = mod_ref
            if not manifest:
                continue
                
            # CASE 1: Process Advanced Multi-Menu Configurations (e.g., archiver.py)
            if "display_multi" in manifest:
                for option in manifest.get("display_multi", []):
                    bits = int(option.get("mask_bits", 0))
                    if not bits or not bool(bits & 8):
                        continue
                    show_title_main = bool(bits & 1)
                    show_desc_main = bool(bits & 2)
                    show_value_main = bool(bits & 4)
                    if not (show_title_main or show_desc_main):
                        continue
                    display_m = option.get("display_menu", "")
                    display_d = option.get("display_desc", "")
                    defaults_dict = manifest.get("defaults", {})
                    call_id = option.get("callback_key", "")
                    fallback_val = defaults_dict.get(call_id, "")
                    live_val = ""
                    if show_value_main and mod_obj and hasattr(mod_obj, "get_live_display_value"):
                        try:
                            live_val = mod_obj.get_live_display_value(call_id, cli_dict)
                        except:
                            pass
                    if not live_val:
                        live_val = fallback_val
                    if show_value_main and live_val:
                        parenthesis_part = f" ({fallback_val})" if fallback_val and live_val != fallback_val else ""
                        description_content = f"{live_val}{parenthesis_part}"
                    else:
                        description_content = display_d
                    if show_title_main and show_desc_main:
                        startup_log.append(f"  {display_m:<28} {description_content}")
                    elif show_title_main:
                        startup_log.append(f"  {display_m}")
                
            # CASE 2: Process Clean Backward-Compatible Single Menu Structures
            meta_menu = 0
            meta_block = manifest.get("meta")
            if isinstance(meta_block, dict):
                meta_menu = int(meta_block.get("menu", manifest.get("menu", 0)))
            else:
                meta_menu = int(manifest.get("menu", 0))
            if not meta_menu:
                continue
            display_m = manifest.get("display_menu", "")
            display_d = manifest.get("display_desc", "")
            show_title = bool(meta_menu & 1)
            show_desc = bool(meta_menu & 2)
            if show_title and show_desc:
                startup_log.append(f"  {display_m:<28} {display_d}")
            elif show_title:
                startup_log.append(f"  {display_m}")
            elif show_desc:
                startup_log.append(f"  {display_d}")

        startup_log.extend([
            update_menu_string,
            " [Q]uit Application:  Requires 3 consecutive taps with the shoes to escape Kansas."
        ])
    import project_saver_x
    project_saver_x.render_better_box(startup_log, title_str=f"Project Saver {app_version}", box_width_override=72)

def log_debug(msg):
    """Prints immediately to the terminal screen AND appends to debug.log natively."""
    try:
        with open("debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {str(msg)}\n")
        print(f"\n\033[95m[DEBUG]\033[0m {str(msg)}")
    except:
        pass
