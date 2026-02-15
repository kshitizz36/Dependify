# server.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, Request
from typing import Optional, Dict
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from docker.errors import DockerException, ContainerError
import os
import subprocess
import asyncio
import json
import shutil
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import configuration and authentication
from config import Config
from auth import AuthService, get_current_user, get_optional_user

# Import updated app objects from modules
from containers import app as container_app, run_script
from modal_write import app as write_app, process_file
from modal_verify import app as verify_app, verify_and_fix
from git_driver import load_repository, create_and_push_branch, create_pull_request, create_fork
from socket_manager import ConnectionManager

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Dependify API",
    description="AI-powered code modernization and technical debt reduction",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize WebSocket manager
manager = ConnectionManager()

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Define request models
class UpdateRequest(BaseModel):
    repository: str = Field(..., description="GitHub repository URL")
    repository_owner: str = Field(..., description="Repository owner username")
    repository_name: str = Field(..., description="Repository name")

    @validator('repository')
    def validate_repository_url(cls, v):
        """Validate that repository URL is a valid GitHub URL."""
        if not v.startswith(('https://github.com/', 'git@github.com:')):
            raise ValueError('Repository must be a valid GitHub URL')
        return v


class GitHubOAuthRequest(BaseModel):
    code: str = Field(..., description="GitHub OAuth authorization code")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify server is running."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "message": "Dependify API is running"
    }


