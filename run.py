"""
Convenient launcher script for the Healthcare AI Assistant.
"""
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add backend directory to sys.path
    backend_path = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.insert(0, backend_path)
    
    print("=" * 70)
    print(" Personalized Healthcare AI Assistant Server Starting")
    print(" Medical Safety Guardrails: ACTIVE (Zero Diagnosis / Zero Rx)")
    print(" URL: http://127.0.0.1:8000")
    print(" Swagger Docs: http://127.0.0.1:8000/docs")
    print("=" * 70)
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
