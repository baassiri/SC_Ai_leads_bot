#!/usr/bin/env python3
"""
Project Architecture Analyzer
Generates comprehensive Mermaid diagrams from project files
Works on Windows, Linux, and Mac - analyzes current directory
"""

import os
import re
import ast
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.modules = {}
        self.routes = []
        self.functions = {}
        self.imports = {}
        self.database_schema = {}
        self.js_components = {}
        
    def analyze_python_file(self, filepath: Path):
        """Analyze a Python file for imports, functions, classes, and routes"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                
            module_name = filepath.stem
            self.modules[module_name] = {
                'imports': [],
                'functions': [],
                'classes': [],
                'routes': []
            }
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.modules[module_name]['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.modules[module_name]['imports'].append(node.module)
                        
                # Extract functions
                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list]
                    }
                    self.modules[module_name]['functions'].append(func_info)
                    
                    # Check for Flask routes
                    for dec in node.decorator_list:
                        if self._is_route_decorator(dec):
                            route_path = self._extract_route_path(dec)
                            if route_path:
                                self.routes.append({
                                    'module': module_name,
                                    'function': node.name,
                                    'path': route_path,
                                    'methods': self._extract_route_methods(dec)
                                })
                
                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    }
                    self.modules[module_name]['classes'].append(class_info)
                    
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
    
    def _get_decorator_name(self, decorator):
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
            elif isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return ""
    
    def _is_route_decorator(self, decorator):
        """Check if decorator is a route decorator"""
        name = self._get_decorator_name(decorator)
        return name in ['route', 'get', 'post', 'put', 'delete', 'patch']
    
    def _extract_route_path(self, decorator):
        """Extract route path from decorator"""
        if isinstance(decorator, ast.Call) and decorator.args:
            if isinstance(decorator.args[0], ast.Constant):
                return decorator.args[0].value
        return None
    
    def _extract_route_methods(self, decorator):
        """Extract HTTP methods from route decorator"""
        methods = []
        if isinstance(decorator, ast.Call):
            for keyword in decorator.keywords:
                if keyword.arg == 'methods':
                    if isinstance(keyword.value, ast.List):
                        methods = [el.value for el in keyword.value.elts if isinstance(el, ast.Constant)]
        return methods if methods else ['GET']
    
    def analyze_javascript_file(self, filepath: Path):
        """Analyze JavaScript file for components and functions"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            module_name = filepath.stem
            self.js_components[module_name] = {
                'functions': [],
                'event_handlers': [],
                'api_calls': []
            }
            
            # Extract function declarations
            func_pattern = r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s*)?\([^)]*\)\s*=>|=\s*function|\([^)]*\)\s*{)'
            functions = re.findall(func_pattern, content)
            self.js_components[module_name]['functions'] = functions
            
            # Extract event listeners
            event_pattern = r'addEventListener\([\'"](\w+)[\'"]'
            events = re.findall(event_pattern, content)
            self.js_components[module_name]['event_handlers'] = events
            
            # Extract API calls
            api_pattern = r'fetch\([\'"]([^\'"]+)[\'"]'
            apis = re.findall(api_pattern, content)
            self.js_components[module_name]['api_calls'] = apis
            
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
    
    def analyze_database(self, db_path: Path):
        """Analyze SQLite database schema"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                self.database_schema[table_name] = []
                
                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                for col in columns:
                    self.database_schema[table_name].append({
                        'name': col[1],
                        'type': col[2],
                        'notnull': col[3],
                        'primary_key': col[5]
                    })
            
            conn.close()
        except Exception as e:
            print(f"Error analyzing database: {e}")
    
    def analyze_project(self):
        """Analyze all files in the project"""
        for filepath in self.project_path.iterdir():
            if filepath.suffix == '.py' and not filepath.name.startswith('__') and filepath.name != 'project_analyzer.py':
                print(f"Analyzing {filepath.name}...")
                self.analyze_python_file(filepath)
            elif filepath.suffix == '.js':
                print(f"Analyzing {filepath.name}...")
                self.analyze_javascript_file(filepath)
            elif filepath.suffix == '.db':
                print(f"Analyzing {filepath.name}...")
                self.analyze_database(filepath)
    
    def generate_mermaid_diagram(self) -> str:
        """Generate comprehensive Mermaid diagram"""
        mermaid = ["graph TB"]
        mermaid.append("")
        mermaid.append("    %% Styling")
        mermaid.append("    classDef pythonModule fill:#3776ab,stroke:#333,stroke-width:2px,color:#fff")
        mermaid.append("    classDef jsModule fill:#f7df1e,stroke:#333,stroke-width:2px,color:#000")
        mermaid.append("    classDef database fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff")
        mermaid.append("    classDef route fill:#4ecdc4,stroke:#333,stroke-width:2px,color:#000")
        mermaid.append("")
        
        # Add Python modules
        if self.modules:
            mermaid.append("    %% Python Modules")
            for module_name, data in self.modules.items():
                functions_str = "<br/>".join([f"+ {f['name']}()" for f in data['functions'][:5]])
                if len(data['functions']) > 5:
                    functions_str += f"<br/>+ ... {len(data['functions'])-5} more"
                
                classes_str = ""
                if data['classes']:
                    classes_str = "<br/>Classes: " + ", ".join([c['name'] for c in data['classes'][:3]])
                
                mermaid.append(f'    {module_name}["{module_name}.py{functions_str}{classes_str}"]')
                mermaid.append(f"    class {module_name} pythonModule")
            
            mermaid.append("")
        
        # Add JavaScript modules
        if self.js_components:
            mermaid.append("    %% JavaScript Modules")
            for module_name, data in self.js_components.items():
                functions_str = "<br/>".join([f"⚡ {f}" for f in data['functions'][:4]])
                if len(data['functions']) > 4:
                    functions_str += f"<br/>⚡ ... {len(data['functions'])-4} more"
                
                mermaid.append(f'    {module_name}["{module_name}.js{functions_str}"]')
                mermaid.append(f"    class {module_name} jsModule")
        
            mermaid.append("")
        
        # Add Database
        if self.database_schema:
            mermaid.append("    %% Database")
            db_tables = "<br/>".join([f"📊 {table}" for table in list(self.database_schema.keys())[:6]])
            if len(self.database_schema) > 6:
                db_tables += f"<br/>📊 ... {len(self.database_schema)-6} more"
            mermaid.append(f'    DB[("Database<br/>{db_tables}")]')
            mermaid.append("    class DB database")
            mermaid.append("")
        
        # Add Routes as nodes
        if self.routes:
            mermaid.append("    %% API Routes")
            for i, route in enumerate(self.routes[:10]):
                route_id = f"route{i}"
                methods = ",".join(route['methods'])
                mermaid.append(f'    {route_id}{{"{methods} {route["path"]}<br/>{route["function"]}()"}}')
                mermaid.append(f"    class {route_id} route")
            
            mermaid.append("")
        
        # Add import relationships
        if self.modules:
            mermaid.append("    %% Module Dependencies")
            for module_name, data in self.modules.items():
                for imp in data['imports']:
                    # Only show internal imports
                    imp_module = imp.split('.')[0]
                    if imp_module in self.modules:
                        mermaid.append(f"    {module_name} --> {imp_module}")
            
            mermaid.append("")
        
        # Connect routes to modules
        if self.routes:
            mermaid.append("    %% Route Connections")
            for i, route in enumerate(self.routes[:10]):
                route_id = f"route{i}"
                mermaid.append(f"    {route['module']} -.->|handles| {route_id}")
            
            mermaid.append("")
        
        # Connect modules to database
        if self.database_schema and self.modules:
            mermaid.append("    %% Database Connections")
            db_modules = ['bot_controller', 'analytics_routes', 'lead_selector', 'credentials_manager', 'app', 'main']
            for module in db_modules:
                if module in self.modules:
                    mermaid.append(f"    {module} <-->|queries| DB")
            
            mermaid.append("")
        
        # Connect JS to Python (API calls)
        if self.js_components and self.routes:
            mermaid.append("    %% Frontend to Backend")
            for js_module, data in self.js_components.items():
                if data['api_calls']:
                    # Try to match API calls to routes
                    for api_call in data['api_calls'][:5]:
                        for i, route in enumerate(self.routes[:10]):
                            if route['path'] in api_call or api_call in route['path']:
                                route_id = f"route{i}"
                                mermaid.append(f"    {js_module} -->|fetch| {route_id}")
                                break
        
        return "\n".join(mermaid)
    
    def generate_database_diagram(self) -> str:
        """Generate detailed database schema diagram"""
        if not self.database_schema:
            return ""
        
        mermaid = ["erDiagram"]
        mermaid.append("")
        
        for table_name, columns in self.database_schema.items():
            mermaid.append(f'    {table_name} {{')
            for col in columns:
                pk = " PK" if col['primary_key'] else ""
                notnull = " NOT NULL" if col['notnull'] else ""
                mermaid.append(f'        {col["type"]} {col["name"]}{pk}{notnull}')
            mermaid.append(f'    }}')
            mermaid.append("")
        
        return "\n".join(mermaid)
    
    def generate_sequence_diagram(self) -> str:
        """Generate sequence diagram for typical user flow"""
        mermaid = ["sequenceDiagram"]
        mermaid.append("    participant User")
        mermaid.append("    participant Frontend")
        
        # Add components based on what exists
        if 'auth' in self.modules:
            mermaid.append("    participant Auth")
        if 'bot_controller' in self.modules:
            mermaid.append("    participant BotController")
        if 'linkedin_messenger' in self.modules:
            mermaid.append("    participant LinkedInMessenger")
        if self.database_schema:
            mermaid.append("    participant Database")
        
        mermaid.append("")
        mermaid.append("    User->>Frontend: Open Application")
        
        if 'auth' in self.modules:
            mermaid.append("    Frontend->>Auth: Authenticate")
            if self.database_schema:
                mermaid.append("    Auth->>Database: Verify Credentials")
                mermaid.append("    Database-->>Auth: User Data")
            mermaid.append("    Auth-->>Frontend: Session Token")
        
        if 'bot_controller' in self.modules:
            mermaid.append("    Frontend->>BotController: Start Campaign")
            if self.database_schema:
                mermaid.append("    BotController->>Database: Get Lead List")
                mermaid.append("    Database-->>BotController: Leads")
            
            if 'linkedin_messenger' in self.modules:
                mermaid.append("    BotController->>LinkedInMessenger: Send Messages")
                if self.database_schema:
                    mermaid.append("    LinkedInMessenger->>Database: Log Activity")
            
            mermaid.append("    BotController-->>Frontend: Status Update")
        
        mermaid.append("    Frontend-->>User: Display Progress")
        
        return "\n".join(mermaid)
    
    def save_diagrams(self, output_dir: str = None):
        """Save all generated diagrams"""
        if output_dir is None:
            output_dir = os.path.join(self.project_path, "architecture_diagrams")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Architecture diagram
        arch_diagram = self.generate_mermaid_diagram()
        with open(os.path.join(output_dir, "architecture.mmd"), 'w', encoding='utf-8') as f:
            f.write(arch_diagram)
        print(f"✓ Saved: architecture.mmd")
        
        # Database diagram
        if self.database_schema:
            db_diagram = self.generate_database_diagram()
            with open(os.path.join(output_dir, "database_schema.mmd"), 'w', encoding='utf-8') as f:
                f.write(db_diagram)
            print(f"✓ Saved: database_schema.mmd")
        
        # Sequence diagram
        seq_diagram = self.generate_sequence_diagram()
        with open(os.path.join(output_dir, "sequence_flow.mmd"), 'w', encoding='utf-8') as f:
            f.write(seq_diagram)
        print(f"✓ Saved: sequence_flow.mmd")
        
        # Combined report
        report = [
            "# Project Analysis Report",
            "",
            f"**Project Path:** `{self.project_path}`",
            "",
            "## Architecture Overview",
            "```mermaid",
            arch_diagram,
            "```",
            "",
        ]
        
        if self.database_schema:
            report.extend([
                "## Database Schema",
                "```mermaid",
                self.generate_database_diagram(),
                "```",
                ""
            ])
        
        report.extend([
            "## Sequence Flow",
            "```mermaid",
            seq_diagram,
            "```",
            "",
            "## Module Details",
            ""
        ])
        
        for module_name, data in self.modules.items():
            report.append(f"### {module_name}.py")
            report.append(f"- **Functions:** {len(data['functions'])}")
            if data['functions']:
                report.append(f"  - {', '.join([f['name'] for f in data['functions'][:5]])}")
                if len(data['functions']) > 5:
                    report.append(f"  - ... and {len(data['functions'])-5} more")
            report.append(f"- **Classes:** {len(data['classes'])}")
            if data['classes']:
                report.append(f"  - {', '.join([c['name'] for c in data['classes']])}")
            report.append(f"- **Imports:** {len(data['imports'])}")
            report.append("")
        
        if self.js_components:
            report.append("## JavaScript Components")
            report.append("")
            for module_name, data in self.js_components.items():
                report.append(f"### {module_name}.js")
                report.append(f"- **Functions:** {len(data['functions'])}")
                if data['functions']:
                    report.append(f"  - {', '.join(data['functions'][:5])}")
                    if len(data['functions']) > 5:
                        report.append(f"  - ... and {len(data['functions'])-5} more")
                report.append(f"- **Event Handlers:** {len(data['event_handlers'])}")
                report.append(f"- **API Calls:** {len(data['api_calls'])}")
                if data['api_calls']:
                    for api in data['api_calls']:
                        report.append(f"  - `{api}`")
                report.append("")
        
        if self.routes:
            report.append("## API Routes")
            report.append("")
            for route in self.routes:
                methods = ", ".join(route['methods'])
                report.append(f"- **{methods}** `{route['path']}` → `{route['function']}()` in `{route['module']}.py`")
            report.append("")
        
        with open(os.path.join(output_dir, "project_analysis.md"), 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        print(f"✓ Saved: project_analysis.md")
        
        return output_dir


def main():
    print("=" * 70)
    print("PROJECT ARCHITECTURE ANALYZER".center(70))
    print("=" * 70)
    print()
    
    # Use current directory
    project_path = os.getcwd()
    print(f"📁 Analyzing: {project_path}")
    print()
    
    analyzer = ProjectAnalyzer(project_path)
    
    print("🔍 Scanning files...")
    analyzer.analyze_project()
    
    print("\n📊 Generating diagrams...")
    output_dir = analyzer.save_diagrams()
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE!".center(70))
    print("=" * 70)
    print(f"\n📂 Output folder: {output_dir}")
    print("\nGenerated files:")
    print("  1. architecture.mmd - Full system architecture diagram")
    print("  2. database_schema.mmd - Database entity relationships")
    print("  3. sequence_flow.mmd - User interaction flow")
    print("  4. project_analysis.md - Complete analysis report")
    print("\n💡 View diagrams at: https://mermaid.live")
    print("   (Copy/paste .mmd file contents)")
    print()


if __name__ == "__main__":
    main()