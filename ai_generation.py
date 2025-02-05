# ai_generation.py
import logging
from config import AI_MODEL, MAX_TOKENS, API_KEY
from error_handling import handle_errors
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)


@handle_errors
def generate_with_ai(prompt: str, system_role: str) -> str:
    """Generate content using AI with error management."""
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
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        raise


@handle_errors
def generate_dockerfile(context: dict) -> str:
    """Generate a production-ready Dockerfile tailored to the project."""
    framework_details = ""
    if context['project_type'] == 'node' and 'express' in context['frameworks']:
        framework_details = "Apply Node.js with Express best practices."
    prompt = f"""
    Create a production Dockerfile for a {context['project_type']} project.
    Frameworks: {context['frameworks']} {framework_details}
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
    return generate_with_ai(prompt, "You are a senior DevOps engineer creating production Dockerfiles.")


@handle_errors
def generate_docker_compose(context: dict) -> str:
    """Generate a docker-compose.yml for multi-service and single-service projects."""
    prompt = f"""
    Create a docker-compose.yml for a {context['project_type']} project.
    Detected services: {list(context['services'].keys())}
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
    return generate_with_ai(prompt, "You are a Docker expert creating production compose files.")


@handle_errors
def generate_docker_readme(context: dict) -> str:
    """Generate documentation for the Docker setup."""
    prompt = f"""
    Generate a Docker README documentation for a {context['project_type']} project with the following details:
    - Detected frameworks: {context['frameworks']}
    - Services: {list(context['services'].keys())}
    - Entry points: {context['entry_points']}
    - Ports: {context['ports']}
    - Environment variables: {list(context['env_vars'].keys())}

    Include instructions on how to build and run the containers, best practices, and troubleshooting tips.

    Provide ONLY the markdown content.
    """
    return generate_with_ai(prompt, "You are a DevOps documentation expert.")
