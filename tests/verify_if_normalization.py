import sys
import os
import csv
import shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from automator import Automator

def verify_if_normalization():
    print("--- Testing IF Normalization ---")
    
    actions_file = "tests/temp_if_norm.csv"
    log_file = "tests/verify_if_norm.log"
    
    # Use IF (uppercase)
    rows = [
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "status = OK"},
        {"TargetApp": "", "Key": "", "Action": "IF", "Value": "'{status}' == 'OK'"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result = Pass"},
        {"TargetApp": "", "Key": "", "Action": "ELSE", "Value": ""},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result = Fail"},
        {"TargetApp": "", "Key": "", "Action": "ENDIF", "Value": ""},
        {"TargetApp": "", "Key": "", "Action": "Exit", "Value": ""}
    ]
    
    with open(actions_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
        writer.writeheader()
        writer.writerows(rows)
        
    app = Automator([actions_file], log_file=log_file, log_level="DEBUG")
    
    try:
        app.load_actions()
        app.run()
    except Exception as e:
        print(f"FAIL: Exception {e}")
        
    # Check result variable
    if app.variables.get("result") == "Pass":
        print("PASS: IF/ELSE/ENDIF normalization worked.")
    else:
        print(f"FAIL: Result is {app.variables.get('result')}")

    # Cleanup
    for handler in app.logger.handlers[:]:
        handler.close()
        app.logger.removeHandler(handler)
    import logging
    logging.shutdown()
    
    if os.path.exists(actions_file): os.remove(actions_file)
    if os.path.exists(log_file): os.remove(log_file)

if __name__ == "__main__":
    verify_if_normalization()
