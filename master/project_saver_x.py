# ==========================================================================
# Project Saver Core: Cross-Platform Unified Shared Framework (project_saver_x.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import re
import configparser
from enum import IntFlag, auto

status_prompt  = "Awaiting Input..."


class MenuTypes(IntFlag):
    NONE              = 0
    MENU_SHORT_NAME   = 1    # Multiple items on a line possible
    MENU_DISPLAY_NAME = 2    # display_menu > display_name
    MENU_VALUE        = 4    # Display real-time value(s) and defaults
    SHOW_ON_MAIN_MENU = 16   # show entry main menu
    SHOW_ON_ALL       = 32   # show in every menu
    SHOW_MULTI_MENU   = 64   # show multi-menu layout engine
    STRIKE_1          = 128  # 1 extra verification press needed
    STRIKE_2          = 256  # 2 extra verification presses needed
    STRIKE_3          = 512  # 3 extra verification presses needed
    PRESS_LONG        = 1024 # Long Press is required

class ConfirmationTypes(IntFlag):
    NONE              = 0
    CHOICE_DEFAULT    = 1    # Default choice available
    CHOICE_YES        = 2    # Yes/Accept
    CHOICE_WAIT       = 4    # Wait Longer
    CHOICE_RETRY      = 8    # Retry/Try Again/Extra Try
    CHOICE_OPEN       = 32   # Open/Use/Accept
    CHOICE_CANCEL     = 64   # Cancel current job
    TIMED_DENY        = 256  # Deny/No/Cancel by default
    TIMED_ACCEPT      = 512  # Accept/Open/Save/Retry by default
    TIMED_5S          = 1024 # 5S timer
    TIMED_10S         = 2048 # 10S timer
    TIMED_15S         = 4096 # 15S Timer Down
    
class AlignFlags:
    NONE    = 0
    # Horizontal Constraints (Bits 1-2)
    LEFT    = 1     # 01 in binary
    RIGHT   = 2     # 10 in binary
    CENTER  = 3     # 11 in binary (LEFT & RIGHT both active!)
    # Vertical Constraints (Bits 16-32)
    TOP     = 16    # 010000 in binary
    BOTTOM  = 24    # 100000 in binary
    MIDDLE  = 40    # 110000 in binary (TOP & BOTTOM both active!)

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

#project_saver_x.render_better_box(
#    system_stats, 
#    title_left="NETWORK TRAFFIC INGESTION",
#    box_style_mask=385, 
#    fg_color="#00FF66", 
#    bg_color="#0A0F24"
#)
#project_saver_x.render_better_box(
#    alert_logs, 
#    title_left="⚠️ CRITICAL EXCEPTION ENCOUNTERED",
#    box_style_mask=274, 
#    fg_color="FF0055"
#)


