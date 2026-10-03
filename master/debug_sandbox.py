# =========================================================================
# Project Saver Core Diagnostic Appliance & Sandboxed Module Auditor
# Designed to identify dynamic path-mangling bugs on clean clients. test1
# =========================================================================
import os
import sys
import platform

def execute_diagnostic_suite():
    print("=" * 80)
    print("🔍 PROJECT SAVER STANDALONE COMPILATION DIAGNOSTIC APP")
    print("=" * 80)
    print(f"Target Operating System  : {platform.platform()}")
    print(f"Python Runtime Version   : {sys.version.split()[0]}")
    print(f"Is Compiled via PyInstaller: {'YES (Standalone Bundle Mode)' if getattr(sys, 'frozen', False) else 'NO (Loose Source Script Mode)'}")
    
    if getattr(sys, 'frozen', False):
        print(f"Temporary Extraction Path: {sys._MEIPASS}")
        print(f"Executable Source Location: {sys.executable}")
        base_search_target = sys._MEIPASS
    else:
        print(f"Active Development Path  : {os.path.dirname(os.path.abspath(__file__))}")
        base_search_target = os.path.dirname(os.path.abspath(__file__))

    print("-" * 80)
    print("💼 STEP 1: AUDITING INTERNALLY EXTRACTED MEMORY SANDBOX OVERVIEW")
    print("Checking for decoupled sibling scripts inside the bundle's execution table...")
    
    targets = ["project_saver_config", "project_saver_ui", "project_saver_daemon"]
    for t in targets:
        # Tries to check if the bytecode is mapped in the system module tracker tables
        in_sys_modules = t in sys.modules
        
        # Physically scan the temporary disk directory context to see if the file exists
        py_filename = f"{t}.py"
        pyc_filename = f"{t}.pyc"
        physically_found_py = os.path.exists(os.path.join(base_search_target, py_filename))
        physically_found_pyc = os.path.exists(os.path.join(base_search_target, pyc_filename))
        
        status = "🟢 PRESENT" if (in_sys_modules or physically_found_py or physically_found_pyc) else "🔴 MISSING / BROKEN"
        print(f" -> Module '{t}': {status}")
        print(f"    [Tracking Metrics -> In sys.modules: {in_sys_modules} | Found .py: {physically_found_py} | Found .pyc: {physically_found_pyc}]")

    print("-" * 80)
    print("🌎 STEP 2: ACTIVE PYTHON PATH MATRIX RESOLUTION SCANS")
    print("Dumping active environment lookup arrays used by the module loader:")
    for idx, path in enumerate(sys.path):
        print(f" [{idx}] -> {path}")

    print("-" * 80)
    print("🔥 STEP 3: LIVE IMPORT EMULATION TRIAL")
    print("Attempting to wake up the decoupled configuration module matrix...")
    try:
        import project_saver_config
        print("🟢 CRITICAL TRAP BYPASSED: project_saver_config successfully imported!")
        print(f"    Loaded From Location: {getattr(project_saver_config, '__file__', 'Internal Baked Bytecode Pool')}")
    except Exception as fatal_error:
        print("🔴 INTERCEPTION CATCH TRIGGERED: Import routine blew up completely.")
        print(f"    Exception Details: {type(fatal_error).__name__} -> {fatal_error}")

    print("=" * 80)
    print("Diagnostic complete. Copy this screen text block to analyze the failure context.")
    print("=" * 80)
    input("Press [ENTER] to exit diagnostic space...")

if __name__ == "__main__":
    execute_diagnostic_suite()
