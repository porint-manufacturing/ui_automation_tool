import uiautomation as auto
import subprocess
import time

def debug_methods():
    print("Launching Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(2)
    
    notepad = auto.WindowControl(searchDepth=1, ClassName='Notepad')
    if not notepad.Exists(maxSearchSeconds=3):
        notepad = auto.WindowControl(searchDepth=1, Name='無題 - メモ帳')
        
    print(f"Notepad: {notepad.Name}")
    
    children = notepad.GetChildren()
    if not children:
        print("No children found!")
        return
        
    child = children[0]
    print(f"Target Child: {child.ControlTypeName} ({child.ClassName})")
    
    # Test 1: Generic Control() method
    print("\n--- Test 1: Generic Control(ControlTypeName=...) ---")
    try:
        t1 = notepad.Control(ControlTypeName=child.ControlTypeName, ClassName=child.ClassName, searchDepth=1, foundIndex=1)
        print(f"Exists: {t1.Exists(maxSearchSeconds=1)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Specific Method via getattr
    print(f"\n--- Test 2: Specific {child.ControlTypeName}() method ---")
    try:
        method = getattr(notepad, child.ControlTypeName)
        t2 = method(ClassName=child.ClassName, searchDepth=1)
        print(f"Exists: {t2.Exists(maxSearchSeconds=1)}")
    except Exception as e:
        print(f"Error: {e}")

    notepad.Close()

if __name__ == "__main__":
    debug_methods()
