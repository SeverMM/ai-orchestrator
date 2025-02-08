import os
import json
from pathlib import Path

def export_codebase(directory="./", output_dir="./codebase_export"):
    """
    Exports folder structure and file contents in Spaces-compatible format
    Returns: Path to output directory
    """
    print("Starting export...")  # Debug print
    output = []
    excluded_dirs = {'__pycache__', 'venv', '.git'}  # Common exclusions
    
    for root, dirs, files in os.walk(directory):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        rel_path = os.path.relpath(root, directory)
        folder_data = {
            "path": rel_path,
            "files": []
        }

        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                folder_data["files"].append({
                    "name": file,
                    "content": content,
                    "size": os.path.getsize(file_path)
                })
            except UnicodeDecodeError:
                folder_data["files"].append({
                    "name": file,
                    "error": "Binary file not decoded"
                })
            except Exception as e:
                folder_data["files"].append({
                    "name": file,
                    "error": str(e)
                })

        output.append(folder_data)

    # Save structured output
    Path(output_dir).mkdir(exist_ok=True)
    
    # Single JSON file format
    output_file = Path(output_dir) / "codebase_export.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print("Export completed!")  # Debug print
    return output_dir

# Add this part to actually run the function
if __name__ == "__main__":
    print("Script starting...")
    result = export_codebase()
    print(f"Files exported to: {result}")
    input("Press Enter to exit...")

