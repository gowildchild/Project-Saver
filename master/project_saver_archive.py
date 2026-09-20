import os
import re
import sys
import hashlib
import time
import subprocess
from bs4 import BeautifulSoup
from project_saver_exporter import EXPORTER_REGISTRY, render_pdf_fallback

# ==================== CONFIGURATIONS ====================
# Set your desired save path here (e.g., "C:/Users/YourName/Documents/ObsidianVault")
# Leaving it as "" saves files right next to the script
SAVE_DIRECTORY = os.path.join(os.path.expanduser("~"), "Documents", "Project-Saver")

# Choose your preferred markdown viewer/editor launcher:
# Options: "system_default", "obsidian", "vscode", "marktext"
CHOSEN_EDITOR = "system_default" 
# ========================================================
if getattr(sys, 'frozen', False):
    EXE_DIRECTORY = os.path.dirname(os.path.abspath(sys.executable))
else:
    EXE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Hardcodes the history index tracker file to live strictly inside your application directory path
HISTORY_FILE = os.path.join(EXE_DIRECTORY, "project_saver.db")

def load_processed_hashes():
    if not os.path.exists(HISTORY_FILE): 
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_hash(session_hash):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{session_hash}\n")

def clean_code_block(text):
    text = re.sub(re.compile(r'^```[a-zA-Z]*\n', re.MULTILINE), '', text)
    text = text.replace('```', '')
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r'^\s*\d+\s*[:|]\s*', '', line)
        cleaned_lines.append(cleaned_line)
    return "\n".join(cleaned_lines).strip()

def detect_language(text):
    text_lower = text.lower()
    if 'import ' in text_lower or 'def ' in text_lower or 'print(' in text_lower: 
        return 'py'
    if 'param(' in text_lower or 'write-host' in text_lower or '$' in text_lower: 
        return 'ps1'
    if 'use strict;' in text_lower or 'sub ' in text_lower or 'my $' in text_lower: 
        return 'pl'
    if text.startswith('{') and text.endswith('}'): 
        return 'json'
    if '<?xml' in text_lower or '<html' in text_lower: 
        return 'xml'
    return 'txt'

def force_window_to_foreground():
    """Forces the terminal execution environment to jump directly to the front of the screen."""
    try:
        if os.name == 'nt':  # Windows Native API Engine
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9) 
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
        elif sys.platform == 'darwin':  # macOS AppleScript Bridge
            os.system("osascript -e 'tell application \"Terminal\" to activate'")
    except Exception:
        pass

def ask_with_countdown(prompt, default_timeout=5, default_value=False):
    """Asks a question with a live timer. If it expires, it uses default_value and erases itself."""
    force_window_to_foreground()
    print(f"[?] {prompt}")
    
    user_responded = False
    input_str = ""
    default_label = "Y/n" if default_value else "y/N"

    if os.name == 'nt':  # Windows Engine
        import msvcrt
        os.system("") # Init ANSI escape codes
        
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
                elif char == '\b':  # Handle Backspace
                    input_str = input_str[:-1]
                    print(f"\r   --> {prompt} | {remaining}s | [{default_label}]: {input_str}", end="", flush=True)
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

    # Erase the prompt from terminal memory lines completely
    sys.stdout.write("\x1b[1A\x1b[2K\x1b[1A\x1b[2K")
    sys.stdout.flush()

    if not user_responded:
        return default_value
    else:
        cleaned_input = input_str.strip().lower()
        if cleaned_input in ['y', 'yes']:
            return True
        if cleaned_input in ['n', 'no']:
            return False
        return default_value

def ask_mode_override(detected_mode, default_timeout=5):
    """Allows dynamic switching of the parsed configuration layout on interception."""
    force_window_to_foreground()
    print(f"[?] Detected mode: [{detected_mode}]. Press 'c' for code, 'w' for web, or let timer run for default.")
    user_responded, input_str = False, ""

    if os.name == 'nt':
        import msvcrt
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            remaining = int(default_timeout - elapsed)
            if remaining <= 0: break
            print(f"\r   --> Override Export Profile? | {remaining}s | [c/w/Keep]: {input_str} ", end="", flush=True)
            if msvcrt.kbhit():
                char = msvcrt.getwche().lower()
                if char in ('\r', '\n'):
                    user_responded = True
                    break
                elif char in ('c', 'w'):
                    input_str = char
                    user_responded = True
                    break
            time.sleep(0.1)
        print()
    else:
        import select
        for remaining in range(default_timeout, 0, -1):
            print(f"\r   --> Override Export Profile? | {remaining}s | [c/w/Keep]: {input_str} ", end="", flush=True)
            ready, _, _ = select.select([sys.stdin], [], [], 1.0)
            if ready:
                input_str = sys.stdin.readline().strip().lower()
                user_responded = True
                break
                
    sys.stdout.write("\x1b[1A\x1b[2K\x1b[1A\x1b[2K")
    sys.stdout.flush()
    
    if user_responded and input_str == 'c': return "code_dev"
    if user_responded and input_str == 'w': return "web_article"
    return detected_mode

