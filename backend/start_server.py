import os
import sys
import subprocess

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PYTHONPATH'] = backend_dir
cmd = [r'C:\Users\HP\AppData\Local\Programs\Python\Python313\python.exe', '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000']
print('Starting server with:', cmd)
subprocess.call(cmd, cwd=backend_dir)
