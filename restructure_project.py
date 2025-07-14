#!/usr/bin/env python3
"""
Project Restructuring Script
Reorganizes the web_api_backend project into a cleaner structure
"""

import os
import shutil
import sys
from pathlib import Path

def create_directory_structure():
    """Create the new directory structure"""
    directories = [
        'app',
        'app/models',
        'app/routers', 
        'app/services',
        'database',
        'database/migrations',
        'database/seeds',
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/manual',
        'tests/debug',
        'scripts',
        'scripts/database_analysis',
        'scripts/category_management',
        'scripts/setup',
        'docs',
        'docs/api',
        'docs/flutter',
        'docs/flow',
        'docs/backup',
        'static/assets',
        'logs'
    ]
    
    print("📁 Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files for Python packages
        if not directory.startswith(('docs', 'static', 'logs')):
            init_file = Path(directory) / '__init__.py'
            if not init_file.exists():
                init_file.touch()
    
    # Create .gitkeep for empty directories
    (Path('logs') / '.gitkeep').touch()
    
    print("✅ Directory structure created!")

def move_core_files():
    """Move core application files to app/ directory"""
    print("\n🔧 Moving core application files...")
    
    core_files = {
        'main.py': 'app/main.py',
        'config.py': 'app/config.py',
        'database.py': 'app/database.py',
        'auth.py': 'app/auth.py'
    }
    
    for source, dest in core_files.items():
        if os.path.exists(source):
            shutil.move(source, dest)
            print(f"  ✓ Moved {source} → {dest}")
    
    # Move existing models and routers directories
    if os.path.exists('models'):
        if os.path.exists('app/models'):
            shutil.rmtree('app/models')
        shutil.move('models', 'app/models')
        print("  ✓ Moved models/ → app/models/")
    
    if os.path.exists('routers'):
        if os.path.exists('app/routers'):
            shutil.rmtree('app/routers')
        shutil.move('routers', 'app/routers')
        print("  ✓ Moved routers/ → app/routers/")
        
    if os.path.exists('services'):
        if os.path.exists('app/services'):
            shutil.rmtree('app/services')
        shutil.move('services', 'app/services')
        print("  ✓ Moved services/ → app/services/")

def move_database_files():
    """Move database-related files"""
    print("\n🗄️ Moving database files...")
    
    migration_files = [
        'add_lock_to_products.py',
        'update_db_schema.py'
    ]
    
    seed_files = [
        'add_accessories.py'
    ]
    
    # Move migration files
    for file in migration_files:
        if os.path.exists(file):
            shutil.move(file, f'database/migrations/{file}')
            print(f"  ✓ Moved {file} → database/migrations/")
    
    # Move seed files
    for file in seed_files:
        if os.path.exists(file):
            shutil.move(file, f'database/seeds/{file}')
            print(f"  ✓ Moved {file} → database/seeds/")
    
    # Move test files that are actually seed files
    test_seed_files = [
        'tests/add_sample_products.py',
        'tests/create_sample_accounts.py'
    ]
    
    for file in test_seed_files:
        if os.path.exists(file):
            filename = os.path.basename(file)
            shutil.move(file, f'database/seeds/{filename}')
            print(f"  ✓ Moved {file} → database/seeds/")

def move_test_files():
    """Reorganize test files"""
    print("\n🧪 Reorganizing test files...")
    
    # Integration tests
    integration_tests = [
        'test_admin_curd_flow.py',
        'test_admin_flow.py',
        'test_complete_improvements.py',
        'test_full_flow.py',
        'tests/test_cart_and_stock.py',
        'tests/test_chatbot_complete_final.py',
        'tests/simple_cart_test.py'
    ]
    
    # Manual tests
    manual_tests = [
        'tests/test_login.py',
        'tests/quick_test.py',
        'test_new_categories.py'
    ]
    
    # Debug tests
    debug_files = [
        'debug/',  # Move entire debug directory
        'tests/check_db_schema.py'
    ]
    
    # Move integration tests
    for file in integration_tests:
        if os.path.exists(file):
            filename = os.path.basename(file)
            shutil.move(file, f'tests/integration/{filename}')
            print(f"  ✓ Moved {file} → tests/integration/")
    
    # Move manual tests
    for file in manual_tests:
        if os.path.exists(file):
            filename = os.path.basename(file)
            shutil.move(file, f'tests/manual/{filename}')
            print(f"  ✓ Moved {file} → tests/manual/")
    
    # Move debug directory
    if os.path.exists('debug'):
        # Move contents of debug directory
        for item in os.listdir('debug'):
            src = os.path.join('debug', item)
            if os.path.isfile(src):
                shutil.move(src, f'tests/debug/{item}')
                print(f"  ✓ Moved debug/{item} → tests/debug/")
        
        # Remove empty debug directory
        try:
            os.rmdir('debug')
        except:
            pass
    
    # Move remaining test files from tests directory
    if os.path.exists('tests'):
        for item in os.listdir('tests'):
            src = os.path.join('tests', item)
            if os.path.isfile(src) and item.endswith('.py'):
                if 'check_db' in item or 'debug' in item:
                    shutil.move(src, f'tests/debug/{item}')
                else:
                    shutil.move(src, f'tests/manual/{item}')
                print(f"  ✓ Moved tests/{item} → tests/manual/ or tests/debug/")

def move_scripts():
    """Move utility scripts"""
    print("\n📜 Moving utility scripts...")
    
    # Database analysis scripts
    db_analysis = [
        'analyze_database.py',
        'analyze_and_fix_products.py', 
        'final_database_report.py',
        'check_products_database.py'
    ]
    
    # Category management scripts
    category_scripts = [
        'fix_categories.py',
        'fix_categories_safe.py',
        'fix_categories_simple.py',
        'fix_categories_direct.py',
        'complete_category_fix.py',
        'fix_remaining_issues.py'
    ]
    
    # Setup scripts
    setup_scripts = [
        'create_accounts.ps1',
        'create_accounts.bat',
        'crud_operations.py'
    ]
    
    # Move database analysis scripts
    for file in db_analysis:
        if os.path.exists(file):
            shutil.move(file, f'scripts/database_analysis/{file}')
            print(f"  ✓ Moved {file} → scripts/database_analysis/")
    
    # Move category management scripts
    for file in category_scripts:
        if os.path.exists(file):
            shutil.move(file, f'scripts/category_management/{file}')
            print(f"  ✓ Moved {file} → scripts/category_management/")
    
    # Move setup scripts
    for file in setup_scripts:
        if os.path.exists(file):
            shutil.move(file, f'scripts/setup/{file}')
            print(f"  ✓ Moved {file} → scripts/setup/")

def move_documentation():
    """Move documentation files"""
    print("\n📚 Moving documentation...")
    
    # API documentation
    api_docs = [
        'API_ENDPOINTS.md',
        'CART_ENDPOINTS.md'
    ]
    
    # Flutter documentation
    flutter_docs = [
        'FLUTTER_GUIDE.md',
        'FLUTTER_LOCAL_SETUP.md',
        'FLUTTER_UPDATE_GUIDE.md'
    ]
    
    # Flow documentation
    flow_docs = [
        'COMPLETE_FLOW_GUIDE.md',
        'FLOW_GUIDE.md',
        'ARCHITECTURE.md'
    ]
    
    # Backup files
    backup_files = [
        'category_backup.txt',
        'category_backup_safe.txt'
    ]
    
    # Move API docs
    for file in api_docs:
        if os.path.exists(file):
            shutil.move(file, f'docs/api/{file}')
            print(f"  ✓ Moved {file} → docs/api/")
    
    # Move Flutter docs
    for file in flutter_docs:
        if os.path.exists(file):
            shutil.move(file, f'docs/flutter/{file}')
            print(f"  ✓ Moved {file} → docs/flutter/")
    
    # Move flow docs
    for file in flow_docs:
        if os.path.exists(file):
            shutil.move(file, f'docs/flow/{file}')
            print(f"  ✓ Moved {file} → docs/flow/")
    
    # Move backup files
    for file in backup_files:
        if os.path.exists(file):
            shutil.move(file, f'docs/backup/{file}')
            print(f"  ✓ Moved {file} → docs/backup/")
    
    # Move README from readme/ directory to docs/api/
    if os.path.exists('readme/README.md'):
        shutil.move('readme/README.md', 'docs/api/admin_curd_guide.md')
        print("  ✓ Moved readme/README.md → docs/api/admin_curd_guide.md")
    
    # Remove empty readme directory
    try:
        if os.path.exists('readme'):
            os.rmdir('readme')
    except:
        pass

def move_static_files():
    """Move static files"""
    print("\n🖼️ Moving static files...")
    
    # Move placeholder to assets
    if os.path.exists('placeholder.png'):
        shutil.move('placeholder.png', 'static/assets/placeholder.png')
        print("  ✓ Moved placeholder.png → static/assets/")

def update_main_py():
    """Update main.py imports for new structure"""
    print("\n🔧 Updating main.py imports...")
    
    main_file = 'app/main.py'
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Update import statements
        content = content.replace('from routers import', 'from app.routers import')
        content = content.replace('from config import', 'from app.config import')
        
        with open(main_file, 'w') as f:
            f.write(content)
        
        print("  ✓ Updated import statements in main.py")

def create_new_main():
    """Create a new main.py in root that imports from app"""
    print("\n🚀 Creating new root main.py...")
    
    main_content = '''#!/usr/bin/env python3
"""
Web Selling Chatbot API
Main entry point for the application
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import API_HOST, API_PORT
    uvicorn.run(app, host=API_HOST, port=API_PORT)
'''
    
    with open('main.py', 'w') as f:
        f.write(main_content)
    
    print("  ✓ Created new main.py in root directory")

def cleanup_old_files():
    """Clean up old files and empty directories"""
    print("\n🧹 Cleaning up...")
    
    # Remove old test directories if empty
    old_dirs = ['tests', 'readme']
    for dir_name in old_dirs:
        try:
            if os.path.exists(dir_name) and not os.listdir(dir_name):
                os.rmdir(dir_name)
                print(f"  ✓ Removed empty directory: {dir_name}")
        except:
            pass
    
    # Remove add_products_proper.py (seems to be a utility script)
    if os.path.exists('add_products_proper.py'):
        shutil.move('add_products_proper.py', 'scripts/database_analysis/add_products_proper.py')
        print("  ✓ Moved add_products_proper.py → scripts/database_analysis/")

def main():
    """Main restructuring function"""
    print("🏗️ Starting Project Restructuring...")
    print("=" * 50)
    
    try:
        create_directory_structure()
        move_core_files()
        move_database_files()
        move_test_files()
        move_scripts()
        move_documentation()
        move_static_files()
        update_main_py()
        create_new_main()
        cleanup_old_files()
        
        print("\n" + "=" * 50)
        print("🎉 Project restructuring completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test the application: python main.py")
        print("2. Run tests: python -m pytest tests/")
        print("3. Check imports and fix any issues")
        print("4. Update any remaining hardcoded paths")
        print("\n📁 New structure created - see PROJECT_STRUCTURE.md for details")
        
    except Exception as e:
        print(f"\n❌ Error during restructuring: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 