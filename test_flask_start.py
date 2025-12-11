"""Test Flask startup."""
import sys
from flask import Flask
print("Python version:", sys.version)
print("Starting imports...")

try:
    print("1. Importing Flask...")
    from flask import Flask
    print("   ✓ Flask imported")
except Exception as e:
    print(f"   ✗ Flask import failed: {e}")
    sys.exit(1)

try:
    print("2. Importing data_tree...")
    from data_tree import DataTree, tree  # pyright: ignore[reportMissingImports]
    print("   ✓ data_tree imported")
except Exception as e:
    print(f"   ✗ data_tree import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. Importing attom_connector...")
    from attom_connector import ATTOMConnector
    print("   ✓ attom_connector imported")
except Exception as e:
    print(f"   ✗ attom_connector import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("4. Importing app...")
    from app import app
    print("   ✓ app imported")
    print("5. Starting Flask server...")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
