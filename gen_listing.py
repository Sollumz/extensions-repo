"""
Generates the packages listing JSON for Sollumz stable and nightly.

Example:
    PS > $BLENDER = "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    PS > python .\gen_listing.py "$BLENDER" ./_repo
"""

import argparse
import subprocess
import shutil
import time
from pathlib import Path

EXAMPLE_LISTING_JSON = """{
   "version": "v1",
   "blocklist": [],
   "data": [
    {
       "id": "sollumz",
       "name": "Sollumz",
       "tagline": "Pretty epic add-on",
       "version": "2.5.0",
       "type": "add-on",
       "archive_size": 856650,
       "archive_hash": "sha256:3d2972a6f6482e3c502273434ca53eec0c5ab3dae628b55c101c95a4bc4e15b2",
       "archive_url": "https://repo.sollumz.org/packages/sollumz",
       "blender_version_min": "4.2.0",
       "maintainer": "Sollumz Team",
       "tags": ["Pipeline"],
       "license": ["SPDX:MIT"],
       "website": "http://sollumz.org/",
       "schema_version": "1.0.0"
    },
    {
       "id": "sollumz_nightly",
       "name": "Sollumz (Nightly)",
       "tagline": "Pretty epic add-on. Latest. Unstable",
       "version": "2.5.0-nightly-abcd123",
       "type": "add-on",
       "archive_size": 856650,
       "archive_hash": "sha256:3d2972a6f6482e3c502273434ca53eec0c5ab3dae628b55c101c95a4bc4e15b2",
       "archive_url": "https://repo.sollumz.org/packages/sollumz-nightly",
       "blender_version_min": "4.2.0",
       "maintainer": "Sollumz Team",
       "tags": ["Pipeline"],
       "license": ["SPDX:MIT"],
       "website": "http://sollumz.org/",
       "schema_version": "1.0.0"
    }
    ]
}
"""

STABLE = "<stable_marker>"    # latest release
NIGHTLY = "<nightly_marker>"  # latest commit

SOLLUMZ_REPO = "https://github.com/Sollumz/Sollumz.git"

PACKAGES = (
    # repo,         commit-ish/STABLE/NIGHTLY
    (SOLLUMZ_REPO,  STABLE),
    (SOLLUMZ_REPO,  NIGHTLY),
)


def git_clone_repo(repo_url, directory_name):
    proc = subprocess.run(
        ["git", "clone", "--no-checkout", repo_url, directory_name])
    proc.check_returncode()


def git_get_latest_release(directory_name):
    proc = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*.*.*"],
        cwd=directory_name,
        capture_output=True,
        text=True
    )
    proc.check_returncode()
    return proc.stdout.strip()


def git_checkout(directory_name, commitish):
    proc = subprocess.run(
        ["git", "checkout", commitish],
        cwd=directory_name,
    )
    proc.check_returncode()


def git_archive(directory_name, commitish, output_file):
    proc = subprocess.run(
        ["git", "archive", "--prefix", "Sollumz/", "-o", output_file, commitish],
        cwd=directory_name,
    )
    proc.check_returncode()


def blender_extension_server_generate(blender_exe, repo_dir):
    proc = subprocess.run(
        [blender_exe, "--command", "extension", "server-generate", "--repo-dir", repo_dir],
    )
    proc.check_returncode()


def main():
    parser = argparse.ArgumentParser(
        prog="gen_listing",
        description="Generates the packages listing JSON for Sollumz stable and nightly."
    )
    parser.add_argument("blender_executable", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    blender_executable = args.blender_executable
    output_directory = args.output_directory

    print(f"Blender Executable: {blender_executable}")
    print(f"Output Directory:   {output_directory.absolute()}")

    if not blender_executable.is_file():
        raise FileNotFoundError(blender_executable)

    output_directory.mkdir(exist_ok=True)

    # with open(output_directory.joinpath("index.json"), mode="w") as f:
    #     f.write(EXAMPLE_LISTING_JSON)

    work_dir = "work_dir_" + time.strftime("%Y%m%d-%H%M%S")
    git_clone_repo(PACKAGES[0][0], work_dir)
    # latest_release = git_get_latest_release(work_dir)
    git_checkout(work_dir, "dev/extension-manifest")
    git_archive(work_dir, "HEAD", output_directory.joinpath(
        "Sollumz.zip").absolute())
    blender_extension_server_generate(blender_executable, output_directory)

    # time.sleep(5)

    # shutil.rmtree("work_dir")


if __name__ == "__main__":
    main()
