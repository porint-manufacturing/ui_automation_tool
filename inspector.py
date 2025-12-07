import uiautomation as auto
import time
import keyboard
import argparse
import csv
import datetime
import sys
import io
import ctypes
import os

# Enable High DPI Awareness to ensure correct coordinates
try:
    auto.SetProcessDpiAwareness(2) # Process_PerMonitorDpiAware
except Exception:
    pass

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from automator.inspector.path_generator import PathGenerator
from automator.inspector.click_handler import ClickHandler
from automator.inspector.output_handler import OutputHandler


class Inspector:
    def __init__(self, mode="modern", output="clipboard"):
        self.mode = mode
        self.output = output
        self.recorded_items = []
        self.path_generator = PathGenerator(mode=mode)
        self.click_handler = ClickHandler()
        self.output_handler = OutputHandler(output_mode=output)
        print(f"UI Inspector initialized (Mode: {mode}, Output: {output})")



    def get_rpa_path(self, control):
        """
        Generates a robust RPA path for the control.
        Delegates to PathGenerator.
        """
        return self.path_generator.get_rpa_path(control)

    def run(self):
        print("UI Inspector started.")
        
        if self.output == "interactive_alias":
            self.run_interactive()
        else:
            self.run_normal()

        self.finalize()

    def run_interactive(self):
        print("Interactive Alias Mode")
        print("Type the alias name and press Enter, then click the target element.")
        print("You can use Left Click or Right Click (Right Click won't trigger the element).")
        print("Type 'q' or 'exit' to finish.")
        print("-" * 50)

        while True:
            try:
                alias_name = input("\n[Interactive] Enter Alias Name (or 'q' to finish): ").strip()
            except EOFError:
                break
                
            if alias_name.lower() in ['q', 'exit']:
                break
            
            if not alias_name:
                print("  >> Name cannot be empty.")
                continue

            print(f"  >> Click the element for '{alias_name}' (Press ESC to cancel this item)...")
            
            result = self.wait_for_click()
            if not result:
                print("  >> Cancelled.")
                continue
            
            control, x, y = result
            path = self.get_rpa_path(control)
            print(f"  >> Captured: {path}")
            
            self.recorded_items.append({
                "AliasName": alias_name,
                "RPA_Path": path
            })

    def run_normal(self):
        print("Hover over an element and CLICK (Left or Right Click) to inspect/record.")
        print("Press 'ESC' to finish and output.")
        print("-" * 50)

        last_element = None
        
        while True:
            if keyboard.is_pressed('esc'):
                print("\nFinishing...")
                break
                
            # Check for left click (0x01) or right click (0x02)
            if (ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000) or \
               (ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000):
                x, y = auto.GetCursorPos()
                control = auto.ControlFromPoint(x, y)
                
                if control:
                    # Debounce
                    if not last_element or not auto.ControlsAreSame(control, last_element):
                        self.inspect_element(control, x, y)
                        last_element = control
                        while (ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000) or \
                              (ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000):
                            time.sleep(0.05)
                else:
                    time.sleep(0.1)
            else:
                last_element = None 
                time.sleep(0.05)

    def wait_for_click(self):
        """Waits for a left or right click. Delegates to ClickHandler."""
        return self.click_handler.wait_for_click()

    def inspect_element(self, control, x, y):
        print(f"\n[Clicked at {x}, {y}] Inspecting...")
        
        # Basic info
        print(f"  Name: {control.Name}")
        print(f"  Type: {control.ControlTypeName}")
        print(f"  Class: {control.ClassName}")
        print(f"  AutoId: {control.AutomationId}")
        
        # Get TargetApp (Window Name)
        # We use the TopLevelControl's Name as the TargetApp identifier.
        # This corresponds to the 'Name' or 'RegexName' used in Automator's find_window.
        root = control.GetTopLevelControl()
        target_app = root.Name if root else "Unknown"
        print(f"  TargetApp: {target_app}")
        
        # Generate Path
        rpa_path = self.get_rpa_path(control)
        print(f"  RPA_Path: {rpa_path}")
        
        # Record
        if self.output in ["csv", "clipboard", "alias"]:
            self.recorded_items.append({
                "TargetApp": target_app,
                "Key": rpa_path,
                "Action": "",
                "Value": ""
            })
            print(f"  -> Recorded ({len(self.recorded_items)} items)")

    def finalize(self):
        """Output recorded items. Delegates to OutputHandler."""
        self.output_handler.finalize(self.recorded_items)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UI Inspector for Automator")
    parser.add_argument("--mode", choices=["modern", "legacy"], default="modern", help="Inspection mode")
    parser.add_argument("--output", choices=["normal", "csv", "clipboard", "alias", "interactive_alias"], default="clipboard", help="Output mode")
    
    args = parser.parse_args()
    
    inspector = Inspector(mode=args.mode, output=args.output)
    inspector.run()
