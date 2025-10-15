"""
Project Structure Analyzer - Part Generator
Analyzes your actual project and creates multiple txt files showing structure and connections
"""

import os
from pathlib import Path
import json

def analyze_project(root_path):
    """Scan the entire project and build structure"""
    
    structure = {
        'directories': {},
        'files': [],
        'connections': {},
        'imports': {}
    }
    
    # Skip these directories
    skip_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'env',
        '.next', 'build', 'dist', '.pytest_cache', '.vscode',
        'eggs', '.eggs', 'htmlcov', '.tox', '.mypy_cache'
    }
    
    # Skip these files
    skip_files = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe'}
    
    print(f"🔍 Scanning: {root_path}")
    print("="*70)
    
    file_count = 0
    dir_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out skip directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        rel_path = os.path.relpath(dirpath, root_path)
        if rel_path == '.':
            rel_path = 'ROOT'
        
        dir_count += 1
        
        # Store directory info
        if rel_path not in structure['directories']:
            structure['directories'][rel_path] = {
                'files': [],
                'subdirs': dirnames.copy()
            }
        
        # Process files
        for filename in filenames:
            # Skip unwanted file types
            if any(filename.endswith(ext) for ext in skip_files):
                continue
            
            file_path = os.path.join(dirpath, filename)
            rel_file_path = os.path.relpath(file_path, root_path)
            
            file_info = {
                'name': filename,
                'path': rel_file_path,
                'size': os.path.getsize(file_path),
                'directory': rel_path,
                'extension': Path(filename).suffix
            }
            
            structure['files'].append(file_info)
            structure['directories'][rel_path]['files'].append(filename)
            file_count += 1
            
            # Analyze Python files for imports
            if filename.endswith('.py'):
                imports = extract_imports(file_path)
                if imports:
                    structure['imports'][rel_file_path] = imports
            
            # Analyze JS files for imports
            elif filename.endswith(('.js', '.jsx')):
                imports = extract_js_imports(file_path)
                if imports:
                    structure['imports'][rel_file_path] = imports
    
    print(f"✅ Found {dir_count} directories")
    print(f"✅ Found {file_count} files")
    print(f"✅ Analyzed {len(structure['imports'])} files for imports")
    
    return structure

def extract_imports(filepath):
    """Extract Python imports from a file"""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
    except:
        pass
    return imports

def extract_js_imports(filepath):
    """Extract JavaScript/React imports from a file"""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if 'import' in line and ('from' in line or 'require' in line):
                    imports.append(line)
    except:
        pass
    return imports

def generate_part1_overview(structure, output_dir):
    """Part 1: Project Overview"""
    
    content = []
    content.append("="*70)
    content.append("PROJECT STRUCTURE ANALYSIS - PART 1: OVERVIEW")
    content.append("="*70)
    content.append("")
    
    # Summary
    content.append("📊 PROJECT SUMMARY")
    content.append("-"*70)
    content.append(f"Total Directories: {len(structure['directories'])}")
    content.append(f"Total Files: {len(structure['files'])}")
    content.append(f"Files with Imports: {len(structure['imports'])}")
    content.append("")
    
    # File types breakdown
    content.append("📁 FILE TYPES")
    content.append("-"*70)
    
    extensions = {}
    for file_info in structure['files']:
        ext = file_info['extension'] or 'no extension'
        extensions[ext] = extensions.get(ext, 0) + 1
    
    for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
        content.append(f"{ext:20s} : {count:4d} files")
    
    content.append("")
    
    # Directory structure (tree view)
    content.append("🌳 DIRECTORY TREE")
    content.append("-"*70)
    
    dirs_sorted = sorted(structure['directories'].keys())
    for dir_path in dirs_sorted:
        depth = dir_path.count(os.sep) if dir_path != 'ROOT' else 0
        indent = "  " * depth
        dir_name = os.path.basename(dir_path) if dir_path != 'ROOT' else '.'
        file_count = len(structure['directories'][dir_path]['files'])
        content.append(f"{indent}├── {dir_name}/ ({file_count} files)")
    
    # Write to file
    output_path = output_dir / "part1_overview.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ Created: {output_path}")
    return output_path

