import uiautomation as auto
import subprocess
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inspector import Inspector

def verify_modes():
    print("Launching Notepad...")
    subprocess.Popen("notepad.exe")
    time.sleep(2)
    
    try:
        notepad = auto.WindowControl(searchDepth=1, RegexName=".*メモ帳.*")
        if not notepad.Exists(maxSearchSeconds=3):
            notepad = auto.WindowControl(searchDepth=1, RegexName=".*Notepad.*")
            
        if not notepad.Exists():
            print("Notepad not found.")
            return False

        # Find the text area (DocumentControl)
        # In Win11 it might be RichEditD2DPT
        doc = notepad.DocumentControl(searchDepth=5)
        if not doc.Exists():
            doc = notepad.EditControl(searchDepth=5)
            
        if not doc.Exists():
            print("Text area not found.")
            return False
        
        print(f"Target Control: {doc.Name} ({doc.ClassName})")
        
        # Test Modern Mode
        print("\n--- Testing Modern Mode ---")
        inspector_modern = Inspector(mode="modern")
        path_modern = inspector_modern.get_rpa_path(doc)
        print(f"Modern Path: {path_modern}")
        
        # Test Legacy Mode
        print("\n--- Testing Legacy Mode ---")
        inspector_legacy = Inspector(mode="legacy")
        path_legacy = inspector_legacy.get_rpa_path(doc)
        print(f"Legacy Path: {path_legacy}")
        
        # Verify Legacy Mode contains ClassName and foundIndex
        if "foundIndex" in path_legacy and "ClassName" in path_legacy:
            print("Legacy Mode Verification: PASS")
            return True
        else:
            print("Legacy Mode Verification: FAIL")
            return False
            
    finally:
        # Close notepad
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'notepad.exe'], 
                          capture_output=True, timeout=5)
        except:
            pass

if __name__ == "__main__":
    success = verify_modes()
    sys.exit(0 if success else 1)
