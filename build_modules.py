# ==========================================================================
# Project Saver: Standalone Pluggable Module Compilation Helper Engine
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import json
import time
import shutil
import hashlib
import subprocess
import importlib.util

def calculate_file_sha256(file_path):
    """Calculates a clean cryptographic validation fingerprint for compiled binaries."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest().lower()
    except Exception as e:
        print(f"   [-] Hash calculation failed for {file_path}: {e}")
        return None

def run_local_module_build_pipeline():
    """Scans local workspace extensions, compiles binaries, and registers manifest metrics."""
    print("\n" + "="*72)
    print(" 🛠️  PROJECT SAVER LOCAL MODULE COMPILATION & RELEASE ENGINE")
    print("="*72)
    
    script_base_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(script_base_dir, "modules")
    dist_dir = os.path.join(script_base_dir, "dist_modules")
    build_dir = os.path.join(script_base_dir, "build_modules")

    # Establish clean target export workspace paths natively
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)

    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)

    global_manifest = {
        "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "modules": {}
    }

    if not os.path.exists(modules_dir):
        print(f"🔴 ERROR: Dedicated modules target directory folder missing: {modules_dir}")
        sys.exit(1)

    # Isolate valid Python extensions while safely ignoring structural directory contexts
    module_files = [f for f in os.listdir(modules_dir) if f.endswith(".py") and f != "__init__.py"]
    
    if not module_files:
        print("⚠️  WARNING: No local pluggable module source code assets discovered.")
        return

    for file_entry in module_files:
        module_name = file_entry[:-3]
        file_path = os.path.join(modules_dir, file_entry)
        print(f"\n📦 Processing Extension: [{module_name.upper()}]")

        try:
            # Dynamically parse individual manifest definitions to execute structural sanity checks
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not hasattr(mod, "MODULE_MANIFEST"):
                print(f"   ⚠️  Skipped [{file_entry}]: Missing 'MODULE_MANIFEST' footprint entry.")
                continue

            manifest = mod.MODULE_MANIFEST
            binary_name = f"{module_name}.exe" if os.name == 'nt' else module_name
            compiled_binary_path = os.path.join(dist_dir, binary_name)

            print(f"   [*] Invoking local PyInstaller binary packaging compilation passes...")
            cmd = [
                "pyinstaller",
                "--onefile",
                "--clean",
                f"--distpath={dist_dir}",
                f"--workpath={build_dir}",
                f"--name={module_name}",
                file_path
            ]
            
            # Suppress high-speed scrolling terminal text spam unless an error occurs
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                print(f"   🔴 ERROR: PyInstaller compilation sequence collapsed for {module_name}!")
                print(result.stderr[:500])
                continue

            if os.path.exists(compiled_binary_path):
                binary_hash = calculate_file_sha256(compiled_binary_path)
                print(f"   🟢 SUCCESS: Compiled validation fingerprint -> {binary_hash}")

                global_manifest["modules"][module_name] = {
                    "display_name": manifest.get("display_name"),
                    "menu_shortcut": manifest.get("menu_shortcut"),
                    "version": manifest.get("meta", {}).get("version", "v0.0.1"),
                    "requires_core": manifest.get("meta", {}).get("requires", "v0.0.79"),
                    "autostart": manifest.get("autostart", False),
                    "binary_filename": binary_name,
                    "sha256": binary_hash
                }
        except Exception as e:
            print(f"   🔴 CRITICAL: Code parsing validation asset check failed on {file_entry}: {e}")

    # Output your system manifest ledger mapping records securely onto disk arrays
    manifest_out_path = os.path.join(dist_dir, "manifest.json")
    with open(manifest_out_path, "w", encoding="utf-8") as json_file:
        json.dump(global_manifest, json_file, indent=2)
    
    print("\n" + "-"*72)
    print(f"✨ COMPILATION COMPLETE: Local deployment file written to: {manifest_out_path}")
    
    # Clean up massive working metadata trace files locally to keep your repo pristine
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
            # Safely erase raw stray compiler specification files from the base workspace root
            spec_file = os.path.join(script_base_dir, f"{module_name}.spec")
            if os.path.exists(spec_file):
                os.remove(spec_file)
        except:
            pass
    print("="*72 + "\n")

if __name__ == "__main__":
    run_local_module_build_pipeline()
