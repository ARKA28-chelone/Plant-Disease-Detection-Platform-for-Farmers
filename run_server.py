import sys
import os

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("================================================================")
    print(f"Starting Plant Disease Detection Backend on port {port}...")
    print(f"Access Frontend Web UI at: http://127.0.0.1:{port}/")
    print(f"Interactive Swagger API Docs: http://127.0.0.1:{port}/docs")
    print("================================================================")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False)