# GitHub OAuth endpoints
@app.post("/auth/github", response_model=AuthResponse, tags=["Authentication"])
@limiter.limit("10/minute")
async def github_oauth(request: Request, oauth_request: GitHubOAuthRequest):
    """
    Exchange GitHub OAuth code for access token.

    This endpoint is called after user authorizes your app on GitHub.
    request must be a starlette.requests.Request instance for slowapi.
    """
    try:
        github_data = await AuthService.exchange_github_code(oauth_request.code)

        # Create JWT token for our API
        user_data = github_data["user"]
        access_token = AuthService.create_access_token(
            data={
                "user_id": user_data["id"],
                "username": user_data["login"],
                "github_token": github_data["github_token"]
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user information."""
    return {"user": current_user}


@app.post('/update', tags=["Repository"])
@limiter.limit(f"{Config.RATE_LIMIT_PER_HOUR}/hour")
async def update(request: Request, payload: UpdateRequest,
                 current_user: Optional[Dict] = Depends(get_optional_user)):
    """
    Process a repository to modernize code and create a pull request.

    This endpoint:
    1. Analyzes repository files for outdated syntax (Reader Agent - Sonnet)
    2. Uses LLM to refactor code (Writer Agent - Haiku)
    3. Verifies and fixes changes (Verifier Agent - Sonnet)
    4. Creates a new branch with changes
    5. Submits a pull request

    Requires authentication for private repositories.
    """
    staging_dir = None

    try:
        print(f"Processing repository: {payload.repository}")

        # Create staging area
        staging_dir = os.path.join(os.getcwd(), "staging")

        # Clean up existing staging directory
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
        os.makedirs(staging_dir)

        # Run container-based script execution to analyze files
        print("Step 1: Analyzing files with Reader Agent (Sonnet)...")
        with container_app.run():
            job_list = run_script.remote(payload.repository)

        if not job_list:
            return {
                "status": "success",
                "message": "No outdated files found in repository",
                "repository": payload.repository,
                "files_analyzed": 0,
                "files_updated": 0
            }

        print(f"Found {len(job_list)} files to update")

        # Step 2: Refactor files with Writer Agent (Haiku - parallel)
        print("Step 2: Refactoring files with Writer Agent (Haiku)...")
        write_outputs = []
        with write_app.run():
            print(f"⚡ Processing {len(job_list)} files in parallel...")
            
            i = 0
            async for output in process_file.map.aio(job_list):
                i += 1
                if output and output.get("refactored_code"):
                    write_outputs.append(output)
                    print(f"✍️ Written {i}/{len(job_list)}: {output.get('file_path', 'unknown')}")
                else:
                    print(f"⚠️ Skipped {i}/{len(job_list)}: No output")

        if not write_outputs:
            raise HTTPException(
                status_code=400,
                detail="Failed to refactor any files. Please check if the repository contains valid code files."
            )

        # Step 3: Verify and fix with Verifier Agent (Sonnet - parallel)
        print("Step 3: Verifying changes with Verifier Agent (Sonnet)...")
        verify_jobs = []
        for output in write_outputs:
            original = next(
                (j for j in job_list if j.get("path") == output.get("file_path")),
                None
            )
            verify_jobs.append({
                "file_path": output["file_path"],
                "original_code": original.get("code_content", "") if original else "",
                "refactored_code": output["refactored_code"],
                "comments": output.get("refactored_code_comments", "")
            })

        refactored_jobs = []
        with verify_app.run():
            print(f"🔍 Verifying {len(verify_jobs)} files in parallel...")
            i = 0
            async for result in verify_and_fix.map.aio(verify_jobs):
                i += 1
                if result and result.get("refactored_code"):
                    file_path = result.get("file_path", "")
                    new_path = (
                        f"{staging_dir}{file_path[24:]}" if file_path and len(file_path) > 24 else os.path.join(staging_dir, os.path.basename(file_path))
                    )
                    # Find original code for this file
                    original_job = next(
                        (j for j in job_list if j.get("path") == file_path),
                        None
                    )
                    refactored_jobs.append({
                        "path": new_path,
                        "new_content": result["refactored_code"],
                        "old_content": original_job.get("code_content", "") if original_job else "",
                        "comments": result.get("refactored_code_comments", "")
                    })
                    status = "✅" if result.get("verified") else "⚠️"
                    print(f"{status} Verified {i}/{len(verify_jobs)}: {file_path} (attempts: {result.get('attempts', 1)})")
                else:
                    print(f"❌ Failed {i}/{len(verify_jobs)}")

        if not refactored_jobs:
            raise HTTPException(
                status_code=400,
                detail="Failed to verify any files. Please check if the repository contains valid code files."
            )

        # Create fork of the repository (or get original if user owns it)
        print("Step 4: Checking repository ownership and creating fork if needed...")
        fork_result = create_fork(payload.repository_owner, payload.repository_name)
        
        if not fork_result:
            raise HTTPException(
                status_code=400,
                detail="Failed to access repository. Make sure GITHUB_TOKEN is configured correctly."
            )
        
        is_own_repo = fork_result.get("is_own_repo", False)
        repo_url = fork_result.get("clone_url")
        repo_owner_username = fork_result.get("owner", {}).get("login")
        
        if is_own_repo:
            print(f"User owns the repository - working directly on: {repo_url}")
        else:
            print(f"Fork created/found: {repo_url}")

        # Clone the repository (fork or original)
        print("Step 5: Cloning repository...")
        clone_cmd = ["git", "clone", repo_url, staging_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to clone repository: {result.stderr}"
            )

        # Load repository info
        print("Step 6: Loading repository information...")
        repo, origin, origin_url = load_repository(staging_dir)
        files_changed = []

        # Apply refactored code to files
        print("Step 7: Applying changes...")
        for job in refactored_jobs:
            file_path = job.get("path")

            if os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(job.get("new_content"))
                    files_changed.append(file_path)
                    print(f"Updated: {file_path}")
                except Exception as write_error:
                    print(f"Error writing file {file_path}: {write_error}")
            else:
                print(f"Warning: File {file_path} does not exist")

        if not files_changed:
            raise HTTPException(
                status_code=400,
                detail="No files were successfully updated"
            )

        # Create branch and push changes
        print("Step 8: Creating branch and pushing changes...")
        new_branch_name, username = create_and_push_branch(repo, origin, files_changed)

        # Create pull request (different logic for own repo vs fork)
        if is_own_repo:
            print("Step 9: Creating pull request in user's own repository...")
        else:
            print("Step 9: Creating pull request from fork to original repository...")
            
        pr_url = create_pull_request(
            new_branch_name,
            payload.repository_owner,  # Original repo owner
            payload.repository_name,   # Original repo name
            "main",                     # Base branch
            username,                   # User's username
            is_own_repo                 # Flag to indicate if it's user's own repo
        )

        # Build response with fork information
        response_data = {
            "status": "success",
            "message": "Repository updated and pull request created successfully",
            "repository": payload.repository,
            "files_analyzed": len(job_list),
            "files_updated": len(files_changed),
            "branch": new_branch_name,
            "pull_request_url": pr_url,
            "is_own_repo": is_own_repo,
            "output": refactored_jobs[:5]  # Return first 5 for preview
        }
        
        # Add fork information if it was forked
        if not is_own_repo:
            response_data["fork_info"] = {
                "message": "A temporary staging fork was created to propose these changes",
                "fork_owner": username,
                "fork_name": payload.repository_name,
                "can_delete": True,
                "delete_note": "You can safely delete this fork after the PR is merged or closed"
            }
        
        return response_data

    except HTTPException:
        raise
    except ContainerError as ce:
        err_output = ce.stderr.decode("utf-8") if ce.stderr else str(ce)
        raise HTTPException(status_code=500, detail=f"Container execution error: {err_output}")
    except DockerException as de:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(de)}")
    except subprocess.CalledProcessError as pe:
        raise HTTPException(status_code=500, detail=f"Git operation failed: {str(pe)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # Cleanup staging directory
        if staging_dir and os.path.exists(staging_dir):
            try:
                shutil.rmtree(staging_dir)
                print("Cleaned up staging directory")
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up staging directory: {cleanup_error}")


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates during repository processing.

    Clients can connect to receive live progress updates.
    """
    await manager.connect(websocket, client_id or "default")
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        await manager.disconnect(client_id or "default")
        print(f"Client {client_id or 'default'} disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await manager.disconnect(client_id or "default")


@app.on_event("startup")
async def startup_event():
    """
    Run validation checks on startup.
    """
    print("=" * 60)
    print("Starting Dependify API v2.0.0")
    print("=" * 60)

    # Validate configuration
    is_valid, missing_vars = Config.validate()
    if not is_valid:
        print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing_vars)}")
        print("Some features may not work correctly.")
    else:
        print("✅ Configuration validated successfully")

    print(f"CORS allowed origins: {Config.get_allowed_origins()}")
    print(f"Rate limit: {Config.RATE_LIMIT_PER_HOUR} requests/hour")
    print("=" * 60)


if __name__ == '__main__':
    import uvicorn

    # Use PORT environment variable from Config
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=False,
        log_level="info"
    )
