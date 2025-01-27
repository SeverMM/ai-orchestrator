import subprocess
import time
import os

def start_service(service_name):
    print(f"Starting {service_name} service...")
    subprocess.Popen(
        ['cmd', '/c', f'python services/{service_name}/service.py'],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

# Service startup delays (in seconds)
service_delays = {
    'atlas': 0,
    'nova': 5,
    'sage': 10,
    'echo': 15,
    'pixel': 20,
    'quantum': 25
}

# Activate virtual environment
os.system('call venv\\Scripts\\activate')

# Start services in order
for service, delay in service_delays.items():
    if delay > 0:
        print(f"Waiting {delay} seconds before starting {service}...")
        time.sleep(delay)
    start_service(service)

print("\nAll services started. Press Ctrl+C to exit...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting...")
