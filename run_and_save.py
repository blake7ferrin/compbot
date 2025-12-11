"""Run the bot and save output to file."""
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from main import main

# Capture all output
output_buffer = io.StringIO()
error_buffer = io.StringIO()

# Override sys.argv to simulate command line arguments
sys.argv = [
    'main.py',
    '--address', '1342 E. Kramer Circle',
    '--city', 'Mesa',
    '--zip', '85203'
]

try:
    with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
        main()
    
    output = output_buffer.getvalue()
    errors = error_buffer.getvalue()
    
    # Write to file
    with open('bot_output.txt', 'w', encoding='utf-8') as f:
        f.write("=== STDOUT ===\n")
        f.write(output)
        f.write("\n\n=== STDERR ===\n")
        f.write(errors)
    
    # Also print to console
    print("=== STDOUT ===")
    print(output)
    if errors:
        print("\n=== STDERR ===")
        print(errors, file=sys.stderr)
    
except Exception as e:
    error_msg = f"Error running bot: {e}\n"
    import traceback
    error_msg += traceback.format_exc()
    
    with open('bot_output.txt', 'w', encoding='utf-8') as f:
        f.write(error_msg)
    
    print(error_msg, file=sys.stderr)
    raise
