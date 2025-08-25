#!/usr/bin/env python
"""
MCOA Web UI Launcher
Run this script to start the web dashboard
"""

import webbrowser
import time
import sys
import os

# Add MCOA to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*60)
print("🎖️  MCOA COMMAND CENTER - WEB UI LAUNCHER")
print("="*60)
print("\nStarting MCOA Web Dashboard...")
print("This will open in your browser at http://localhost:5001")
print("\nPress Ctrl+C to stop the server")
print("="*60 + "\n")

# Start the Flask app
try:
    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:5001')
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Import and run the app
    from app import app, socketio, mcoa_service
    socketio.run(app, debug=False, host='0.0.0.0', port=5001)
    
except KeyboardInterrupt:
    print("\n\nShutting down MCOA Command Center...")
    print("Semper Fi! 🇺🇸")
    sys.exit(0)
except Exception as e:
    print(f"\nError starting server: {e}")
    print("\nMake sure you have installed the requirements:")
    print("  pip install -r requirements.txt")
    sys.exit(1)