def generate_part2_backend(structure, output_dir):
    """Part 2: Backend Files"""
    
    content = []
    content.append("="*70)
    content.append("PROJECT STRUCTURE ANALYSIS - PART 2: BACKEND FILES")
    content.append("="*70)
    content.append("")
    
    # Filter backend files
    backend_files = [f for f in structure['files'] if 'backend' in f['path'].lower()]
    
    content.append(f"📦 BACKEND FILES ({len(backend_files)} files)")
    content.append("-"*70)
    content.append("")
    
    # Group by directory
    backend_dirs = {}
    for file_info in backend_files:
        dir_path = file_info['directory']
        if dir_path not in backend_dirs:
            backend_dirs[dir_path] = []
        backend_dirs[dir_path].append(file_info)
    
    for dir_path in sorted(backend_dirs.keys()):
        content.append(f"\n📁 {dir_path}/")
        content.append("-"*70)
        
        for file_info in sorted(backend_dirs[dir_path], key=lambda x: x['name']):
            size_kb = file_info['size'] / 1024
            content.append(f"  {file_info['name']:40s} ({size_kb:7.2f} KB)")
            
            # Show imports if available
            if file_info['path'] in structure['imports']:
                imports = structure['imports'][file_info['path']]
                if imports:
                    content.append(f"    Imports:")
                    for imp in imports[:5]:  # Show first 5 imports
                        content.append(f"      • {imp}")
                    if len(imports) > 5:
                        content.append(f"      ... and {len(imports)-5} more")
                content.append("")
    
    # Write to file
    output_path = output_dir / "part2_backend.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ Created: {output_path}")
    return output_path

def generate_part3_frontend(structure, output_dir):
    """Part 3: Frontend Files"""
    
    content = []
    content.append("="*70)
    content.append("PROJECT STRUCTURE ANALYSIS - PART 3: FRONTEND FILES")
    content.append("="*70)
    content.append("")
    
    # Filter frontend files
    frontend_files = [f for f in structure['files'] if 'frontend' in f['path'].lower() or 'src' in f['path'].lower()]
    
    content.append(f"⚛️  FRONTEND FILES ({len(frontend_files)} files)")
    content.append("-"*70)
    content.append("")
    
    # Group by directory
    frontend_dirs = {}
    for file_info in frontend_files:
        dir_path = file_info['directory']
        if dir_path not in frontend_dirs:
            frontend_dirs[dir_path] = []
        frontend_dirs[dir_path].append(file_info)
    
    for dir_path in sorted(frontend_dirs.keys()):
        content.append(f"\n📁 {dir_path}/")
        content.append("-"*70)
        
        for file_info in sorted(frontend_dirs[dir_path], key=lambda x: x['name']):
            size_kb = file_info['size'] / 1024
            content.append(f"  {file_info['name']:40s} ({size_kb:7.2f} KB)")
            
            # Show imports if available
            if file_info['path'] in structure['imports']:
                imports = structure['imports'][file_info['path']]
                if imports:
                    content.append(f"    Imports:")
                    for imp in imports[:5]:
                        content.append(f"      • {imp}")
                    if len(imports) > 5:
                        content.append(f"      ... and {len(imports)-5} more")
                content.append("")
    
    # Write to file
    output_path = output_dir / "part3_frontend.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ Created: {output_path}")
    return output_path

def generate_part4_connections(structure, output_dir):
    """Part 4: File Connections"""
    
    content = []
    content.append("="*70)
    content.append("PROJECT STRUCTURE ANALYSIS - PART 4: FILE CONNECTIONS")
    content.append("="*70)
    content.append("")
    
    content.append("🔗 IMPORT RELATIONSHIPS")
    content.append("-"*70)
    content.append("")
    content.append("This shows which files import from which files/modules")
    content.append("")
    
    for filepath, imports in sorted(structure['imports'].items()):
        if imports:
            content.append(f"📄 {filepath}")
            content.append("   Imports:")
            
            for imp in imports:
                # Clean up the import statement
                if 'from' in imp:
                    content.append(f"   ↓ {imp}")
                else:
                    content.append(f"   ↓ {imp}")
            
            content.append("")
    
    # Write to file
    output_path = output_dir / "part4_connections.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ Created: {output_path}")
    return output_path

def generate_part5_config(structure, output_dir):
    """Part 5: Configuration Files"""
    
    content = []
    content.append("="*70)
    content.append("PROJECT STRUCTURE ANALYSIS - PART 5: CONFIGURATION")
    content.append("="*70)
    content.append("")
    
    # Config file extensions
    config_exts = {'.json', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.env', '.toml'}
    config_names = {'config', 'package', 'requirements', 'setup', 'dockerfile', 'makefile'}
    
    config_files = []
    for file_info in structure['files']:
        ext = file_info['extension'].lower()
        name = file_info['name'].lower()
        
        if ext in config_exts or any(cn in name for cn in config_names):
            config_files.append(file_info)
    
    content.append(f"⚙️  CONFIGURATION FILES ({len(config_files)} files)")
    content.append("-"*70)
    content.append("")
    
    for file_info in sorted(config_files, key=lambda x: x['path']):
        size_kb = file_info['size'] / 1024
        content.append(f"📄 {file_info['path']}")
        content.append(f"   Size: {size_kb:.2f} KB")
        content.append(f"   Directory: {file_info['directory']}")
        content.append("")
    
    # Write to file
    output_path = output_dir / "part5_config.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ Created: {output_path}")
    return output_path

