import uiautomation as auto
import subprocess
import time

def debug_calc_path():
    print("Launching Calc...")
    subprocess.Popen("calc.exe", shell=True)
    time.sleep(2)
    
    print("Searching for Calculator window...")
    # Try to find the window exactly as automator does
    win = auto.WindowControl(searchDepth=1, Name='電卓')
    if not win.Exists(maxSearchSeconds=3):
        # Try English name just in case
        win = auto.WindowControl(searchDepth=1, Name='Calculator')
        
    if not win.Exists():
        print("FAIL: Calculator window not found.")
        return

    print(f"Window found: {win.Name} (ClassName: {win.ClassName})")
    
    # Try to find NavView at depth 1
    print("Searching for NavView at depth 1...")
    nav_view = win.CustomControl(searchDepth=1, AutomationId='NavView')
    if nav_view.Exists(maxSearchSeconds=1):
        print("PASS: NavView found at depth 1.")
    else:
        print("FAIL: NavView NOT found at depth 1.")
        
        # Try deeper search
        print("Searching for NavView at depth 2...")
        nav_view = win.CustomControl(searchDepth=2, AutomationId='NavView')
        if nav_view.Exists(maxSearchSeconds=1):
            print("PASS: NavView found at depth 2.")
        else:
            print("FAIL: NavView NOT found at depth 2.")
            
            # Try recursive
            print("Searching for NavView recursively...")
            nav_view = win.CustomControl(AutomationId='NavView')
            if nav_view.Exists(maxSearchSeconds=1):
                print("PASS: NavView found recursively.")
                # Check actual depth
                # We can't easily check depth without walking up, but we know it's > 2
            else:
                print("FAIL: NavView NOT found recursively.")

if __name__ == "__main__":
    auto.SetProcessDpiAwareness(2)
    debug_calc_path()