def launch_markdown_editor(file_path):
    """Launches your chosen markdown editor automatically."""
    print(f"[*] Launching editor ({CHOSEN_EDITOR}) for: {file_path}")
    try:
        if CHOSEN_EDITOR == "obsidian":
            filename_only = os.path.basename(file_path)
            subprocess.run(["start", f"obsidian://open?file={filename_only}"], shell=True)
        elif CHOSEN_EDITOR == "vscode":
            subprocess.Popen(["code", file_path], shell=True)
        elif CHOSEN_EDITOR == "marktext":
            subprocess.Popen(["marktext", file_path], shell=True)
        else:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
    except Exception as e:
        print(f"[-] Could not automatically launch editor: {e}")

def process_html_content(html_string, page_title, source_origin="Natively Captured", 
                         export_folder="", export_format="markdown", export_type="auto", auto_timeout=None, editor_override=None, app_version=None):
    current_session_hash = hashlib.md5(html_string.encode('utf-8')).hexdigest()
    processed_hashes = load_processed_hashes()
    
    if current_session_hash in processed_hashes:
        print(f"\n[!] ALERT: This identical session layout was already processed! Skipping.")
        return

    soup = BeautifulSoup(html_string, "html.parser")
    
    if export_type == "code":
        export_mode = "code_dev"
    elif export_type == "web":
        export_mode = "web_article"
    else: # Default behavior ("auto")
        origin_lower = source_origin.lower()
        if "github.com" in origin_lower or "google.com" in origin_lower:
            export_mode = "code_dev"
        else:
            export_mode = "web_article"

    export_mode = ask_mode_override(export_mode, default_timeout=4)
    parsing_root = soup
    is_github = "github.com" in source_origin.lower()

    if is_github:
        github_code_container = soup.find(id="read-only-cursor-wrapper") or soup.find(class_="blob-wrapper") or soup.find('react-file-lines')
        if github_code_container:
            parsing_root = github_code_container
            print("[*] Target Match: Isolated GitHub Code Content Area.")
    elif export_mode == "web_article":
        reader_container = soup.find(['article', 'main']) or soup.find(class_=re.compile(r'reader|content|article-body|post-content', re.I)) or soup.find(id=re.compile(r'reader|content|article-body|post-content', re.I))
        if reader_container:
            parsing_root = reader_container
            print("[*] Target Match: Isolated Reader-View structure for processing.")

    url_clean = source_origin.split('?')[0].split('#')[0]
    url_match = re.search(r'\.([a-zA-Z0-9]+)$', url_clean)
    url_extension = url_match.group(1).lower() if url_match else None
    
    if url_extension in ['html', 'htm', 'php', 'asp', 'aspx']:
        url_extension = None

    safe_title = re.sub(r'[\\/*?:"<>| ]', '_', page_title)[:50]
    
    base_dir = export_folder if export_folder else (SAVE_DIRECTORY if SAVE_DIRECTORY else os.getcwd())
    
    ExporterClass = EXPORTER_REGISTRY.get(export_mode, EXPORTER_REGISTRY["code_dev"])
    exporter = ExporterClass(base_dir, safe_title, app_version if app_version else "v0.0.60")

    timeout_duration = auto_timeout if auto_timeout is not None else 5

    export_detailed = ask_with_countdown("Create a detailed folder?", timeout_duration, False)
    trigger_auto_launch = ask_with_countdown("Open directly inside Markdown Editor?", timeout_duration, True)

    exporter.initialize_directories(export_detailed)

    for technical_garbage in parsing_root(["script", "style", "meta", "link", "noscript"]):
        technical_garbage.decompose()

    final_markdown_blocks = []
    code_block_index = 1
    recent_context_text = "script_asset"
    seen_code_hashes = set()

    if is_github and parsing_root != soup:
        for num in parsing_root.find_all(class_=re.compile(r'line-number|blob-num', re.I)):
            num.decompose()
        
        raw_code_text = parsing_root.get_text()
        clean_code = clean_code_block(raw_code_text)
        
        ext = url_extension if url_extension else detect_language(clean_code)
        
        asset_filename = f"{code_block_index}_github_source.{ext}"
        final_markdown_blocks.append(exporter.format_code(asset_filename, ext, clean_code))
        
        if export_detailed:
            asset_filepath = os.path.join(exporter.asset_folder, asset_filename)
            with open(asset_filepath, "w", encoding="utf-8") as script_file:
                script_file.write(clean_code)
    else:
        for element in parsing_root.find_all(['p', 'pre', 'code', 'h1', 'h2', 'h3', 'li', 'img']):
            if element.name == 'img':
                img_src = element.get('src', '').strip()
                if not img_src: 
                    continue
                img_alt = element.get('alt', '').strip() or element.get('title', '').strip() or "Captured Image"
                final_markdown_blocks.append(exporter.format_image(img_alt, img_src))
                continue
            text = element.get_text() if element.name in ['pre', 'code'] else element.get_text().strip()

            if not text or len(text.strip()) < 2 or text.strip().startswith("data:image/"): 
                continue

            is_pre_block = element.name == 'pre'
            
            is_inline_code = element.name == 'code' and (any(
                re.search(pattern, text.strip()) for pattern in [r'^import\s', r'^def\s', r'^\$', r'^use strict;', r'^class\s', r'^\s*def\s']
            ) or (text.strip().startswith('{') and text.strip().endswith('}')))


            if is_pre_block or is_inline_code:
                if text.strip().startswith('{') and text.strip().endswith('}'):
                    clean_code = text.strip()  
                else:
                    clean_code = clean_code_block(text)
                    
                code_hash = hashlib.md5(clean_code.encode('utf-8')).hexdigest()
                if code_hash in seen_code_hashes: 
                    continue
                seen_code_hashes.add(code_hash)

                ext = url_extension if (url_extension and is_github) else detect_language(clean_code)
                
                descriptive_slug = re.sub(r'[^a-zA-Z0-9\s]', '', recent_context_text).strip().lower()
                descriptive_slug = "_".join(descriptive_slug.split()[:5])
                if not descriptive_slug: 
                    descriptive_slug = "asset"

                asset_filename = f"{code_block_index}_{descriptive_slug}.{ext}"
                final_markdown_blocks.append(exporter.format_code(asset_filename, ext, clean_code))
                
                if export_detailed:
                    asset_filepath = os.path.join(exporter.asset_folder, asset_filename)
                    with open(asset_filepath, "w", encoding="utf-8") as script_file:
                        script_file.write(clean_code)
                code_block_index += 1
            else:
                text_clean = text.strip()
                if element.name in ['p', 'h2', 'h3'] and len(text_clean) > 5: 
                    recent_context_text = text_clean
                if element.name == 'h1': 
                    final_markdown_blocks.append(f"\n## {text_clean}\n")
                elif element.name == 'h2': 
                    final_markdown_blocks.append(f"\n### {text_clean}\n")
                elif element.name == 'h3': 
                    final_markdown_blocks.append(f"\n#### {text_clean}\n")
                elif element.name == 'li': 
                    final_markdown_blocks.append(f"* {text_clean}")
                else:
                    if final_markdown_blocks and final_markdown_blocks[-1] == text_clean: 
                        continue
                    final_markdown_blocks.append(f"\n{text_clean}\n")

    target_formats = [f.strip().lower() for f in export_format.split(',')]
    if 'html' in target_formats:
        with open(exporter.output_html, "w", encoding="utf-8") as f: 
            f.write(html_string)
        print(f"[+] Local backup HTML saved: {exporter.output_html}")
        
    if 'markdown' in target_formats or 'md' in target_formats:
        with open(exporter.output_md, "w", encoding="utf-8") as f:
            exporter.write_header(f, page_title, source_origin)
            exporter.write_blocks(f, final_markdown_blocks)
        print(f"[+] Structured Markdown Document saved: {exporter.output_md}")
        
    if 'pdf' in target_formats:
        render_pdf_fallback(exporter.output_pdf, page_title, source_origin, final_markdown_blocks)
        print(f"[+] Rendered PDF Document saved: {exporter.output_pdf}")

    save_processed_hash(current_session_hash)
    
    if trigger_auto_launch and ('markdown' in target_formats or 'md' in target_formats): 
        launch_markdown_editor(exporter.output_md)


if __name__ == "__main__":
    # Fallback to direct script execution handling via terminal inputs
    export_flag = "auto"
    if "--export-type" in sys.argv:
        try:
            idx = sys.argv.index("--export-type")
            export_flag = sys.argv[idx + 1].strip().lower()
        except IndexError:
            pass

    target_file = None
    for arg in sys.argv[1:]:
        if not arg.startswith("-") and arg != export_flag:
            target_file = arg
            break

    if target_file and os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            process_html_content(f.read(), target_file.replace(".html", ""), target_file, export_type=export_flag)
