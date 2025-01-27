# scripts/check_setup.py
import os
from pathlib import Path

def check_project_structure():
    root_dir = Path(__file__).parent.parent
    
    required_structure = {
        "migrations": {
            "versions": ["001_initial.py"],
            "files": ["env.py"]
        },
        "config": {"files": ["settings.py"]},
        "database": {"files": ["models.py", "connection.py"]},
        "scripts": {"files": ["setup_fresh.py", "reset_db.py", "run_migrations.py"]},
        "root_files": ["alembic.ini"]
    }
    
    print("Checking project structure...")
    
    for dir_name, contents in required_structure.items():
        if dir_name == "root_files":
            # Check root-level files
            for file_name in contents:
                file_path = root_dir / file_name
                print(f"\nChecking root file: {file_name}")
                print(f"Exists: {file_path.exists()}")
                if file_path.exists():
                    print(f"Size: {file_path.stat().st_size} bytes")
        else:
            # Check directories and their contents
            dir_path = root_dir / dir_name
            print(f"\nChecking directory: {dir_name}")
            print(f"Exists: {dir_path.exists()}")
            
            if dir_path.exists():
                # Check subdirectories
                for subdir_name, files in contents.items():
                    if subdir_name == "files":
                        # Check files in current directory
                        for file_name in files:
                            file_path = dir_path / file_name
                            print(f"  File {file_name}: {'exists' if file_path.exists() else 'MISSING'}")
                    else:
                        # Check subdirectory
                        subdir_path = dir_path / subdir_name
                        print(f"\n  Checking subdirectory: {subdir_name}")
                        print(f"  Exists: {subdir_path.exists()}")
                        if subdir_path.exists():
                            for file_name in files:
                                file_path = subdir_path / file_name
                                print(f"    File {file_name}: {'exists' if file_path.exists() else 'MISSING'}")

if __name__ == "__main__":
    check_project_structure()