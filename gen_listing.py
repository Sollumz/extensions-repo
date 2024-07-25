"""
Generates the packages listing JSON for Sollumz stable and nightly.

Example:
    PS > $BLENDER = "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    PS > python .\gen_listing.py "$BLENDER" ./_repo
"""

import argparse
from pathlib import Path


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
        f.write('{"hello": "world"}')

if __name__ == "__main__":
    main()