def generate_part6_summary(structure, output_dir, created_files):
    """Part 6: Summary and Guide"""
    
    content = []
    content.append("="*70)
    content.append("PROJECT STRUCTURE ANALYSIS - PART 6: SUMMARY & GUIDE")
    content.append("="*70)
    content.append("")
    
    content.append("📚 FILES CREATED")
    content.append("-"*70)
    for i, filepath in enumerate(created_files, 1):
        content.append(f"{i}. {filepath}")
    content.append("")
    
    content.append("🎯 KEY FINDINGS")
    content.append("-"*70)
    
    # Backend stats
    backend_files = [f for f in structure['files'] if 'backend' in f['path'].lower()]
    content.append(f"Backend Files: {len(backend_files)}")
    
    # Frontend stats
    frontend_files = [f for f in structure['files'] if 'frontend' in f['path'].lower()]
    content.append(f"Frontend Files: {len(frontend_files)}")
    
    # Python files
    py_files = [f for f in structure['files'] if f['extension'] == '.py']
    content.append(f"Python Files: {len(py_files)}")
    
    # JS files
    js_files = [f for f in structure['files'] if f['extension'] in ['.js', '.jsx']]
    content.append(f"JavaScript Files: {len(js_files)}")
    
    content.append("")
    
    content.append("📖 HOW TO USE THIS ANALYSIS")
    content.append("-"*70)
    content.append("1. part1_overview.txt    - See the big picture")
    content.append("2. part2_backend.txt     - Explore backend structure")
    content.append("3. part3_frontend.txt    - Explore frontend structure")
    content.append("4. part4_connections.txt - See how files connect")
    content.append("5. part5_config.txt      - Review configuration")
    content.append("6. part6_summary.txt     - This file")
    content.append("")
    
    content.append("💡 UNDERSTANDING CONNECTIONS")
    content.append("-"*70)
    content.append("Look at part4_connections.txt to see:")
    content.append("- Which files import from which modules")
    content.append("- How backend and frontend communicate")
    content.append("- Which files are central (imported by many)")
    content.append("- Which files are isolated (import nothing)")
    content.append("")
    
    content.append("🔍 NEXT STEPS")
    content.append("-"*70)
    content.append("1. Read part1_overview.txt to understand the project")
    content.append("2. Check part2_backend.txt to see backend organization")
    content.append("3. Review part4_connections.txt to trace data flow")
    content.append("4. Use this info to understand how everything connects")
    
    # Write to file
    output_path = output_dir / "part6_summary.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ Created: {output_path}")
    return output_path

def main():
    """Main function"""
    
    # Get project root from user or use current directory
    import sys
    
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        project_root = Path.cwd()
    
    if not project_root.exists():
        print(f"❌ Error: Directory not found: {project_root}")
        return
    
    print("="*70)
    print("PROJECT STRUCTURE ANALYZER")
    print("="*70)
    print(f"📁 Analyzing: {project_root}")
    print("")
    
    # Analyze project
    structure = analyze_project(project_root)
    
    print("")
    print("="*70)
    print("GENERATING OUTPUT FILES")
    print("="*70)
    print("")
    
    # Output directory (same as project root)
    output_dir = project_root
    
    # Generate all parts
    created_files = []
    
    created_files.append(generate_part1_overview(structure, output_dir))
    created_files.append(generate_part2_backend(structure, output_dir))
    created_files.append(generate_part3_frontend(structure, output_dir))
    created_files.append(generate_part4_connections(structure, output_dir))
    created_files.append(generate_part5_config(structure, output_dir))
    created_files.append(generate_part6_summary(structure, output_dir, created_files))
    
    print("")
    print("="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print("")
    print("📚 Generated 6 text files:")
    for filepath in created_files:
        print(f"  ✅ {filepath.name}")
    print("")
    print(f"📁 Location: {output_dir}")
    print("")
    print("📖 Start with: part1_overview.txt")
    print("="*70)

if __name__ == "__main__":
    main()
