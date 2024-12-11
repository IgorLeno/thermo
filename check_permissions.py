# check_permissions.py
import os
import sys
import ctypes
from pathlib import Path

def is_admin():
    """Check if the script is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_folder_permissions(path):
    """Check if we have write permissions on a folder"""
    try:
        test_file = path / "permission_test.txt"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception:
        return False

def main():
    """Main function to check and request permissions"""
    current_dir = Path.cwd()
    venv_dir = current_dir / "venv"
    
    print("Checking permissions...")
    
    # Check if running as admin
    if not is_admin():
        print("\nScript is not running with admin privileges.")
        print("Some operations may require elevated permissions.")
        
        # Try to run as admin
        if sys.platform == 'win32':
            print("\nAttempting to restart with admin privileges...")
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            except Exception as e:
                print(f"Failed to elevate privileges: {e}")
                print("Please run the script as administrator manually.")
                sys.exit(1)
    
    # Check directory permissions
    if not get_folder_permissions(current_dir):
        print(f"\nNo write permissions in {current_dir}")
        print("Please ensure you have write permissions to the project directory.")
        sys.exit(1)
    
    # Try to create venv directory if it doesn't exist
    if not venv_dir.exists():
        try:
            venv_dir.mkdir(parents=True)
            print("\nSuccessfully created venv directory.")
        except Exception as e:
            print(f"\nError creating venv directory: {e}")
            print("Please ensure you have write permissions or run as administrator.")
            sys.exit(1)
    
    # Check venv directory permissions
    if not get_folder_permissions(venv_dir):
        print(f"\nNo write permissions in {venv_dir}")
        print("Please ensure you have write permissions to the venv directory.")
        sys.exit(1)
    
    print("\nAll permission checks passed!")
    print("You can now run setup_environment.py")

if __name__ == "__main__":
    main()