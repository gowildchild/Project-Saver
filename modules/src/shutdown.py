# ==========================================================================
# Project Saver Module: Pluggable System Power Controller (shutdown.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved. 
# ==========================================================================
import os
import sys
import time
import subprocess
import threading
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
        "version": "v0.0.57",
        "requires": "v0.0.81",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True,         # Sets availability for cloud installation/use
        "menu": 19
    },
    "autostart": True,            # Manually loaded via workspace hotkey selections
    "display_profile": {
        "box_style_mask": 145,     # Standard high-density layout view
        "align_mask": 16,           # Inline Default
        "fg_color": "",            
        "bg_color": ""             
    },
    "display_multi": [
        {
            "callback_key": "daemon_status_info", 
            "menu_shortcut": "",
            "display_menu": "Daemon State",
            "display_name": "Host OS",
            "mask_bits": 6,   # 4 (MENU_VALUE) + 2 (MENU_DISPLAY_NAME)
            "action_type": "custom"
        },        
        {
            "callback_key": "cancel_shutdown",
            "menu_shortcut": "c",
            "display_menu": "Cancel",
            "display_desc": "Aborts any started shutdowns.",
            "mask_bits": 2
        },
        {
            "callback_key": "timed_shutdown",
            "menu_shortcut": "t",
            "display_menu": "Timed",
            "display_desc": "Schedules machine shutdown sequence in minutes.",
            "mask_bits": 6         # Bit 1 (Title) + Bit 4 (Live Value)

        },
        {
            "callback_key": "emg_shutdown",
            "menu_shortcut": "e",
            "display_menu": "EMG",
            "display_desc": "Emergency shutdown sequencing.",
            "mask_bits": 0         # Bit 1 (Title) + Bit 4 (Live Value)

        },        
        {
            "callback_key": "instant_shutdown",
            "menu_shortcut": "s",
            "menu_toggles": 3,
            "display_menu": "Shutdown Now",
            "display_desc": "Triggers instant system power-down routine.",
            "mask_bits": 5        # Bit 1 (Title) + Bit 4 (Live value tracking progress counts)
        }
    ],
    "defaults": {
        "daemon_status_info": "Detecting...",
        "timed_shutdown": "5 minutes",
        "emg_shutdown": "3 minutes",
        "instant_shutdown": "Requires 3 presses.",        
        "default_timer_minutes": "5",
        "emg_timer_minutes": "3",
        "safety_trigger_count": "3",
        "safety_trigger_shortcut": "s"
    }
}

LIVE_DAEMON_STATE = {
    "status_text": "Monitoring OS...",
    "lock": threading.Lock()
}

STRIKE_STATE = {"current_count": 0}

def _windows_power_message_pump():
    global LIVE_DAEMON_STATE
    try:
        import win32gui
        import win32con
    except ImportError:
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "Missing win32 modules"
        return

    def wndproc(hwnd, msg, wparam, lparam):
        if msg == win32con.WM_QUERYENDSESSION:
            with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "SHUTDOWN!"
            return True 
        elif msg == win32con.WM_ENDSESSION:
            if wparam is True:
                with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "LOGOUT!"
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = wndproc
    wc.lpszClassName = "ProjectSaverShutdownWatcher"
    hinst = win32gui.GetModuleHandle(None)
    try:
        class_atom = win32gui.RegisterClass(wc)
        hwnd = win32gui.CreateWindow(class_atom, "Project Saver Hook", 0, 0, 0, 0, 0, 0, 0, hinst, None)
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "Active 🟢"
        win32gui.PumpMessages()
    except Exception as err:
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = f"Win Hook Error: {err}"

# ─── LINUX D-BUS (SYSTEMD) SUBTHREAD ENGINE ───
def _linux_dbus_message_pump():
    global LIVE_DAEMON_STATE
    try:
        import dbus
        from gi.repository import GLib
    except ImportError:
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "Missing dbus/gobject libs"
        return

    def shutdown_signal_handler(preparing):
        if preparing:
            with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "LNX SHUTDOWN!"

    try:
        bus = dbus.SystemBus()
        bus.add_signal_receiver(shutdown_signal_handler, bus_name="org.freedesktop.login1", signal_name="PrepareForShutdown")
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "Active (Linux DBus) 🟢"
        loop = GLib.MainLoop()
        loop.run()
    except Exception as err:
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = f"Linux Hook Error: {err}"

