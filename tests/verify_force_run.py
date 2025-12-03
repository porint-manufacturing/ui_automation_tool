import subprocess
import os
import sys

def verify_force_run():
    print("=== Force Run Option Verification ===\n")
    
    # Create a test CSV with an intentional error
    test_actions = """TargetApp,Key,Action,Value
電卓,,Launch,calc.exe
電卓,,Wait,2
電卓,NonExistentElement,Click,
電卓,,Exit,"""
    
    test_file = "tests/temp_force_run_test.csv"
    
    with open(test_file, 'w', encoding='utf-8-sig') as f:
        f.write(test_actions)
    
    print("1. Testing default behavior (should stop on error)...")
    result1 = subprocess.run(
        [sys.executable, "automator.py", test_file],
        capture_output=True,
        text=True
    )
    
    if result1.returncode != 0:
        print("PASS: Stopped on error (exit code: {})".format(result1.returncode))
        if "Stopping execution due to error" in result1.stdout:
            print("PASS: Error message found in output")
        else:
            print("INFO: Error message not found, but exit code indicates failure")
    else:
        print("FAIL: Did not stop on error")
        return False
    
    print("\n2. Testing --force-run (should continue on error)...")
    result2 = subprocess.run(
        [sys.executable, "automator.py", test_file, "--force-run"],
        capture_output=True,
        text=True
    )
    
    # With --force-run, it should complete (exit code 0) even with errors
    if result2.returncode == 0:
        print("PASS: Continued execution despite error (exit code: 0)")
        if "Action failed" in result2.stdout:
            print("PASS: Error was logged but execution continued")
        else:
            print("INFO: No error logged (element might have been found)")
    else:
        print("FAIL: Stopped execution even with --force-run")
        return False
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("\n=== Force Run Verification: PASS ===")
    return True

if __name__ == "__main__":
    success = verify_force_run()
    sys.exit(0 if success else 1)
