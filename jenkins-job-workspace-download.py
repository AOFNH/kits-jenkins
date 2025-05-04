import os

import requests
from dotenv import load_dotenv

load_dotenv()


def get_config():
    config = {
        "host": os.getenv("JENKINS_HOST"),
        "base_path": os.getenv("JENKINS_BASE_PATH"),
        "headers": {
            'Accept': os.getenv("HEADER_ACCEPT"),
            'User-Agent': os.getenv("HEADER_USER_AGENT"),
            'Referer': None  # Dynamic settings
        },
        "cookies": {
            'jenkins-timestamper-offset': os.getenv("COOKIE_TIMESTAMPER_OFFSET"),
            'JSESSIONID.d1fdbf4f': os.getenv("COOKIE_JSESSIONID"),
            'screenResolution': os.getenv("COOKIE_SCREENRESOLUTION")
        }
    }

    # 验证必要配置
    required = [
        ("JENKINS_HOST", config["host"]),
        ("JENKINS_BASE_PATH", config["base_path"]),
        ("COOKIE_JSESSIONID", config["cookies"]["JSESSIONID.d1fdbf4f"])
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
    config['headers']['Referer'] = referer

    files = [
        (f"{referer}*zip*/{job_name}.zip", f"{job_name}.zip"),
        (f"{referer}.gitignore", ".gitignore"),
        (f"{referer}.git/*zip*/.git.zip", ".git.zip")
    ]

    for url, filename in files:
        try:
            r = requests.get(
                url,
                headers=config['headers'],
                cookies=config['cookies'],
                verify=False
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


if __name__ == "__main__":
    try:
        with open("jobs.txt") as f:
            jobs = [line.strip() for line in f if line.strip()]

        for job in jobs:
            print(f"\nProcessing {job}:")
            download_job_files(job)

    except FileNotFoundError:
        print("Error: Missing jobs.txt file")
    except ValueError as ve:
        print(f"Configuration Error: {str(ve)}")
