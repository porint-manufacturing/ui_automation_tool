
import sys
import os
import subprocess
import time
import uiautomation as auto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from automator import Automator

def verify_chained_path():
    automator = Automator()
    print(f"DEBUG: Automator type: {type(automator)}")
    print(f"DEBUG: Automator dir: {dir(automator)}")
    
    print("Launching Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(5)
    
    notepad = auto.WindowControl(searchDepth=1, ClassName='Notepad')
    if not notepad.Exists(maxSearchSeconds=5):
        notepad = auto.WindowControl(searchDepth=1, Name='無題 - メモ帳')
    if not notepad.Exists(maxSearchSeconds=5):
        print("Notepad not found.")
        return

    print(f"Notepad found: {notepad.Name}")
    
    # Construct a chained path manually that matches what Inspector generates
    # Window -> Pane -> Document
    
    # Let's inspect the structure first to be sure.
    doc = notepad.DocumentControl()
    if not doc.Exists():
        print("Document control not found via simple search.")
        return

    # Get parent of doc
    parent = doc.GetParentControl()
    print(f"Parent of Doc: {parent.ControlTypeName} ({parent.ClassName})")
    
    # Construct path: Parent -> Doc
    # We use searchDepth=1 to enforce shallow search.
    
    # Test 1: Simple Path (Descendant search)
    print("\n--- Test 1: Simple Path ---")
    path1 = f"{parent.ControlTypeName}(ClassName='{parent.ClassName}')"
    print(f"Path: {path1}")
    e1 = automator.find_element_by_path(notepad, path1)
    print(f"Result: {'Found' if e1 else 'Not Found'}")

    # Test 2: Path with searchDepth=1
    print("\n--- Test 2: Path with searchDepth=1 ---")
    path2 = f"{parent.ControlTypeName}(ClassName='{parent.ClassName}', searchDepth=1)"
    print(f"Path: {path2}")
    e2 = automator.find_element_by_path(notepad, path2)
    print(f"Result: {'Found' if e2 else 'Not Found'}")

    # Test 3: Chained Path
    print("\n--- Test 3: Chained Path ---")
    path3 = f"{parent.ControlTypeName}(ClassName='{parent.ClassName}', searchDepth=1) -> {doc.ControlTypeName}(ClassName='{doc.ClassName}', searchDepth=1)"
    print(f"Path: {path3}")
    e3 = automator.find_element_by_path(notepad, path3)
    print(f"Result: {'Found' if e3 else 'Not Found'}")

    notepad.Close()

if __name__ == "__main__":
    verify_chained_path()