def render_bitmask_box(
    raw_lines_list: list, 
    title_left: str = "Project Saver", 
    title_right: str = "",
    foot_left: str = "",
    foot_middle: str = "",
    foot_right: str = "",
    box_style_mask: int = 274,  
    box_width_override: int = 0,
    fg_color: str = "",         
    bg_color: str = "",
    align_mask: int = 0         # 0 = Inline Default, 43 = Center Middle Overlay Pop-up
):
    """
    Advanced Data-Driven Canvas Framework with 24-bit True Colour and Absolute Grid Placement.
    Uses binary align_mask coordinates to render overlay popups without moving terminal line layers behind it.
    """
    def get_visual_width(text_line: str) -> int:
        import re
        clean = re.sub(r'\033\[[0-9;]*m', '', str(text_line))
        width = 0
        for char in clean:
            o = ord(char)
            if o in (0xfe0f, 0x200d): continue
            if (0x1f300 <= o <= 0x1f9ff) or (0x2600 <= o <= 0x27bf) or (0x2b50 <= o <= 0x2b55): width += 2
            elif 0x4e00 <= o <= 0x9fff: width += 2
            else: width += 1
        return width

    def hex_to_ansi(hex_str: str, is_bg: bool = False) -> str:
        if not hex_str: return ""
        clean_hex = hex_str.lstrip('#').strip()
        if len(clean_hex) != 6: return ""
        try:
            r, g, b = int(clean_hex[0:2], 16), int(clean_hex[2:4], 16), int(clean_hex[4:6], 16)
            return f"\x1b[48;2;{r};{g};{b}m" if is_bg else f"\x1b[38;2;{r};{g};{b}m"
        except: return ""

    # 1. Isolate Core Frame Typography Widths
    filtered_lines = [line for line in raw_lines_list if str(line).strip() not in ("---", "===")]
    header_len = get_visual_width(title_left) + get_visual_width(title_right) + 6
    footer_len = get_visual_width(foot_left) + get_visual_width(foot_middle) + get_visual_width(foot_right) + 8
    max_content_len = max((get_visual_width(line) for line in filtered_lines), default=len(title_left))
    max_len = max(max_content_len, header_len, footer_len)
    
    target_width = box_width_override if box_width_override > 0 else 76
    box_width = max(target_width, max_len + 4)
    box_height = len(raw_lines_list) + 2  # Total layout rows including top and bottom frames

    # 2. Decode Terminal Screen Position Coordinates Absolute Mapping
    start_row = 0
    start_col = 0
    is_absolute_overlay = align_mask > 0

    if is_absolute_overlay:
        try:
            term_cols, term_rows = os.get_terminal_size()
            
            # Horizontal Bit Evaluation Pass
            h_bits = align_mask & 3
            if h_bits == 3:    start_col = max(1, (term_cols - box_width) // 2)      # CENTER
            elif h_bits == 1:  start_col = 2                                         # LEFT
            elif h_bits == 2:  start_col = max(1, term_cols - box_width - 1)         # RIGHT
            else: start_col = 2
            
            # Vertical Bit Evaluation Pass
            v_bits = align_mask & 48
            if v_bits == 48:   start_row = max(1, (term_rows - box_height) // 2)     # MIDDLE
            elif v_bits == 16: start_row = 2                                         # TOP
            elif v_bits == 32: start_row = max(1, term_rows - box_height - 1)        # BOTTOM
            else: start_row = 2
            
            # Freeze active terminal cursor positioning layout paths safely
            sys.stdout.write("\x1b[s")
        except:
            is_absolute_overlay = False

    def print_line(content_str, current_row_offset):
        if is_absolute_overlay:
            # Jump explicitly to terminal absolute column slot without carriage drop cascades
            sys.stdout.write(f"\x1b[{start_row + current_row_offset};{start_col}H{content_str}")
        else:
            print(content_str)

    # 3. Compile Color Elements
    c_on = f"{hex_to_ansi(fg_color, False)}{hex_to_ansi(bg_color, True)}"
    c_off = "\x1b[0m" if c_on else ""

    # 4. Map Glyph Line Sets
    GLYPHS = {
        1: {"TL": "┌", "TR": "┐", "BL": "└", "BR": "┘", "HZ": "─", "VT": "│", "DIV": "├"},
        2: {"TL": "╔", "TR": "╗", "BL": "╚", "BR": "╝", "HZ": "═", "VT": "║", "DIV": "╠"},
        3: {"TL": "▄", "TR": "▄", "BL": "█", "BR": "█", "HZ": "▄", "VT": "█", "DIV": "╠"}
    }
    accent_id  = box_style_mask & 7        
    inside_id  = (box_style_mask & 48) >> 4  
    outside_id = (box_style_mask & 384) >> 7 

    g_out = GLYPHS.get(outside_id if outside_id in GLYPHS else (accent_id if accent_id in GLYPHS else 1))
    g_in  = GLYPHS.get(inside_id if inside_id in GLYPHS else (accent_id if accent_id in GLYPHS else 1))
    g_acc = GLYPHS.get(accent_id if accent_id in GLYPHS else 1)

    # 5. Render Top Header Line
    left_header = f"─┤ {title_left} ├" if title_left else ""
    right_header = f"┤ {title_right} ├─" if title_right else ""
    available_fill = box_width - get_visual_width(left_header) - get_visual_width(right_header)
    header_dash_line = g_out["HZ"] * max(4, available_fill)
    
    print_line(f"{c_on}{g_out['TL']}{left_header}{header_dash_line}{right_header}{g_out['TR']}{c_off}", 0)

    # 6. Render Body Rows
    row_idx = 1
    for line in raw_lines_list:
        clean_line = str(line).rstrip()
        if clean_line.strip() == "===":
            print_line(f"{c_on}{g_out['VT']}{g_acc['HZ'] * box_width}{g_out['VT']}{c_off}", row_idx)
        elif clean_line.strip() == "---":
            print_line(f"{c_on}{g_in['DIV']}{g_in['HZ'] * box_width}{g_in['DIV']}{c_off}", row_idx)
        else:
            current_width = get_visual_width(clean_line)
            padding_spaces = " " * (box_width - current_width - 2)
            print_line(f"{c_on}{g_out['VT']}{c_off} {clean_line}{padding_spaces} {c_on}{g_out['VT']}{c_off}", row_idx)
        row_idx += 1

    # 7. Render Dynamic Footer
    f_left = f"─┤ {foot_left} ├" if foot_left else ""
    f_mid = f"┤ {foot_middle} ├" if foot_middle else ""
    f_right = f"┤ {foot_right} ├─" if foot_right else ""
    rem_footer_fill = box_width - (get_visual_width(f_left) + get_visual_width(f_mid) + get_visual_width(f_right))

    if rem_footer_fill < 4 or not f_mid:
        footer_dash = g_out["HZ"] * max(4, rem_footer_fill)
        print_line(f"{c_on}{g_out['BL']}{f_left}{footer_dash}{f_right}{g_out['BR']}{c_off}", row_idx)
    else:
        split_fill = rem_footer_fill // 2
        print_line(f"{c_on}{g_out['BL']}{f_left}{g_out['HZ'] * split_fill}{f_mid}{g_out['HZ'] * (rem_footer_fill - split_fill)}{f_right}{g_out['BR']}{c_off}", row_idx)

    # 8. Unfreeze Cursor and Clear Line Pipeline
    if is_absolute_overlay:
        sys.stdout.write("\x1b[u")
        sys.stdout.flush()

def render_better_box(raw_lines_list, title_str="Project Saver", box_width_override=0):
    # Forward pass to the unified engine with explicit defaults
    render_bitmask_box(raw_lines_list, title_left=title_str, box_width_override=box_width_override)

def draw_fixed_menu_bar(app_version, port_num, active_module="Main Daemon"):
# ######## 8 Lines of Code After for Navigation Context ########
    """
    Natively renders an isolated top system menu dashboard line bar at row 1 
    holding network port allocations and cross-platform real-time metrics.
    """
    import time
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

#def render_better_box(raw_lines_list, title_str="Project Saver", box_width_override=0):
#    # Forward pass to the unified engine with explicit defaults
#    render_bitmask_box(raw_lines_list, title_left=title_str, box_width_override=box_width_override)

def render_nice_box(raw_lines_list: list, title_str: str = "Project Saver", box_width_override: int = 0):
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

def ask_with_bitmask_countdown(prompt, confirmation_mask):
    """
    Enriched interactive countdown dialogue tracking inputs, timing scales, and defaults
    driven completely by stacked ConfirmationTypes flags while preserving legacy layout widths.
    """
    force_window_to_foreground()
    
    # 1. Decode durations safely from the enum matrix flags
    default_timeout = 5
    if ConfirmationTypes.TIMED_5S in confirmation_mask:
        default_timeout = 5
    elif ConfirmationTypes.TIMED_10S in confirmation_mask:
        default_timeout = 10
    elif ConfirmationTypes.TIMED_15S in confirmation_mask:
        default_timeout = 15

    # 2. Extract structural default fallback options on expiration
    default_value = False
    if ConfirmationTypes.TIMED_ACCEPT in confirmation_mask:
        default_value = True
    elif ConfirmationTypes.TIMED_DENY in confirmation_mask:
        default_value = False
    elif ConfirmationTypes.CHOICE_DEFAULT in confirmation_mask:
        default_value = True

    # 3. Dynamically compile a multi-choice option character label list
    allowed_choices = []
    
    # Yes / Accept Option Mapping
    if ConfirmationTypes.CHOICE_YES in confirmation_mask:
        allowed_choices.append("Y" if default_value else "y")
    else:
        allowed_choices.append("n") # Safety implicit 'no' option path boundary
        
    # Open / Use / Accept Alternative Flag Mapping
    if ConfirmationTypes.CHOICE_OPEN in confirmation_mask:
        allowed_choices.append("O" if default_value else "o")
        
    # Retry / Try Again Secondary Path Mapping
    if ConfirmationTypes.CHOICE_RETRY in confirmation_mask:
        allowed_choices.append("R" if default_value else "r")
        
    # Wait Longer Iteration Flag Mapping
    if ConfirmationTypes.CHOICE_WAIT in confirmation_mask:
        allowed_choices.append("W" if default_value else "w")
        
    # Cancel Job / Abort Command Sequence Mapping
    if ConfirmationTypes.CHOICE_CANCEL in confirmation_mask:
        # Cancel often targets the negative space; format case intentionally
        allowed_choices.append("C" if not default_value else "c")

    # Join gathered options cleanly into a uniform display label (e.g., [y/r/C] or [Y/o/r/c])
    default_label = "/".join(allowed_choices)

    print(f"[?] {prompt}")
    user_responded = False
    input_str = ""

    if os.name == 'nt':  # Windows Engine
        import msvcrt
        os.system("")  # Initialize ANSI color tables
        
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            remaining = int(default_timeout - elapsed)
            
            if remaining <= 0:
                break
                
            print(f"\r   --> {prompt} | {remaining}s | [{default_label}]: {input_str} ", end="", flush=True)
            
            if msvcrt.kbhit():
                char = msvcrt.getwche()
                if char in ('\r', '\n'):
                    user_responded = True
                    break
                elif char == '\b':  # Handle Backspace deletions cleanly
                    input_str = input_str[:-1]
                    print(f"\r   --> {prompt} | {remaining}s | [{default_label}]: {input_str} \x1b[K", end="", flush=True)
                else:
                    input_str += char
                    
            time.sleep(0.1)
        print()

    else:  # macOS / Linux Engine
        import select
        for remaining in range(default_timeout, 0, -1):
            print(f"\r   --> {prompt} | {remaining}s | [{default_label}]: {input_str} ", end="", flush=True)
            ready, _, _ = select.select([sys.stdin], [], [], 1.0)
            if ready:
                input_str = sys.stdin.readline().strip().lower()
                user_responded = True
                break

    # Cleanly remove the countdown visual artifacts from your active console frame memory lines
    sys.stdout.write("\x1b[1A\x1b[2K\x1b[1A\x1b[2K")
    sys.stdout.flush()

    if not user_responded:
        return "DEFAULT_TIMEOUT_TRIGGERED"
    else:
        cleaned_input = input_str.strip().lower()
        if cleaned_input in ['y', 'yes']: return "YES"
        if cleaned_input in ['n', 'no']: return "NO"
        if cleaned_input in ['r', 'retry']: return "RETRY"
        if cleaned_input in ['c', 'cancel']: return "CANCEL"
        if cleaned_input in ['o', 'open']: return "OPEN"
        if cleaned_input in ['w', 'wait']: return "WAIT"
        return "INVALID_SELECTION_FALLBACK"


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

    cli_dict, _, _ = module_library.bootstrap_session(cli_dict, "v0.0.1", 19763)
    
    status_message = "Awaiting Input..."
    strike_counters = {}
    
    while True:
        # 1. Clear terminal screen platform-natively using your shared tracking routine
        module_library.clear_screen_with_trace(manifest, caller_file)

        # 2. Build the structural layout context arrays dynamically
        panel_content = [
            f"   Active Module Name:  {manifest['display_name']}",
            "---",
        ]

        # 3. Dynamic row mapping driven entirely by your display_multi metadata rules
        short_line_buffer = ""
        
        for option in manifest.get("display_multi", []):
            bits = MenuTypes(int(option.get("mask_bits", 0)))
            if bits == MenuTypes.NONE:
                continue
                
            show_short_name = MenuTypes.MENU_SHORT_NAME in bits
            show_display_name = MenuTypes.MENU_DISPLAY_NAME in bits
            show_value = MenuTypes.MENU_VALUE in bits
            
            display_m = option.get("display_menu", "").strip()
            display_d = option.get("display_desc", "").strip()
            
            live_val = ""
            if show_value and get_live_val_callback:
                try:
                    live_val = get_live_val_callback(option.get("callback_key", ""), cli_dict)
                except:
                    pass

            if not live_val and show_value:
                live_val = manifest.get("defaults", {}).get(option.get("callback_key", ""), "")

            if show_value and live_val:
                description_content = f"{display_d} -> ({live_val})"
            else:
                description_content = display_d
                
            # Handle option bit compilation layouts dynamically
            if show_short_name:
                item_str = f" [{option.get('menu_shortcut', '').upper()}] {display_m if display_m else option.get('callback_key', '')}  "
                if len(short_line_buffer) + len(item_str) > 65:
                    panel_content.append(short_line_buffer)
                    short_line_buffer = "   " + item_str
                else:
                    short_line_buffer += item_str if short_line_buffer else "   " + item_str
            else:
                if short_line_buffer:
                    panel_content.append(short_line_buffer)
                    short_line_buffer = ""
                    
                if show_display_name and display_d:
                    panel_content.append(f"   {display_m:<24}{description_content}")
                elif show_display_name:
                    panel_content.append(f"   {display_m}")
                elif display_d:
                    panel_content.append(f"   {description_content}")

        if short_line_buffer:
            panel_content.append(short_line_buffer)

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
        
        if user_input in ['-', 'q']:
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

        # Intercept and validate safety verification flags before executing down inside module
        matched_option = None
        for opt in manifest.get("display_multi", []):
            if opt.get("menu_shortcut", "").lower() == str(user_input).lower():
                matched_option = opt
                break
                
        if matched_option:
            opt_bits = MenuTypes(int(matched_option.get("mask_bits", 0)))
            required_strikes = 0
            if MenuTypes.STRIKE_1 in opt_bits: required_strikes = 1
            elif MenuTypes.STRIKE_2 in opt_bits: required_strikes = 2
            elif MenuTypes.STRIKE_3 in opt_bits: required_strikes = 3
            
            if required_strikes > 0:
                current_strikes = strike_counters.get(user_input, 0) + 1
                if current_strikes <= required_strikes:
                    strike_counters[user_input] = current_strikes
                    status_message = f"⚠️ WARNING: Verification Captured! Press [{user_input.upper()}] ({current_strikes}/{required_strikes + 1}) times to verify action."
                    time.sleep(0.05)
                    continue
                else:
                    strike_counters[user_input] = 0  # Strike validation clear on pass match

        # 6. Hand off key captures directly to the module interior handler to execute routines
        if handle_key_callback:
            callback_response = handle_key_callback(user_input, cli_dict, manifest)
            if callback_response == "BREAK_LOOP":
                break
            elif callback_response:
                status_message = callback_response

        time.sleep(0.05)

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
