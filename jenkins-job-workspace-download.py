import os
import zipfile
import shutil

import requests
from dotenv import load_dotenv

load_dotenv()


def get_config():
    config = {
        "host": os.getenv("JENKINS_HOST"),
        "base_path": os.getenv("JENKINS_BASE_PATH"),
        "headers": {
            "Accept": os.getenv("HEADER_ACCEPT"),
            "User-Agent": os.getenv("HEADER_USER_AGENT"),
            "Referer": None,  # Dynamic settings
        },
        "cookies": {
            "jenkins-timestamper-offset": os.getenv("COOKIE_TIMESTAMPER_OFFSET"),
            "JSESSIONID.d1fdbf4f": os.getenv("COOKIE_JSESSIONID"),
            "screenResolution": os.getenv("COOKIE_SCREENRESOLUTION"),
        },
    }

    # Validate required configurations
    required = [
        ("JENKINS_HOST", config["host"]),
        ("JENKINS_BASE_PATH", config["base_path"]),
        ("COOKIE_JSESSIONID", config["cookies"]["JSESSIONID.d1fdbf4f"]),
    ]

    for var_name, value in required:
        if not value:
            raise ValueError(f"Missing required environment variable: {var_name}")

    return config


def download_job_files(job_name):
    config = get_config()
    job_dir = os.path.join(os.getcwd(), os.getenv("DOWNLOAD_DIR"), job_name)
    os.makedirs(job_dir, exist_ok=True)

    referer = f"{config['host']}{config['base_path']}/{job_name}/ws/"
    config["headers"]["Referer"] = referer

    files = [
        (f"{referer}*zip*/{job_name}.zip", f"{job_name}.zip"),
        (f"{referer}.gitignore", ".gitignore"),
        (f"{referer}.git/*zip*/.git.zip", ".git.zip"),
    ]

    for url, filename in files:
        try:
            r = requests.get(
                url, headers=config["headers"], cookies=config["cookies"], verify=False
            )

            filepath = os.path.join(job_dir, filename)
            if r.status_code == 200:
                with open(filepath, "wb") as file:
                    file.write(r.content)
                print(f"[OK] {filename}")
            else:
                print(f"[{r.status_code}] {filename}")
        except Exception as e:
            print(f"[Error] {filename}: {str(e)}")


def extract_job_files(job_name):
    """Extract workspace files to the specified directory"""
    source_dir = os.path.join(os.getcwd(), os.getenv("DOWNLOAD_DIR"), job_name)

    # Remove prefix from job name for target directory
    prefix = os.getenv("ENV_JOB_PREFIX", "")
    clean_job_name = (
        job_name[len(prefix) :] if job_name.startswith(prefix) else job_name
    )
    target_dir = os.path.join(os.getcwd(), os.getenv("UNZIP_DIR"), clean_job_name)
    temp_dir = os.path.join(os.getcwd(), "temp_extract")

    # Ensure directories exist
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    # Iterate through all files in the source directory
    for filename in os.listdir(source_dir):
        source_path = os.path.join(source_dir, filename)

        # Process main workspace zip file
        if filename == f"{job_name}.zip":
            try:
                # First extract to temporary directory
                with zipfile.ZipFile(source_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Move contents from the internal directory with the same name to target directory
                inner_job_dir = os.path.join(temp_dir, job_name)
                if os.path.exists(inner_job_dir) and os.path.isdir(inner_job_dir):
                    for item in os.listdir(inner_job_dir):
                        source_item = os.path.join(inner_job_dir, item)
                        target_item = os.path.join(target_dir, item)
                        if os.path.isdir(source_item):
                            if os.path.exists(target_item):
                                shutil.rmtree(target_item)
                            shutil.copytree(source_item, target_item)
                        else:
                            shutil.copy2(source_item, target_item)
                    print(f"[OK] Extracted and moved contents from {filename}")
                    # Clean up temporary directory
                    shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir, exist_ok=True)
                else:
                    print(
                        f"[Error] Expected directory {job_name} not found in extracted contents"
                    )
            except Exception as e:
                print(f"[Error] Failed to process {filename}: {str(e)}")
        # Process other zip files
        elif filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(source_path, "r") as zip_ref:
                    zip_ref.extractall(target_dir)
                print(f"[OK] Extracted {filename}")
            except Exception as e:
                print(f"[Error] Failed to extract {filename}: {str(e)}")
        # Process non-zip files
        else:
            try:
                target_path = os.path.join(target_dir, filename)
                shutil.copy2(source_path, target_path)
                print(f"[OK] Copied {filename}")
            except Exception as e:
                print(f"[Error] Failed to copy {filename}: {str(e)}")

    # Finally clean up temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    try:
        with open("jobs.txt") as f:
            jobs = [line.strip() for line in f if line.strip()]

        for job in jobs:
            print(f"\nProcessing {job}:")
            download_job_files(job)
            print(f"\nExtracting {job}:")
            extract_job_files(job)

    except FileNotFoundError:
        print("Error: Missing jobs.txt file")
    except ValueError as ve:
        print(f"Configuration Error: {str(ve)}")
