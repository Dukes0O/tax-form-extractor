import os
import sys
import zipfile
import requests
import shutil
from pathlib import Path

def install_poppler_for_windows():
    """
    Download and install Poppler for Windows
    """
    print("Installing Poppler for Windows...")
    
    # Create a directory for Poppler
    poppler_dir = Path("./poppler")
    poppler_dir.mkdir(exist_ok=True)
    
    # Download Poppler
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
    zip_path = poppler_dir / "poppler.zip"
    
    print(f"Downloading Poppler from {poppler_url}...")
    response = requests.get(poppler_url, stream=True)
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Extract the ZIP file
    print("Extracting Poppler...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(poppler_dir)
    
    # Add Poppler to PATH
    poppler_bin = poppler_dir / "poppler-23.11.0" / "Library" / "bin"
    poppler_bin_str = str(poppler_bin.resolve())
    
    # Check if Poppler is already in PATH
    path_env = os.environ.get('PATH', '')
    if poppler_bin_str not in path_env:
        print(f"Adding Poppler to PATH: {poppler_bin_str}")
        os.environ['PATH'] = poppler_bin_str + os.pathsep + path_env
    
    print("Poppler installation complete!")
    print(f"Poppler binaries are located at: {poppler_bin_str}")
    print("Please add this path to your system PATH environment variable for permanent use.")
    
    # Clean up
    os.remove(zip_path)
    
    return poppler_bin_str

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        poppler_path = install_poppler_for_windows()
        print("\nTo test if Poppler is working, run the following command in a new terminal:")
        print(f"set PATH={poppler_path};%PATH% && pdftoppm -v")
    else:
        print("This script is for Windows only. For other platforms, please install Poppler using your package manager.")
        print("For example, on Ubuntu/Debian: sudo apt-get install poppler-utils")
