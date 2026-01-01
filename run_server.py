"""
Stable server runner - keeps server alive
"""
import sys
import time

# Import the app
from app import app

if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("🚀 SERVER READY!")
        print("="*60)
        print("✓ Open browser: http://localhost:5000")
        print("✓ Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Start server in a way that keeps it alive
        from waitress import serve
        serve(app, host='localhost', port=5000, threads=4, channel_timeout=300)
        
    except ImportError:
        # Fallback to Flask if waitress not available
        print("Using Flask development server...")
        app.run(host='localhost', port=5000, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
