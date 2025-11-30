import subprocess
import time
import uiautomation as auto
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inspector import Inspector

def find_legacy_paths():
    print("Launching Calculator...")
    subprocess.Popen("calc.exe")
    time.sleep(2)
    
    calc_window = auto.WindowControl(searchDepth=1, Name="電卓")
    if not calc_window.Exists(maxSearchSeconds=3):
        calc_window = auto.WindowControl(searchDepth=1, RegexName=".*Calculator.*")
    
    if not calc_window.Exists():
        print("Calculator window not found.")
        return

    inspector = Inspector()
    
    targets = [
        {"type": "ButtonControl", "Name": "5"},
        {"type": "ButtonControl", "Name": "プラス"}, # or Plus
        {"type": "ButtonControl", "Name": "3"},
        {"type": "ButtonControl", "Name": "等号"}, # or Equals
        {"type": "TextControl", "AutomationId": "CalculatorExpression"},
        {"type": "TextControl", "AutomationId": "CalculatorResults"},
        {"type": "ButtonControl", "AutomationId": "TogglePaneButton"},
        # Menu items might be tricky if not open, but let's try to find them if possible or skip
    ]

    print("\n--- Legacy Mapping (Global Index) ---")
    with open("legacy_paths.txt", "w", encoding="utf-8") as f:
        for target in targets:
            control = None
            name_key = target.get("Name") or target.get("AutomationId")
            
            if "AutomationId" in target:
                control = calc_window.Control(ControlTypeName=target["type"], AutomationId=target["AutomationId"], searchDepth=5)
            elif "Name" in target:
                control = calc_window.Control(ControlTypeName=target["type"], Name=target["Name"], searchDepth=5)
                if not control.Exists() and target["Name"] == "プラス":
                     control = calc_window.Control(ControlTypeName=target["type"], Name="Plus", searchDepth=5)
                if not control.Exists() and target["Name"] == "等号":
                     control = calc_window.Control(ControlTypeName=target["type"], Name="Equals", searchDepth=5)

            if control and control.Exists():
                # Calculate Global Index relative to calc_window
                class_name = control.ClassName
                control_type = control.ControlTypeName
                
                print(f"Calculating global index for {name_key} ({control_type}, Class='{class_name}')...")
                
                # Find all matches from window
                matches = calc_window.GetChildren() # Start with children? No, need descendants.
                # uiautomation doesn't have a simple "GetAllDescendants" that filters by type/class efficiently without walking.
                # But we can use GetFirstChild/GetNextSibling loop or WalkControl.
                # Or simply loop with foundIndex until we find it?
                
                global_index = 0
                found = False
                
                # We can use a loop with foundIndex=1, 2, 3... until we match the control
                # This is slow but accurate.
                idx = 1
                while True:
                    # Search params
                    params = {"ControlTypeName": control_type, "foundIndex": idx}
                    if class_name:
                        params["ClassName"] = class_name
                    
                    candidate = calc_window.Control(**params)
                    if not candidate.Exists(0, 0): # Don't wait
                        break
                    
                    if auto.ControlsAreSame(candidate, control):
                        global_index = idx
                        found = True
                        break
                    
                    idx += 1
                    if idx > 100: # Safety break
                        print("  Index too high, stopping.")
                        break
                
                if found:
                    # Construct legacy key
                    props = []
                    if class_name:
                        props.append(f"ClassName='{class_name}'")
                    props.append(f"foundIndex={global_index}")
                    
                    props_str = "(" + ", ".join(props) + ")"
                    legacy_key = f"{target['type']}{props_str}"
                    
                    f.write(f"{name_key},{legacy_key}\n")
                    print(f"Mapped {name_key} -> {legacy_key}")
                else:
                    f.write(f"{name_key},NOT_FOUND_GLOBAL\n")
                    print(f"Failed to find global index for {name_key}")
            else:
                f.write(f"{name_key},NOT_FOUND\n")
                print(f"Failed to map {name_key}")

if __name__ == "__main__":
    find_legacy_paths()
