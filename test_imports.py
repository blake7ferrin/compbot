"""Test all imports to find the issue."""
import sys
from flask import Flask
print("Python version:", sys.version)
print("Python path:", sys.executable)
print("=" * 60)

try:
    print("Testing Flask...")
    from flask import Flask
    print("✓ Flask imported")
except Exception as e:
    print(f"✗ Flask import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Testing DataTree...")
    from data_tree import DataTree, tree  # pyright: ignore[reportMissingImports]
    print("✓ DataTree imported")
except Exception as e:
    print(f"✗ DataTree import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Testing ATTOMConnector...")
    from attom_connector import ATTOMConnector
    print("✓ ATTOMConnector imported")
except Exception as e:
    print(f"✗ ATTOMConnector import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Testing MLSCompBot...")
    from bot import MLSCompBot
    print("✓ MLSCompBot imported")
except Exception as e:
    print(f"✗ MLSCompBot import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Testing Flask app...")
    from app import app
    print("✓ Flask app imported")
    print(f"App name: {app.name}")
except Exception as e:
    print(f"✗ Flask app import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("ALL IMPORTS SUCCESSFUL!")
print("=" * 60)
print("\nNow testing Flask startup...")

try:
    import threading
    import time
    import socket
    
    def run_flask():
        print("Starting Flask server...")
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    
    print("Waiting for Flask to start...")
    time.sleep(5)
    
    # Test connection
    s = socket.socket()
    result = s.connect_ex(('127.0.0.1', 5000))
    s.close()
    
    if result == 0:
        print("✓ Flask is running and accepting connections on port 5000!")
        print("Open http://127.0.0.1:5000 in your browser")
    else:
        print("✗ Flask is NOT accepting connections")
        print("Check the Flask output above for errors")
        
except Exception as e:
    print(f"✗ Error starting Flask: {e}")
    import traceback
    traceback.print_exc()
