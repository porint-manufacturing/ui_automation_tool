import uiautomation as auto
import subprocess
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# This script emulates automator logic but doesn't import it directly.
# However, if it did, we would need this.
# It uses uiautomation directly.

def debug_indices():
    print("Launching Calculator...")
    subprocess.Popen("calc.exe")
    time.sleep(2)
    
    calc_window = auto.WindowControl(searchDepth=1, Name="電卓")
    if not calc_window.Exists(maxSearchSeconds=3):
        calc_window = auto.WindowControl(searchDepth=1, RegexName=".*Calculator.*")
    
    if not calc_window.Exists():
        print("Calculator window not found.")
        return

    print("Listing ButtonControls by foundIndex (1-50)...")
    for i in range(1, 51):
        try:
            # Emulate automator.py logic (implicit searchDepth)
            btn = calc_window.Control(ControlTypeName="ButtonControl", ClassName="Button", foundIndex=i)
            if btn.Exists(0, 0):
                print(f"Index {i}: Name='{btn.Name}', AutomationId='{btn.AutomationId}'")
            else:
                print(f"Index {i}: Not found")
                break
        except Exception as e:
            print(f"Index {i}: Error {e}")

if __name__ == "__main__":
    debug_indices()
