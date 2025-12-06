import uiautomation as auto
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inspector import Inspector

def verify_inspector():
    print("Launching Calc...")
    import subprocess
    subprocess.Popen("calc.exe", shell=True)
    import time
    time.sleep(2)
    
    try:
        win = auto.WindowControl(searchDepth=1, Name='電卓')
        if not win.Exists(maxSearchSeconds=3):
            win = auto.WindowControl(searchDepth=1, Name='Calculator')
            
        if not win.Exists():
            print("FAIL: Calculator window not found.")
            return False

        # Find '5' button
        btn = win.ButtonControl(AutomationId='num5Button', searchDepth=0xFFFFFFFF)
        if not btn.Exists(maxSearchSeconds=2):
            print("FAIL: '5' button not found.")
            return False
            
        print(f"Found button: {btn.Name}")
        
        # Test Inspector
        inspector = Inspector(mode="modern")
        path = inspector.get_rpa_path(btn)
        print(f"Generated Path: {path}")
        
        # Verify path is short
        if "->" in path:
            print("FAIL: Path contains '->' (too long)")
            return False
        elif "AutomationId='num5Button'" in path:
            print("PASS: Path is short and contains AutomationId")
            return True
        else:
            print("FAIL: Path does not contain AutomationId")
            return False
            
    finally:
        # Close calculator
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'CalculatorApp.exe'], 
                          capture_output=True, timeout=5)
        except:
            pass

if __name__ == "__main__":
    auto.SetProcessDpiAwareness(2)
    success = verify_inspector()
    sys.exit(0 if success else 1)
