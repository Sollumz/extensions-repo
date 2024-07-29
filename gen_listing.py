"""
Generates the packages listing JSON for Sollumz stable and nightly.

Example:
    PS > $BLENDER = "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    PS > python .\gen_listing.py "$BLENDER" ./_repo
"""

import argparse
import subprocess
import time
import tomllib
import uuid
from pathlib import Path

STABLE = "<stable_marker>"  # latest release

SOLLUMZ_REPO = "https://github.com/Sollumz/Sollumz.git"

PACKAGES = (
    # repo,         commit-ish/STABLE
    (SOLLUMZ_REPO,  STABLE),
    (SOLLUMZ_REPO,  "main"), # development package
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
        ["git", "archive", "--prefix", Path(output_file).stem + "/", "-o", output_file, commitish],
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
        description="Generates the packages listing JSON for the Sollumz extensions repository."
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

    used_extension_ids = {}
    for repo_url, commitish in PACKAGES:
        work_dir = ".work_dir_" + uuid.uuid4().hex
        git_clone_repo(repo_url, work_dir)

        if commitish == STABLE:
            commitish = git_get_latest_release(work_dir)

        git_checkout(work_dir, commitish)

        blender_manifest_path = Path(work_dir).joinpath("blender_manifest.toml")
        if not blender_manifest_path.is_file():
            print(
                f"Package '{repo_url}'-{commitish} is missing the blender_manifest.toml. "
                "Not generating an extension package."
            )
            continue

        with open(blender_manifest_path, "rb") as f:
            blender_manifest = tomllib.load(f)

        if "id" not in blender_manifest:
            print(
                f"Package '{repo_url}'-{commitish} is missing 'id' in the blender_manifest.toml. "
                "Not generating an extension package."
            )
            continue

        extension_id = blender_manifest["id"]

        if extension_id in used_extension_ids:
            other = used_extension_ids[extension_id]
            print(
                f"Extension ID '{extension_id}' from package '{repo_url}'-{commitish} already in use by package {other}. "
                "Not generating an extension package."
            )
            continue

        used_extension_ids[extension_id] = f"'{repo_url}'-{commitish}"

        git_archive(work_dir, commitish, output_directory.joinpath(f"{extension_id}.zip").absolute())

    blender_extension_server_generate(blender_executable, output_directory)


if __name__ == "__main__":
    main()
