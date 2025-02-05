# main.py
import os
import sys
import logging
import argparse
from logging_setup import setup_logging
from project_analysis import analyze_project_structure
from ai_generation import generate_dockerfile, generate_docker_compose, generate_docker_readme
from file_operations import write_config


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

        # Generate and write Dockerfile
        dockerfile_content = generate_dockerfile(context)
        write_config(args.output, 'Dockerfile', dockerfile_content, args.force)

        # Generate and write docker-compose.yml
        compose_content = generate_docker_compose(context)
        write_config(args.output, 'docker-compose.yml', compose_content, args.force)

        # Generate Docker documentation README
        docker_readme = generate_docker_readme(context)
        write_config(args.output, 'dockerreadme.md', docker_readme, args.force)

        logging.info("Successfully generated infrastructure configuration and documentation.")
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