# ─── MACOS COCOA RUNLOOP SUBTHREAD ENGINE ───
def _macos_cocoa_message_pump():
    global LIVE_DAEMON_STATE
    try:
        from AppKit import NSWorkspace
        from Foundation import NSObject
        from PyObjCTools import AppHelper
    except ImportError:
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "Missing PyObjC modules"
        return

    class ShutdownObserver(NSObject):
        def receiveWillPowerOff_(self, notification):
            with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "MAC SHUTDOWN!"

    try:
        nc = NSWorkspace.sharedWorkspace().notificationCenter()
        observer = ShutdownObserver.alloc().init()
        nc.addObserver_selector_name_object_(observer, "receiveWillPowerOff:", "NSWorkspaceWillPowerOffNotification", None)
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = "Active (macOS Cocoa) 🟢"
        AppHelper.runConsoleEventLoop()
    except Exception as err:
        with LIVE_DAEMON_STATE["lock"]: LIVE_DAEMON_STATE["status_text"] = f"Mac Hook Error: {err}"




def register_module_callbacks(server_reference=None):
    """
    Unified Background Thread Spawner.
    """
    import threading
    
    t = None
    if os.name == 'nt':
        t = threading.Thread(target=_windows_power_message_pump, daemon=True)
    elif sys.platform == 'darwin':
        t = threading.Thread(target=_macos_cocoa_message_pump, daemon=True)
    else:
        t = threading.Thread(target=_linux_dbus_message_pump, daemon=True)
        
    if t:
        t.start()


def get_live_display_value(callback_key, cli_dict=None):
    """
    Resolves active local runtime parameters dynamically on every frame pass, 
    feeding live string counters directly into the centralized workspace loop.
    """
    if callback_key == "daemon_status_info":
        with LIVE_DAEMON_STATE["lock"]:
            return LIVE_DAEMON_STATE["status_text"]
            
    if callback_key == "timed_shutdown":
        timer_min = module_library.get_setting("shutdown", "default_timer_minutes", "5")
        return f"{timer_min} minutes"

    if callback_key == "emg_shutdown":
        emg_timer_min = module_library.get_setting("shutdown", "emg_timer_minutes", "3")
        return f"{emg_timer_min} minutes"
    
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
            return "🟢 Shutdown cancelled successfully."
        except Exception as err:
            return f"🔴 ERROR cancelling Shutdown sequence -> {err}"

    elif user_input == 't':
        try:
            timer_min_str = module_library.get_setting("shutdown", "default_timer_minutes", "5")
            timer_minutes = int(timer_min_str) if timer_min_str.isdigit() else 5
            seconds_target = timer_minutes * 60
            
            if is_windows: subprocess.Popen(f"shutdown /s /t {seconds_target}", shell=True)
            else: subprocess.Popen(["shutdown", "-h", f"+{timer_minutes}"])
            return f"🟢 Shutdown power sequence activated (+{timer_minutes}m)."
        except Exception as err:
            return f"🔴 ERROR: Failed to execute timed trigger -> {err}"

    elif user_input == 'e':
        try:
            emg_timer_min_str = module_library.get_setting("shutdown", "emg_timer_minutes", "3")
            emg_timer_minutes = int(emg_timer_min_str) if emg_timer_min_str.isdigit() else 3
            emg_seconds_target = emg_timer_minutes * 60
            
            if is_windows: subprocess.Popen(f"shutdown /s /t {emg_seconds_target}", shell=True)
            else: subprocess.Popen(["shutdown", "-h", f"+{emg_timer_minutes}"])
            return f"🟢 Emergency Shutdown Override (+{emg_timer_minutes}m)."
        except Exception as err:
            return f"🔴 Failed to execute Shutdown Override -> {err}"

    elif user_input == 's':
        target_limit = 3
        for opt in manifest.get("display_multi", []):
            if opt.get("callback_key") == "instant_shutdown":
                target_limit = int(opt.get("menu_toggles", 3))

        STRIKE_STATE["current_count"] += 1
        if STRIKE_STATE["current_count"] >= target_limit:
            print("\n[!] Initializing forced machine shutdown now...")
            try:
                if is_windows: subprocess.Popen("shutdown /s /t 0", shell=True)
                else: subprocess.Popen(["shutdown", "-h", "now"])
            except: pass
            sys.exit(0)
        else:
            return f"⚠️ WARNING: [{STRIKE_STATE['current_count']}/{target_limit}] times to confirm powerdown down switch."
            
    return "Awaiting input power command option..."

def execute_interactive_menu(cli_dict, app_version, port_num):
    """Routes execution straight down into the centralized framework orchestrator loop."""
    import project_saver_x
    
    if MODULE_MANIFEST.get("autostart") and not cli_dict.get("engine_bootstrapped"):
        register_module_callbacks(cli_dict)

    project_saver_x.run_interactive_workspace_loop(
        MODULE_MANIFEST, __file__, cli_dict, 
        get_live_display_value, handle_local_keyboard_action, 
        box_title="Shutdown Controller"
    )
        
if __name__ == "__main__":
    module_library.run_standalone_safely(MODULE_MANIFEST, execute_interactive_menu)
