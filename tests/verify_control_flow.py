import sys
import os
import csv
import subprocess
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from automator import Automator

def verify_control_flow():
    print("--- Testing Control Flow ---")
    
    actions_file = "tests/temp_control_flow.csv"
    log_file = "tests/verify_control_flow.log"
    
    # Define test cases in a single CSV
    # 1. SetVariable
    # 2. If (True) -> Execute -> EndIf
    # 3. If (False) -> Else -> Execute -> EndIf
    # 4. Loop (Count 3)
    # 5. Loop (Condition)
    
    rows = [
        # 1. SetVariable
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "test_var = 100"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "status = 'START'"},
        
        # 2. If (True)
        {"TargetApp": "", "Key": "", "Action": "If", "Value": "{test_var} == 100"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result_if_true = 'PASS'"},
        {"TargetApp": "", "Key": "", "Action": "Else", "Value": ""},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result_if_true = 'FAIL'"},
        {"TargetApp": "", "Key": "", "Action": "EndIf", "Value": ""},
        
        # 3. If (False)
        {"TargetApp": "", "Key": "", "Action": "If", "Value": "{test_var} == 999"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result_if_false = 'FAIL'"},
        {"TargetApp": "", "Key": "", "Action": "Else", "Value": ""},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result_if_false = 'PASS'"},
        {"TargetApp": "", "Key": "", "Action": "EndIf", "Value": ""},
        
        # 4. Loop (Count 3)
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "loop_count = 0"},
        {"TargetApp": "", "Key": "", "Action": "Loop", "Value": "3"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "loop_count = {loop_count} + 1"},
        {"TargetApp": "", "Key": "", "Action": "EndLoop", "Value": ""},
        
        # 5. Loop (Condition) - Loop until count is 5 (starts at 3 from previous loop)
        {"TargetApp": "", "Key": "", "Action": "Loop", "Value": "{loop_count} < 5"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "loop_count = {loop_count} + 1"},
        {"TargetApp": "", "Key": "", "Action": "EndLoop", "Value": ""},
        
        # 6. Nested Loop
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "outer = 0"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "inner_total = 0"},
        {"TargetApp": "", "Key": "", "Action": "Loop", "Value": "2"}, # Outer loop 2 times
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "outer = {outer} + 1"},
        {"TargetApp": "", "Key": "", "Action": "Loop", "Value": "3"}, # Inner loop 3 times
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "inner_total = {inner_total} + 1"},
        {"TargetApp": "", "Key": "", "Action": "EndLoop", "Value": ""},
        {"TargetApp": "", "Key": "", "Action": "EndLoop", "Value": ""},
        
        # Verify results by printing to log (using a dummy action or just checking vars in log if we logged them)
        # We can use a custom action or just rely on SetVariable logging.
        # But SetVariable logs "Set variable 'name' to 'value'".
        # So we can check the log for the final values.
    ]
    
    with open(actions_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
        writer.writeheader()
        writer.writerows(rows)
        
    print("Created temp actions file.")
    
    cmd = [
        sys.executable, "automator.py",
        actions_file,
        "--log-file", log_file,
        "--log-level", "INFO"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            
        # Checks
        checks = [
            "Set variable 'result_if_true' to 'PASS'",
            "Set variable 'result_if_false' to 'PASS'",
            "Set variable 'loop_count' to '3'", # After first loop
            "Set variable 'loop_count' to '5'", # After second loop
            "Set variable 'outer' to '2'",
            "Set variable 'inner_total' to '6'" # 2 * 3 = 6
        ]
        
        all_passed = True
        for check in checks:
            # We need to find the LAST occurrence of the variable setting to be sure?
            # Or just ensure it exists.
            # For loop_count, it will be set to 1, 2, 3... so '3' will be there.
            # But we want to ensure it reached 3.
            if check in log_content:
                print(f"PASS: Found '{check}'")
            else:
                print(f"FAIL: Missing '{check}'")
                all_passed = False
                
        if all_passed:
            print("Control Flow Verification: PASS")
            if os.path.exists(log_file): os.remove(log_file)
        else:
            print("Control Flow Verification: FAIL")
            print("--- Log Content ---")
            print(log_content)
            print("-------------------")
            
    except subprocess.CalledProcessError as e:
        print(f"Control Flow Verification: FAIL - Process error {e}")
    except Exception as e:
        print(f"Control Flow Verification: FAIL - {e}")
    finally:
        if os.path.exists(actions_file): os.remove(actions_file)

if __name__ == "__main__":
    verify_control_flow()
