# project_analysis.py
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict
from error_handling import handle_errors

def parse_env_file(file_path: Path) -> Dict[str, str]:
    """Parse .env file into key-value pairs."""
    env_vars = {}
    try:
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip("'").strip('"')
    except Exception as e:
        logging.warning(f"Error parsing {file_path}: {str(e)}")
    return env_vars

def register_docker_service(file_path: Path, context: Dict) -> None:
    """Register a Docker service in the context."""
    service_name = file_path.parent.name
    context['services'][service_name] = {
        'type': 'docker',
        'path': str(file_path.parent),
        'dockerfile': str(file_path)
    }
    logging.info(f"Registered Docker service: {service_name}")

def detect_microservices(context: Dict) -> None:
    """Detect microservices architecture patterns."""
    docker_services = [s for s in context['services'].values() if s['type'] == 'docker']
    if len(docker_services) > 1:
        context['service_patterns'].append('microservices')
        logging.info("Detected microservices architecture")
    # Check for common service directories
    service_dirs = {'src/services', 'services', 'apps'}
    for file_path in context['detected_files']:
        parent_dir = Path(file_path).parent.name
        if parent_dir in service_dirs:
            context['service_patterns'].append('service-directory')
            logging.info(f"Found service directory: {parent_dir}")

def detect_entry_points(context: Dict) -> None:
    """Detect application entry points."""
    entry_points = []
    project_type = context['project_type']
    if project_type == 'node':
        for file in context['detected_files']:
            if file.endswith('package.json'):
                try:
                    with open(file) as f:
                        pkg = json.load(f)
                        if 'main' in pkg:
                            entry_points.append(pkg['main'])
                        if 'scripts' in pkg and 'start' in pkg['scripts']:
                            entry_points.append(pkg['scripts']['start'])
                except Exception as e:
                    logging.warning(f"Error reading {file}: {str(e)}")
    elif project_type == 'python':
        common_entries = ['app.py', 'main.py', 'manage.py', 'wsgi.py']
        entry_points = [f for f in context['detected_files'] if Path(f).name in common_entries]
    elif project_type == 'java':
        entry_points = [f for f in context['detected_files'] if f.endswith(('Application.java', 'Main.java'))]
    context['entry_points'] = list(set(entry_points))
    logging.info(f"Detected entry points: {context['entry_points']}")

def detect_ports(context: Dict) -> None:
    """Detect potential ports from environment, Dockerfiles, and code patterns."""
    ports = set()
    if 'PORT' in context['env_vars']:
        try:
            ports.add(int(context['env_vars']['PORT']))
        except ValueError:
            pass
    for service in context['services'].values():
        if service['type'] == 'docker':
            try:
                with open(service['dockerfile']) as f:
                    content = f.read()
                    matches = re.findall(r'EXPOSE\s+(\d+)', content)
                    ports.update(map(int, matches))
            except Exception as e:
                logging.warning(f"Error reading Dockerfile: {str(e)}")
    port_patterns = [
        r'\.listen\(.*?(\d{4,5})',
        r'PORT\s*[:=]\s*(\d+)',
        r'port:\s*(\d+)',
        r'\bport\s*=\s*(\d+)'
    ]
    for file in context['detected_files']:
        if any(file.endswith(ext) for ext in ['.js', '.py', '.java', '.go', '.cs']):
            try:
                with open(file) as f:
                    content = f.read()
                    for pattern in port_patterns:
                        matches = re.findall(pattern, content)
                        ports.update(map(int, matches))
            except Exception as e:
                logging.debug(f"Error reading {file}: {str(e)}")
    # Add framework default ports
    framework_ports = {
        'node': 3000, 'react': 3000, 'express': 3000,
        'django': 8000, 'flask': 5000, 'spring-boot': 8080,
        'dotnet': 5000
    }
    for framework in context['frameworks']:
        if framework in framework_ports:
            ports.add(framework_ports[framework])
    context['ports'] = sorted([p for p in ports if 1 <= p <= 65535])
    logging.info(f"Detected ports: {context['ports']}")

@handle_errors
def analyze_project_structure(project_path: str) -> Dict:
    """Analyze the project structure and return a context dictionary."""
    context = {
        'project_type': 'unknown',
        'frameworks': [],
        'services': {},
        'dependencies': {},
        'env_vars': {},
        'entry_points': [],
        'ports': [],
        'detected_files': [],
        'service_patterns': []
    }
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '.git']]
        for file in files:
            file_path = Path(root) / file
            context['detected_files'].append(str(file_path))
            # Detect project type based on key files
            if file == 'package.json':
                context['project_type'] = 'node'
            elif file == 'requirements.txt':
                context['project_type'] = 'python'
            elif file == 'pom.xml':
                context['project_type'] = 'java'
            elif file == 'go.mod':
                context['project_type'] = 'go'
            elif file.endswith('.csproj'):
                context['project_type'] = 'dotnet'
            # Detect frameworks from package.json dependencies
            if file == 'package.json':
                try:
                    with open(file_path) as f:
                        pkg = json.load(f)
                        deps = pkg.get('dependencies', {})
                        if 'react' in deps:
                            context['frameworks'].append('react')
                        if 'express' in deps:
                            context['frameworks'].append('express')
                except Exception as e:
                    logging.warning(f"Error reading {file_path}: {str(e)}")
            if file == '.env':
                context['env_vars'].update(parse_env_file(file_path))
            if file == 'Dockerfile':
                register_docker_service(file_path, context)
    detect_microservices(context)
    detect_entry_points(context)
    detect_ports(context)
    return context
