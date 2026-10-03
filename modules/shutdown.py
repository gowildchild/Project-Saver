# shutdown.py (Example GitHub Module Structure)
MODULE_MANIFEST = {
    "name": "shutdown",
    "display_name": "s[H]utdown controller",
    "menu_shortcut": "h",        # Shortcut from main menu
    "autostart": False,
    "defaults": {
        "default_timer_minutes": "5",
        "safety_trigger_count": "2"
    }
}

def register_module_callbacks():
    """Hooks into daemon server traffic if autostart is True"""
    pass

def execute_interactive_menu():
    """Fired when user hits 'M' -> selects 'shutdown', or hits shortcut 'H'"""
    # Handles [C]ancel, [T]imed, [S]hutdown, and [-] to return
    pass
