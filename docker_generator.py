#!/usr/bin/env python3
"""
AI-Powered DevOps Automation Tool
Author: Sethu Satheesh
Version: 2.0.0
"""

import os
import sys
import re
import json
import logging
import argparse
from pathlib import Path
from functools import wraps
from typing import Dict, List
# import openai
from openai import OpenAI
import yaml
from logging.handlers import RotatingFileHandler

# --------------------------
# Configuration
# --------------------------
# Get the API key from the environment variable
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("No API key found. Please set the OPENAI_API_KEY environment variable.")

SUPPORTED_PROJECT_TYPES = ['node', 'python', 'java', 'go', 'dotnet']
DEFAULT_IGNORE_PATTERNS = [
    '**/node_modules', '**/.git', '**/__pycache__', '*.env', '*.secret',
    '**/*.log', '**/venv', '**/.idea', '**/.vscode'
]
AI_MODEL = "gpt-4"
MAX_TOKENS = 2000
client = OpenAI(api_key=api_key)

# --------------------------
# Logging Configuration
# --------------------------
def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rotation and verbosity"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                'docker-gen.log', maxBytes=10 * 1024 * 1024, backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    logging.getLogger('openai').setLevel(logging.WARNING)


# --------------------------
# Error Handling
# --------------------------
def handle_errors(func):
    """Decorator for error handling and logging"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            raise

    return wrapper


# --------------------------
# Project Analysis Core
# --------------------------
def parse_env_file(file_path: Path) -> Dict[str, str]:
    """Parse .env file into key-value pairs"""
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
    """Register Docker service in context"""
    service_name = file_path.parent.name
    context['services'][service_name] = {
        'type': 'docker',
        'path': str(file_path.parent),
        'dockerfile': str(file_path)
    }
    logging.info(f"Registered Docker service: {service_name}")


def detect_microservices(context: Dict) -> None:
    """Detect microservices architecture patterns"""
    # Detect multiple Docker services
    docker_services = [s for s in context['services'].values() if s['type'] == 'docker']
    if len(docker_services) > 1:
        context['service_patterns'].append('microservices')
        logging.info("Detected microservices architecture")

    # Detect service directories
    service_dirs = {'src/services', 'services', 'apps'}
    for file_path in context['detected_files']:
        parent_dir = Path(file_path).parent.name
        if parent_dir in service_dirs:
            context['service_patterns'].append('service-directory')
            logging.info(f"Found service directory: {parent_dir}")


def detect_entry_points(context: Dict) -> None:
    """Detect application entry points"""
    entry_points = []
    project_type = context['project_type']

    if project_type == 'node':
        # Check package.json files
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
        entry_points = [f for f in context['detected_files']
                        if Path(f).name in common_entries]

    elif project_type == 'java':
        entry_points = [f for f in context['detected_files']
                        if f.endswith(('Application.java', 'Main.java'))]

    context['entry_points'] = list(set(entry_points))
    logging.info(f"Detected entry points: {context['entry_points']}")


def detect_ports(context: Dict) -> None:
    """Detect potential ports from config and code"""
    ports = set()

    # From environment variables
    if 'PORT' in context['env_vars']:
        try:
            ports.add(int(context['env_vars']['PORT']))
        except ValueError:
            pass

    # From Dockerfiles
    for service in context['services'].values():
        if service['type'] == 'docker':
            try:
                with open(service['dockerfile']) as f:
                    content = f.read()
                    matches = re.findall(r'EXPOSE\s+(\d+)', content)
                    ports.update(map(int, matches))
            except Exception as e:
                logging.warning(f"Error reading Dockerfile: {str(e)}")

    # From code patterns
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

    # Framework defaults
    framework_ports = {
        'node': 3000,
        'react': 3000,
        'express': 3000,
        'django': 8000,
        'flask': 5000,
        'spring-boot': 8080,
        'dotnet': 5000
    }

    for framework in context['frameworks']:
        if framework in framework_ports:
            ports.add(framework_ports[framework])

    context['ports'] = sorted([p for p in ports if 1 <= p <= 65535])
    logging.info(f"Detected ports: {context['ports']}")


@handle_errors
def analyze_project_structure(project_path: str) -> Dict:
    """Analyze project structure and return context"""
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

            # Detect project type
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

            # Detect frameworks
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

            # Process environment files
            if file == '.env':
                context['env_vars'].update(parse_env_file(file_path))

            # Register Docker services
            if file == 'Dockerfile':
                register_docker_service(file_path, context)

    detect_microservices(context)
    detect_entry_points(context)
    detect_ports(context)
    return context


# --------------------------
# AI Generation Core
# --------------------------
@handle_errors
def generate_with_ai(prompt: str, system_role: str) -> str:
    """Handle AI generation with error management"""
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content
    except client.RateLimitError:
        logging.error("API rate limit exceeded")
        sys.exit(1)
    except client.AuthenticationError:
        logging.error("Invalid API key")
        sys.exit(1)


def generate_dockerfile(context: Dict) -> str:
    """Generate optimized Dockerfile using AI"""
    prompt = f"""
    Create production Dockerfile for {context['project_type']} project
    Frameworks: {context['frameworks']}
    Entry points: {context['entry_points']}
    Ports: {context['ports']}
    Environment variables: {list(context['env_vars'].keys())}

    Requirements:
    - Multi-stage build
    - Non-root user
    - Security best practices
    - Production optimizations
    - Health checks

    Provide ONLY the Dockerfile content.
    """
    return generate_with_ai(
        prompt,
        "You are a senior DevOps engineer creating production Dockerfiles."
    )


def generate_docker_compose(context: Dict) -> str:
    """Generate docker-compose.yml using AI"""
    prompt = f"""
    Create docker-compose.yml for {context['project_type']} project
    Services: {len(context['services'])}
    Ports: {context['ports']}
    Environment variables: {list(context['env_vars'].keys())}

    Requirements:
    - Network isolation
    - Resource constraints
    - Volume management
    - Health checks
    - Production-grade settings

    Provide ONLY valid YAML.
    """
    return generate_with_ai(
        prompt,
        "You are a Docker expert creating production compose files."
    )


# --------------------------
# Security & Validation
# --------------------------
@handle_errors
def validate_dockerfile(content: str) -> str:
    """Perform security validation"""
    warnings = []
    checks = {
        r'FROM\s+.*:latest': 'Avoid latest tags',
        r'USER\s+root': 'Running as root user',
        r'ADD\s+': 'Use COPY instead of ADD',
        r'curl\s+\|': 'Insecure pipe installation',
        r'apk add\s+(?!.*--no-cache)': 'Missing cache cleanup'
    }

    for pattern, message in checks.items():
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(message)

    if warnings:
        logging.warning("Security Warnings:")
        for warn in warnings:
            logging.warning(f"  - {warn}")

    return content


# --------------------------
# File Operations
# --------------------------
@handle_errors
def write_config(output_dir: str, filename: str, content: str, force: bool = False) -> None:
    """Safe file writer with conflict resolution"""
    output_path = Path(output_dir) / filename
    if output_path.exists() and not force:
        raise FileExistsError(f"{output_path} exists. Use --force to overwrite.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    logging.info(f"Generated: {output_path}")


# --------------------------
# Main CLI
# --------------------------
def main():
    parser = argparse.ArgumentParser(
        description='AI-Powered DevOps Automation Tool',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('project_dir', help='Path to project directory')
    parser.add_argument('-o', '--output', default='.', help='Output directory')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing files')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable debug logging')

    args = parser.parse_args()
    setup_logging(args.verbose)

    if not os.getenv("OPENAI_API_KEY"):
        logging.error("OPENAI_API_KEY environment variable required")
        sys.exit(1)

    try:
        context = analyze_project_structure(args.project_dir)

        docker_content = generate_dockerfile(context)
        validated_content = validate_dockerfile(docker_content)
        write_config(args.output, 'Dockerfile', validated_content, args.force)

        compose_content = generate_docker_compose(context)
        write_config(args.output, 'docker-compose.yml', compose_content, args.force)

        logging.info("Successfully generated infrastructure configuration")

    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
