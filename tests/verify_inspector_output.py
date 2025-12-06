import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inspector import Inspector
import os
import uiautomation as auto

def verify_output():
    print("--- Testing CSV Output ---")
    inspector_csv = Inspector(output="csv")
    inspector_csv.recorded_items = [
        {"TargetApp": "TestApp", "Key": "TestKey1", "Action": "", "Value": ""},
        {"TargetApp": "TestApp", "Key": "TestKey2", "Action": "", "Value": ""}
    ]
    inspector_csv.finalize()
    
    # Check if file exists
    files = [f for f in os.listdir(".") if f.startswith("inspector_") and f.endswith(".csv")]
    if files:
        print(f"CSV File Created: {files[-1]}")
    else:
        print("CSV File NOT Created")
        return False

    print("\n--- Testing Clipboard Output ---")
    inspector_clip = Inspector(output="clipboard")
    inspector_clip.recorded_items = [
        {"TargetApp": "ClipApp", "Key": "ClipKey", "Action": "", "Value": ""}
    ]
    inspector_clip.finalize()
    
    clip_text = auto.GetClipboardText()
    print(f"Clipboard Content:\n{clip_text}")
    
    if "ClipKey" in clip_text:
        print("Clipboard Verification: PASS")
        return True
    else:
        print("Clipboard Verification: FAIL")
        return False

if __name__ == "__main__":
    success = verify_output()
    sys.exit(0 if success else 1)
