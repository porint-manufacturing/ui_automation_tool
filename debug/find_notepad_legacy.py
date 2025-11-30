import subprocess
import time
import uiautomation as auto
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inspector import Inspector

def find_notepad_legacy():
    print("Launching Notepad...")
    subprocess.Popen("notepad.exe")
    time.sleep(3)
    
    notepad = auto.WindowControl(searchDepth=1, RegexName=".*メモ帳.*")
    if not notepad.Exists(maxSearchSeconds=5):
        notepad = auto.WindowControl(searchDepth=1, RegexName=".*Notepad.*")
    
    if not notepad.Exists():
        print("Notepad window not found.")
        return

    inspector = Inspector()
    
    # Find the main text area. 
    # In Win11 Notepad, it might be DocumentControl or EditControl.
    # Let's search for both.
    print("Searching for text area...")
    
    # Try DocumentControl
    doc = notepad.DocumentControl(searchDepth=5)
    if doc.Exists():
        print(f"Found DocumentControl: {inspector.get_rpa_path(doc)}")
    else:
        print("DocumentControl not found.")
        
    # Try EditControl
    edit = notepad.EditControl(searchDepth=5)
    if edit.Exists():
        print(f"Found EditControl: {inspector.get_rpa_path(edit)}")
    else:
        print("EditControl not found.")

if __name__ == "__main__":
    find_notepad_legacy()
