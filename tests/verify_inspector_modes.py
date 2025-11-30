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
    
    notepad = auto.WindowControl(searchDepth=1, RegexName=".*メモ帳.*")
    if not notepad.Exists(maxSearchSeconds=3):
        notepad = auto.WindowControl(searchDepth=1, RegexName=".*Notepad.*")
        
    if not notepad.Exists():
        print("Notepad not found.")
        return

    # Find the text area (DocumentControl)
    # In Win11 it might be RichEditD2DPT
    doc = notepad.DocumentControl(searchDepth=5)
    if not doc.Exists():
        doc = notepad.EditControl(searchDepth=5)
        
    if not doc.Exists():
        print("Text area not found.")
        return
        
    print(f"Target Control: {doc.Name} ({doc.ClassName})")
    
    # Test Modern Mode
    print("\n--- Testing Modern Mode ---")
    inspector_modern = Inspector(mode="modern")
    path_modern = inspector_modern.get_rpa_path(doc)
    print(f"Modern Path: {path_modern}")
    
    # Expectation: Should contain Name if available, or ClassName. 
    # If Name is "テキスト エディター" (Win11), it should be there.
    
    # Test Legacy Mode
    print("\n--- Testing Legacy Mode ---")
    inspector_legacy = Inspector(mode="legacy")
    path_legacy = inspector_legacy.get_rpa_path(doc)
    print(f"Legacy Path: {path_legacy}")
    
    # Expectation: Should NOT contain Name (unless we changed logic), 
    # MUST contain ClassName and foundIndex.
    
    if "foundIndex" in path_legacy and "ClassName" in path_legacy:
        print("Legacy Mode Verification: PASS")
    else:
        print("Legacy Mode Verification: FAIL")

if __name__ == "__main__":
    verify_modes()
