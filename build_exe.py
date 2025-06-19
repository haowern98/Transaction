#!/usr/bin/env python3
"""
Simple build script for Transaction Matcher EXE
Creates ONLY the single executable file
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller found")
        return True
    except ImportError:
        print("❌ Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
        return True

def clean_previous():
    """Clean only what's necessary"""
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    # Remove old spec files
    for spec in Path('.').glob('*.spec'):
        spec.unlink()

def build_single_exe():
    """Build only the EXE file"""
    print("🔨 Building TransactionMatcher.exe...")
    
    cmd = [
        "pyinstaller",
        "src/gui_launcher.py",
        "--onefile",                    # Single EXE only
        "--name", "TransactionMatcher", # EXE name
        "--windowed",                   # No console window
        "--add-data", "src;src",        # Include source code
        "--hidden-import", "PyQt5.sip", # PyQt5 compatibility
        "--clean"                       # Clean build
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Build failed!")
        return False

def main():
    """Main build process"""
    print("🚀 Simple EXE Builder - TransactionMatcher")
    print("=" * 45)
    
    # Check requirements
    if not Path("src/gui_launcher.py").exists():
        print("❌ Run from project root (folder with 'src' directory)")
        sys.exit(1)
    
    if not check_pyinstaller():
        sys.exit(1)
    
    # Clean and build
    clean_previous()
    
    if not build_single_exe():
        sys.exit(1)
    
    # Check result
    exe_path = Path("dist/TransactionMatcher.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n🎉 Success!")
        print(f"📁 Created: {exe_path}")
        print(f"📏 Size: {size_mb:.1f} MB")
        print(f"\n✅ Ready to distribute: Just share TransactionMatcher.exe")
    else:
        print("❌ EXE not found!")
        sys.exit(1)

if __name__ == "__main__":
    main()