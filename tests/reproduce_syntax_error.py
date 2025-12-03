import sys
import os
import csv
import subprocess
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from automator import Automator

def reproduce_syntax_error():
    print("--- Reproducing Syntax Error ---")
    
    actions_file = "tests/temp_syntax_error.csv"
    log_file = "tests/reproduce_syntax_error.log"
    
    # Case 1: Variable with space, used without quotes in condition
    # var = "Hello World"
    # If {var} == 'Hello World' -> If Hello World == 'Hello World' -> Syntax Error
    
    rows = [
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "status = Hello World"},
        {"TargetApp": "", "Key": "", "Action": "If", "Value": "{status} == 'Hello World'"},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result = Match"},
        {"TargetApp": "", "Key": "", "Action": "Else", "Value": ""},
        {"TargetApp": "", "Key": "", "Action": "SetVariable", "Value": "result = NoMatch"},
        {"TargetApp": "", "Key": "", "Action": "EndIf", "Value": ""},
        {"TargetApp": "", "Key": "", "Action": "Exit", "Value": ""}
    ]
    
    with open(actions_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
        writer.writeheader()
        writer.writerows(rows)
        
    print("Created temp actions file.")
    
    app = Automator([actions_file], log_file=log_file, log_level="DEBUG")
    
    try:
        app.load_actions()
        app.run()
    except Exception as e:
        print(f"Caught expected exception: {e}")
        
    # Close logger handlers to release file
    for handler in app.logger.handlers[:]:
        handler.close()
        app.logger.removeHandler(handler)
    import logging
    logging.shutdown()
    time.sleep(0.5) # Wait for file release
    
    # Check log for SyntaxError
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        if "Condition evaluation failed" in log_content and "SyntaxError" in log_content:
            print("PASS: Reproduced SyntaxError as expected.")
        else:
            print("FAIL: Did not reproduce SyntaxError.")
            print(log_content)

    if os.path.exists(actions_file): os.remove(actions_file)
    if os.path.exists(log_file): os.remove(log_file)

if __name__ == "__main__":
    reproduce_syntax_error()
