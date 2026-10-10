# ==========================================================================
# Project Saver Core: Cross-Platform Unified Shared Framework (project_saver_x.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import re
import configparser

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
