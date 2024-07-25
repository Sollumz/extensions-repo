"""
Generates the packages listing JSON for Sollumz stable and nightly.

Example:
    PS > $BLENDER = "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    PS > python .\gen_listing.py "$BLENDER" ./_repo
"""

import argparse
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
       "id": "sollumz-nightly",
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

def main():
    parser = argparse.ArgumentParser(
        prog="gen_listing",
        description="Generates the packages listing JSON for Sollumz stable and nightly."
    )
    parser.add_argument("blender_executable", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    blender_executable: Path = args.blender_executable
    output_directory: Path = args.output_directory

    print(f"Blender Executable: {blender_executable}")
    print(f"Output Directory:   {output_directory.absolute()}")


    if not blender_executable.is_file():
        raise FileNotFoundError(blender_executable)

    output_directory.mkdir(exist_ok=True)

    with open(output_directory.joinpath("index.json"), mode="w") as f:
        f.write(EXAMPLE_LISTING_JSON)

if __name__ == "__main__":
    main()
