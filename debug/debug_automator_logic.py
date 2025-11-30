import uiautomation as auto
import subprocess
import time
import re

def debug_logic():
    print("Launching Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(2)
    
    notepad = auto.WindowControl(searchDepth=1, ClassName='Notepad')
    if not notepad.Exists(maxSearchSeconds=3):
        notepad = auto.WindowControl(searchDepth=1, Name='無題 - メモ帳')
        
    print(f"Notepad: {notepad.Name}")
    
    # Get child info for test
    children = notepad.GetChildren()
    child = children[0]
    print(f"Target Child: {child.ControlTypeName} ({child.ClassName})")
    
    # Simulate Automator logic
    path_string = f"{child.ControlTypeName}(ClassName='{child.ClassName}', searchDepth=1)"
    print(f"Path: {path_string}")
    
    parts = [p.strip() for p in path_string.split('->')]
    current = notepad
    
    for part in parts:
        print(f"Processing part: {part}")
        match = re.match(r"(\w+)(?:\((.*)\))?", part)
        control_type = match.group(1)
        props_str = match.group(2)
        
        search_params = {"ControlTypeName": control_type}
        found_index = 1
        
        if props_str:
            name_match = re.search(r"Name='([^']*)'", props_str)
            id_match = re.search(r"AutomationId='([^']*)'", props_str)
            class_match = re.search(r"ClassName='([^']*)'", props_str)
            index_match = re.search(r"foundIndex=(\d+)", props_str)
            depth_match = re.search(r"searchDepth=(\d+)", props_str)
            
            if name_match:
                search_params["Name"] = name_match.group(1)
            if id_match:
                search_params["AutomationId"] = id_match.group(1)
            if class_match:
                search_params["ClassName"] = class_match.group(1)
            if index_match:
                found_index = int(index_match.group(1))
            if depth_match:
                search_params["searchDepth"] = int(depth_match.group(1))

        print(f"  Params: {search_params}, Index: {found_index}")
        
        try:
            target = current.Control(
                foundIndex=found_index,
                **search_params
            )
            print(f"  Target Exists: {target.Exists(maxSearchSeconds=1)}")
            if target.Exists():
                current = target
            else:
                print("  Target NOT found")
        except Exception as e:
            print(f"  Error: {e}")

    notepad.Close()

if __name__ == "__main__":
    debug_logic()
