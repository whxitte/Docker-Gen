# Docker Gen AI 🚀

A powerful tool for automating the generation of Dockerfiles and `docker-compose.yml` files, optimized with AI and built for production-grade deployments.

## Key Features 🔑

### Enterprise-Grade Architecture
- Modular design with clear separation of concerns
- Comprehensive error handling and logging
- Configurable output directories
- Force overwrite protection

### Advanced AI Integration
- GPT-4 optimized prompts for generating Dockerfiles and `docker-compose.yml` files
- Rate limit handling for API interactions
- Temperature control for consistent results
- Framework-specific optimizations

### Production Security
- Dockerfile validation suite for security and optimization
- Security best practice enforcement
- Environment variable protection
- Non-root user enforcement

### DevOps Automation
- Microservices detection and configuration
- Multi-project type support (Node.js, Python, Ruby, etc.)
- Automatic dependency analysis for accurate Dockerfile generation
- Health check integration for service health monitoring

### Operational Excellence
- Rotating log files for easy troubleshooting
- Verbose debugging mode for in-depth insights
- CLI help and documentation for easy usage
- Cross-platform compatibility (Windows, macOS, Linux)


## Installation ⬇️

### Install dependencies
Make sure you have the required dependencies:

```bash
pip install openai pyyaml typing-extensions
```

## Usage 🚀

### Basic Usage
Set the OpenAI API key environment variable and run the script:

```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Basic usage
python docker-gen.py /path/to/project
```
## Advanced Usage 🚀

Customize output and enable verbose debugging:

```bash
# Advanced usage
python docker-gen.py /path/to/project \
  --output ./infra \
  --force \
  --verbose
```
## Run with Different Verbosity Levels

```
# Basic usage
docker-gen ./my-project


# Verbose mode
docker-gen ./my-project -v

# Custom output directory
docker-gen ./my-project -o ./output
Integrate with CI/CD
```

## GitHub Actions Example
```
- name: Generate Infrastructure
  run: |
    pip install docker-gen-ai
    docker-gen . -o ./infra
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```
