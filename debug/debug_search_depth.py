import uiautomation as auto
import subprocess
import time

def debug_search_depth():
    print("Launching Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(2)
    
    notepad = auto.WindowControl(searchDepth=1, ClassName='Notepad')
    if not notepad.Exists(maxSearchSeconds=3):
        notepad = auto.WindowControl(searchDepth=1, Name='無題 - メモ帳')
        
    print(f"Notepad: {notepad.Name}")
    
    # Find direct child Pane
    # Win11: Notepad -> NotepadTextBox (Pane)
    # Win10: Notepad -> Edit
    
    children = notepad.GetChildren()
    print("Children:")
    for c in children:
        print(f"  {c.ControlTypeName} ({c.ClassName})")
        
    print("\nTesting Control(searchDepth=1)...")
    # Pick the first child
    first_child = children[0]
    
    target = notepad.Control(
        ControlTypeName=first_child.ControlTypeName,
        ClassName=first_child.ClassName,
        searchDepth=1,
        foundIndex=1
    )
    
    if target.Exists(maxSearchSeconds=1):
        print("Found with searchDepth=1: PASS")
    else:
        print("Found with searchDepth=1: FAIL")

    notepad.Close()

if __name__ == "__main__":
    debug_search_depth()
