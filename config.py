# config.py
import os

# Get API key from environment
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    raise ValueError("No API key found. Please set the OPENAI_API_KEY environment variable.")

SUPPORTED_PROJECT_TYPES = ['node', 'python', 'java', 'go', 'dotnet']
DEFAULT_IGNORE_PATTERNS = [
    '**/node_modules', '**/.git', '**/__pycache__', '*.env', '*.secret',
    '**/*.log', '**/venv', '**/.idea', '**/.vscode'
]
AI_MODEL = "gpt-4"
MAX_TOKENS = 2000

# In future, load additional user configuration (e.g., from config.yaml) if needed.