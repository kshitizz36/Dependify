import modal
import checker
import os
import supabase

# Create an image with all necessary dependencies
image = modal.Image.debian_slim(python_version="3.10") \
    .apt_install("git", "python3", "bash") \
    .pip_install("python-dotenv", "anthropic", "fastapi", "uvicorn", "modal", "pydantic", "websockets", "supabase") \
    .add_local_python_source("checker") \
    .add_local_python_source("modal_write") \
    .add_local_python_source("config") \
    .add_local_python_source("auth") \
    .add_local_python_source("containers") \
    .add_local_python_source("server")

app = modal.App(name="claude-write", image=image)

@app.function(
    timeout=300,  # 5 minutes per file
    max_containers=100,  # Process up to 100 files in parallel
    min_containers=3,  # Keep 3 containers warm for faster response
    secrets=[
        modal.Secret.from_name("ANTHROPIC_API_KEY"),
        modal.Secret.from_name("SUPABASE_URL"),
        modal.Secret.from_name("SUPABASE_KEY"),
    ],
)
def process_file(job):
    """
    Writer Agent: Refactors outdated code using Haiku (fast, parallel).

    Args:
        job: Dictionary containing file path and code content

    Returns:
        Dictionary with refactored code and comments
    """
    from pydantic import BaseModel, ValidationError
    from os import getenv
    import json
    import supabase
    from anthropic import Anthropic

    # Get credentials from Modal secrets (environment variables)
    ANTHROPIC_API_KEY = getenv("ANTHROPIC_API_KEY")
    SUPABASE_URL = getenv("SUPABASE_URL")
    SUPABASE_KEY = getenv("SUPABASE_KEY")

    # Initialize Supabase client
    supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

    class JobReport(BaseModel):
        refactored_code: str
        refactored_code_comments: str

    # Model configuration
    WRITER_MODEL = "claude-3-5-haiku-20241022"

    # Initialize Anthropic client (Writer Agent - Haiku)
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    file_path = job["path"]
    code_content = job["code_content"]

    user_prompt = (
        "Analyze the following code and determine if the syntax is out of date. "
        "If it is out of date, specify what changes need to be made in the following JSON format:\n\n"
        "{\n"
        '  "refactored_code": "A rewrite of the file that is more up to date, using the native language (i.e. if the file is a NextJS file, rewrite the NextJS file using Javascript/Typescript with the updated API changes). The file should be a complete file, not just a partial updated code segment.",\n'
        '  "refactored_code_comments": "Comments and explanations for your code changes. Be as descriptive, informative, and technical as possible."\n'
        "}\n\n"
        f"File: {file_path}\n\n"
        f"Code:\n{code_content}"
    )

    try:
        print(f"Processing file: {file_path}")

        response = client.messages.create(
            model=WRITER_MODEL,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": "You are a helpful assistant that analyzes code and returns a JSON object with the refactored code and the comments that come with it. Your goal is to identify outdated syntax in code and suggest changes to update it to the latest syntax. Return ONLY valid JSON with keys: refactored_code, refactored_code_comments.\n\n" + user_prompt
                }
            ]
        )

        # Parse response JSON into JobReport
        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        parsed = json.loads(response_text)
        job_report = JobReport(**parsed)

        # Update Supabase with progress
        filename = file_path.split("/")[-1]
        data = {
            "status": "WRITING",
            "message": f"✍️ Updating {filename}",
            "code": job_report.refactored_code
        }

        try:
            supabase_client.table("repo-updates").insert(data).execute()
        except Exception as db_error:
            # If filename/old_code columns don't exist, try without them
            print(f"Database error (may need to add columns): {db_error}")
            data_fallback = {
                "status": "WRITING",
                "message": f"✍️ Updating {filename}",
                "code": job_report.refactored_code
            }
            supabase_client.table("repo-updates").insert(data_fallback).execute()

        return {
            "file_path": file_path,
            **job_report.model_dump()
        }
    except (ValidationError, json.JSONDecodeError) as parse_error:
        print(f"Error parsing LLM response for {file_path}: {parse_error}")
        return None
    except Exception as e:
        # Handle any other exceptions, e.g. network errors, model issues, etc.
        print(f"Error analyzing {file_path}: {e}")
        return None
