import os

def check_required_files():
    print("Checking required files...")
    
    required_files = [
        'config.ini',
        'config_manager.py',
        'icons',
        'assets',
        'thesis_copy/Main.py'
    ]
    
    all_exists = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_exists = False
    
    if all_exists:
        print("\n✅ All required files are present!")
    else:
        print("\n❌ Some files are missing!")
    
    return all_exists

if __name__ == "__main__":
    check_required_files()