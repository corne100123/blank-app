import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    """Helper to find files relative to the executable or script."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, path)

if __name__ == "__main__":
    # Ensure the 'DFUS_30_Suite' directory is in the python path for imports
    sys.path.append(resolve_path("DFUS_30_Suite"))
    
    # Path to your main app file
    app_path = resolve_path(os.path.join("DFUS_30_Suite", "app.py"))
    
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ]
    sys.exit(stcli.main())