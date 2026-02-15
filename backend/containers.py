import os
import modal
import subprocess
from checker import fetch_updates
from checker import CodeChange

# Create Modal image with all necessary dependencies
image = modal.Image.debian_slim(python_version="3.10") \
    .apt_install("git", "python3", "bash") \
    .pip_install(
        "python-dotenv",
        "anthropic",
        "fastapi",
        "uvicorn",
        "modal",
        "pydantic",
        "websockets",
        "supabase"
    ) \
    .add_local_python_source("checker") \
    .add_local_python_source("config") \
    .add_local_python_source("auth") \
    .add_local_python_source("server")

app = modal.App(name="claude-read", image=image)


@app.function(
    timeout=600,  # 10 minutes for large repos
    max_containers=50,  # Allow up to 50 parallel analysis workers
    min_containers=2,  # Keep 2 containers warm to avoid cold starts
    secrets=[
        modal.Secret.from_name("ANTHROPIC_API_KEY"),
        modal.Secret.from_name("SUPABASE_URL"),
        modal.Secret.from_name("SUPABASE_KEY")
    ]
)
def run_script(repo_url: str) -> list[CodeChange]:
    """
    Clones the given repository, analyzes files for outdated syntax,
    and returns a list of CodeChange objects.

    Args:
        repo_url: GitHub repository URL to analyze

    Returns:
        List of CodeChange objects representing files that need updates
    """
    import os

    subprocess.run(
        ["git", "clone", "https://github.com/kshitizz36/pot-tools.git", "scripts"],
        check=True,
        capture_output=True,
        text=True
    ).stdout

    os.chdir("scripts")
    subprocess.run(
        ["git", "clone", repo_url, "repository"],
        check=True,
        capture_output=True,
        text=True
    ).stdout

    subprocess.run(
        ["ls", "repository"],
        check=True,
        capture_output=True,
        text=True
    ).stdout

    data = fetch_updates(os.getcwd() + "/repository")

    return [change.model_dump(mode="json") for change in data]  # Ensure CodeChange is serializable
