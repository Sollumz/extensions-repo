"""
Generates the packages listing JSON for Sollumz stable and nightly.

Example:
    PS > $BLENDER = "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    PS > python .\gen_listing.py "$BLENDER" ./_repo
"""

import argparse
import subprocess
import tomllib
import uuid
from pathlib import Path
import requests
import zipfile
import io

STABLE = "<stable_marker>"  # latest release

SOLLUMZ_REPO = ("Sollumz", "Sollumz")  # (owner, name)
SOLLUMZ_RDR_REPO = ("Sollumz", "Sollumz-RDR")
VICHO_TOOLS_REPO = ("Hancapo", "VichoTools")
RUBY_MLO_SCALEFORM_TOOLS_REPO = ("Rubyyss", "MLOScaleformTool")

PACKAGES = (
    # repo             commit-ish/STABLE
    (SOLLUMZ_REPO,                  STABLE),
    (SOLLUMZ_REPO,                  "main"),  # development package
    (SOLLUMZ_RDR_REPO,              "main"),
    (VICHO_TOOLS_REPO,              STABLE),
    (RUBY_MLO_SCALEFORM_TOOLS_REPO, STABLE),
)

# TODO: for dev package check success CI (https://api.github.com/repos/Sollumz/Sollumz/commits/8769218f2882f548b914de17ff4264d919ce0c44/check-runs)


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


USER_AGENT = "Sollumz (extensions-repo)"
GITHUB_HEADERS = {
    "User-Agent": USER_AGENT,
    "X-GitHub-Api-Version": "2022-11-28",
}


def github_get_release_by_tag(repo, tag_name):
    owner, name = repo
    url = f"https://api.github.com/repos/{owner}/{name}/releases/tags/{tag_name}"
    req = requests.get(url, headers=GITHUB_HEADERS | {"Accept": "application/vnd.github+json"})
    return req.json() if req.status_code == 200 else None


def github_dowload_release_asset(repo, asset_id):
    owner, name = repo
    url = f"https://api.github.com/repos/{owner}/{name}/releases/assets/{asset_id}"
    req = requests.get(url, headers=GITHUB_HEADERS | {"Accept": "application/octet-stream"})
    return req.content if req.status_code == 200 else None


def validate_extension_manifest(repo, commitish, blender_manifest_path, used_extension_ids):
    """Validates a blender_manifest.toml. Not exhaustive. Returns the extension 'id' or None if invalid."""

    if not blender_manifest_path.is_file():
        print(
            f"Package {repo}-{commitish} is missing the blender_manifest.toml. "
            "Not generating an extension package."
        )
        return None

    with blender_manifest_path.open("rb") as f:
        blender_manifest = tomllib.load(f)

    if "id" not in blender_manifest:
        print(
            f"Package {repo}-{commitish} is missing 'id' in the blender_manifest.toml. "
            "Not generating an extension package."
        )
        return None

    extension_id = blender_manifest["id"]

    if extension_id in used_extension_ids:
        other = used_extension_ids[extension_id]
        print(
            f"Extension ID '{extension_id}' from package {repo}-{commitish} already in use by package {other}. "
            "Not generating an extension package."
        )
        return None

    used_extension_ids[extension_id] = f"{repo}-{commitish}"
    return extension_id


def build_extension_package_from_git_archive(repo, work_dir, commitish, used_extension_ids, output_directory):
    """Creates the extension package through 'git archive' of a specific commit."""
    git_checkout(work_dir, commitish)

    blender_manifest_path = Path(work_dir).joinpath("blender_manifest.toml")
    extension_id = validate_extension_manifest(repo, commitish, blender_manifest_path, used_extension_ids)
    if extension_id is not None:
        git_archive(work_dir, commitish, output_directory.joinpath(f"{extension_id}.zip").absolute())


def build_extension_package_from_github_release(repo, release_tag, used_extension_ids, output_directory):
    """Tries to download the extension package from GitHub release assets.
    Returns False if it should try to create the package with 'git archive' (there is no release or no assets).
    """
    release = github_get_release_by_tag(repo, release_tag)
    if release is None:
        print(
            f"Found tag '{release_tag}' for package {repo}-STABLE but no GitHub release. "
            "Generating extension package with 'git archive'."
        )
        return False

    assets = release["assets"]
    if not assets:
        print(
            f"Found tag '{release_tag}' and GitHub release for package {repo}-STABLE but no release assets. "
            "Generating extension package with 'git archive'."
        )
        return False

    asset = assets[0]
    asset_name = asset["name"]
    asset_id = asset["id"]
    print(
        f"Found tag '{release_tag}' and GitHub release for package {repo}-STABLE. "
        f"Downloading extension package from release asset '{asset_name}' (id: {asset_id})."
    )
    asset_data = github_dowload_release_asset(repo, asset_id)
    try:
        with zipfile.ZipFile(io.BytesIO(asset_data)) as zip:
            blender_manifest_path = zipfile.Path(zip, "blender_manifest.toml")
            if not blender_manifest_path.is_file():
                root_dir_name = asset_name.removesuffix(".zip")
                blender_manifest_path = zipfile.Path(zip, f"{root_dir_name}/blender_manifest.toml")

            extension_id = validate_extension_manifest(repo, "STABLE", blender_manifest_path, used_extension_ids)
            if extension_id is not None:
                with output_directory.joinpath(f"{extension_id}.zip").open("wb") as f:
                    f.write(asset_data)
            return True
    except Exception as e:
        print(
            f"Release asset '{asset_name}' is not a valid ZIP file. "
            "Not generating an extension package."
        )
        print(f"Exception: {e}")
        return True

    return False


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
    for repo, commitish in PACKAGES:
        owner, name = repo
        repo_url = f"https://github.com/{owner}/{name}.git"
        work_dir = ".work_dir_" + uuid.uuid4().hex
        git_clone_repo(repo_url, work_dir)

        if commitish == STABLE:
            release_tag = git_get_latest_release(work_dir)
            if build_extension_package_from_github_release(repo, release_tag, used_extension_ids, output_directory):
                continue
            else:
                commitish = release_tag  # fallback to git archive

        build_extension_package_from_git_archive(repo, work_dir, commitish, used_extension_ids, output_directory)

    blender_extension_server_generate(blender_executable, output_directory)


if __name__ == "__main__":
    main()
