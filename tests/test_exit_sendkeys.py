import uiautomation as auto
import subprocess
import time

# Launch calculator
print("Launching calculator...")
calc = subprocess.Popen("calc.exe")
time.sleep(2)

# Find window
window = auto.WindowControl(searchDepth=1, Name="電卓")
if not window.Exists(maxSearchSeconds=3):
    window = auto.WindowControl(searchDepth=1, RegexName=".*Calculator.*")

if not window.Exists():
    print("Calculator not found")
    exit(1)

print(f"Found window: {window.Name}")

# Test window.SendKeys() vs auto.SendKeys()
print("\nTesting window.SendKeys('{Alt}{F4}')...")
window.SetFocus()
time.sleep(0.1)
window.SendKeys('{Alt}{F4}')
time.sleep(1)

# Check if closed
if not window.Exists(maxSearchSeconds=1):
    print("SUCCESS: Calculator closed using window.SendKeys()")
else:
    print("FAIL: Calculator still open")
    # Clean up
    subprocess.run(['taskkill', '/F', '/IM', 'CalculatorApp.exe'], capture_output=True)
