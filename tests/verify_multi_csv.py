import sys
import os
import csv
import subprocess
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from automator import Automator

def verify_multi_csv():
    print("--- Testing Multiple CSV Import ---")
    
    # Create temp files
    files = {
        "setup.csv": [
            {"TargetApp": "", "Key": "", "Action": "Launch", "Value": "notepad.exe"},
            {"TargetApp": "", "Key": "", "Action": "Wait", "Value": "3"}
        ],
        "main.csv": [
            {"TargetApp": "メモ帳", "Key": "Alias_Text", "Action": "SendKeys", "Value": "Multi CSV Test"}
        ],
        "teardown.csv": [
            {"TargetApp": "メモ帳", "Key": "", "Action": "Exit", "Value": ""}
        ],
        "common_alias.csv": [
            {"AliasName": "Alias_Text", "RPA_Path": "DocumentControl(searchDepth=5)"}
        ],
        "override_alias.csv": [
            # This should NOT be used if we load common_alias AFTER override_alias?
            # Or if we load common then override, override wins.
            # Let's test override: Define Alias_Text in both, but different paths?
            # Actually, let's just define a new alias here to verify merging.
            {"AliasName": "Alias_Unused", "RPA_Path": "ButtonControl(Name='Unused')"}
        ]
    }
    
    # Write files
    for filename, rows in files.items():
        path = os.path.join("tests", filename)
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            if "AliasName" in rows[0]:
                writer = csv.DictWriter(f, fieldnames=["AliasName", "RPA_Path"])
            else:
                writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
            writer.writeheader()
            writer.writerows(rows)
            
    print("Created temp CSV files.")
    
    log_file = "tests/verify_multi_csv.log"
    
    # Command: python automator.py tests/setup.csv tests/main.csv tests/teardown.csv --aliases tests/common_alias.csv tests/override_alias.csv
    cmd = [
        sys.executable, "automator.py",
        "tests/setup.csv", "tests/main.csv", "tests/teardown.csv",
        "--aliases", "tests/common_alias.csv", "tests/override_alias.csv",
        "--log-file", log_file,
        "--log-level", "DEBUG"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        # Check log
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            
        # Verify:
        # 1. Loading messages for all files
        # 2. Alias resolution
        # 3. Execution of actions from all files
        
        checks = [
            "Loading actions from tests/setup.csv",
            "Loading actions from tests/main.csv",
            "Loading actions from tests/teardown.csv",
            "Loading aliases from tests/common_alias.csv",
            "Loading aliases from tests/override_alias.csv",
            "Resolved alias 'Alias_Text'",
            "Sending keys: Multi CSV Test"
        ]
        
        all_passed = True
        for check in checks:
            if check in log_content:
                print(f"PASS: Found '{check}'")
            else:
                print(f"FAIL: Missing '{check}'")
                all_passed = False
        
        if all_passed:
            print("Multi CSV Verification: PASS")
            if os.path.exists(log_file): os.remove(log_file)
        else:
            print("Multi CSV Verification: FAIL")
            print("--- Log Content ---")
            print(log_content)
            print("-------------------")
            
    except subprocess.CalledProcessError as e:
        print(f"Multi CSV Verification: FAIL - Process error {e}")
    except Exception as e:
        print(f"Multi CSV Verification: FAIL - {e}")
    finally:
        # Cleanup
        for filename in files.keys():
            path = os.path.join("tests", filename)
            if os.path.exists(path): os.remove(path)
        # Log file cleanup moved to success block
        subprocess.run("taskkill /f /im notepad.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    verify_multi_csv()
