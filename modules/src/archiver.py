# ==========================================================================
# Project Saver Module: Pluggable Core Archiver Hook Layer (archiver.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import time
import json
import module_library

MODULE_MANIFEST = {
    "name": "archiver",
    "display_name": "Site & Code Archival",
    "display_menu": "[A]rchive Engine",
    "display_desc": "Save Projects Through SingleFile",
    "menu_shortcut": "a",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.34",
        "requires": "v0.0.79",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True,         # Sets availability for cloud installation/use
        "menu": 3
    },
    "autostart": True,             # AUTO-STARTS: Instantly hooks listening loops on boot!
    "display_multi": [
        {
            "callback_key": "live_interception_stats",
            "menu_shortcut": "",
            "display_menu": "",
            "display_desc": "",
            "mask_bits": 4,
            "action_type": "custom"
        },        
        {
            "callback_key": "profile_mode",
            "menu_shortcut": "p",
            "display_menu": "⚙️ [P]rofile Mode:",
            "display_desc": "AUTO / CODE / WEB Configuration Profile Strategy",
            "mask_bits": 13,         # Bit 1 (Title) + Bit 4 (Live Value)
            "action_type": "forward_upstream"
        },
        {
            "callback_key": "formats_enabled",
            "menu_shortcut": "f",
            "display_menu": "🗒️ [F]ormats Enabled:",
            "display_desc": "MARKDOWN / HTML / PDF Asset Output Generation",
            "mask_bits": 13,         # Bit 1 (Title) + Bit 4 (Live Value)
            "action_type": "forward_upstream"
        },
        {
            "callback_key": "export_folder",
            "menu_shortcut": "e",
            "display_menu": "📂 [E]xport Folder:",
            "display_desc": "Target directory folder location layout path",
            "mask_bits": 13,         # Bit 1 (Title) + Bit 4 (Live Value)
            "action_type": "forward_upstream"
        }
    ],
    "defaults": {
        "profile_mode": "AUTO",
        "formats_enabled": "MARKDOWN",
        "export_folder": r"\\testshare\FWC_science\WEB Vault",
        "autosave_captured_json": "no",
        "verbose_logging": "yes"
    }
}

LAST_CAPTURED_PACKET_INFO = {
    "timestamp": "No packets intercepted yet.",
    "target_url": "N/A",
    "content_length": 0
}

def register_module_callbacks(server_reference=None):
    """
    Executed automatically on boot because autostart is True.
    """
    global LAST_CAPTURED_PACKET_INFO
    pass

def process_intercepted_payload_broadcast(url, html_bytes, headers_dict):
    """
    Callback trigger target invoked by the core socket server daemon.
    Proves that the module can successfully receive all necessary data strings.
    """
    global LAST_CAPTURED_PACKET_INFO
    LAST_CAPTURED_PACKET_INFO["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
    LAST_CAPTURED_PACKET_INFO["target_url"] = str(url)
    LAST_CAPTURED_PACKET_INFO["content_length"] = len(html_bytes) if html_bytes else 0

def get_live_display_value(callback_key, cli_dict=None):
    """Resolves runtime execution values dynamically for the centralized loop tracker."""
    import os
    if not cli_dict:
        cli_dict = {}
        
    if callback_key == "live_interception_stats":
        return (
            f"\n   📡 LIVE DAEMON INTERCEPTION OVERVIEW:\n"
            f"      Last Intercept Timestamp: {LAST_CAPTURED_PACKET_INFO['timestamp']}\n"
            f"      Intercepted Target URL:   {LAST_CAPTURED_PACKET_INFO['target_url']}\n"
            f"      Intercepted Bytes Length: {LAST_CAPTURED_PACKET_INFO['content_length']} bytes"
        )
    elif callback_key == "export_folder":
        raw_folder = cli_dict.get('export_folder') or MODULE_MANIFEST["defaults"]["export_folder"]
        return os.path.abspath(raw_folder) if raw_folder else ""
    elif callback_key == "profile_mode":
        return str(cli_dict.get('export_type') or MODULE_MANIFEST["defaults"]["profile_mode"]).upper()
    elif callback_key == "formats_enabled":
        return str(cli_dict.get('export_format') or MODULE_MANIFEST["defaults"]["formats_enabled"]).upper()
    return ""

def handle_local_keyboard_action(user_input, cli_dict, manifest):
    """Passes key strings downstream straight to your centralized layout router helper."""
    import project_saver_x
    return project_saver_x.handle_unified_keyboard_routing(
        user_input, cli_dict, manifest, 
        get_live_display_value, local_custom_callback=None
    )

# --- TARGET CODE MODIFICATION BLOCK ---
def execute_interactive_menu(cli_dict, app_version, port_num):
    """
    Routes execution straight down into the centralized framework orchestrator loop,
    completely bypassing redundant, hardcoded terminal polling logic.
    """
    import project_saver_x
    project_saver_x.run_interactive_workspace_loop(
        MODULE_MANIFEST, __file__, cli_dict, 
        get_live_display_value, handle_local_keyboard_action, 
        box_title="Website Archiver"
    )
        
if __name__ == "__main__":
    module_library.run_standalone_safely(MODULE_MANIFEST, execute_interactive_menu)
