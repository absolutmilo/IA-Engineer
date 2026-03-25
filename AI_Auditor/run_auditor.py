#!/usr/bin/env python3
"""
AI Engineering Guardian - Launcher
Choose between GUI or CLI interface
"""

import argparse
import sys
from pathlib import Path
from utils.logger import setup_logging

def main():
    # Setup logging early
    setup_logging(verbose=True)
    
    parser = argparse.ArgumentParser(
        description="AI Engineering Guardian - Auditor System",
        epilog="Choose your preferred interface mode"
    )
    
    # Interface selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gui", action="store_true", 
                       help="Launch the graphical user interface")
    group.add_argument("cli_path", nargs="?", metavar="PROJECT_PATH",
                       help="Run command-line audit on specified project")
    
    # Common options
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.gui:
        # Launch GUI
        try:
            print("🚀 Launching AI Engineering Guardian GUI...")
            from integrated_auditor_gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"❌ Failed to import GUI: {e}")
            print("Make sure all dependencies are installed: pip install -r requirements.txt")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to launch GUI: {e}")
            sys.exit(1)
            
    elif args.cli_path:
        # Launch CLI
        try:
            # Import and run main CLI
            project_path = Path(args.cli_path).resolve()
            if not project_path.exists():
                print(f"❌ Project path does not exist: {project_path}")
                sys.exit(1)
                
            # Add debug flag to sys.argv for main() to pick up
            if args.debug:
                sys.argv.append("--debug")
                
            print(f"🚀 Running CLI audit on: {project_path}")
            from main import main as cli_main
            cli_main()
            
        except ImportError as e:
            print(f"❌ Failed to import CLI: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to run CLI audit: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
