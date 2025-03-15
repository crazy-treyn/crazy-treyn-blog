#!/usr/bin/env python3

import os
import subprocess
import argparse
from typing import List
from pathlib import Path
import re
import yaml  # New import for reading YAML config

def export_html_wasm(notebook_path: str, output_dir: str, as_app: bool = False) -> bool:
    """Export a single marimo notebook to HTML format.

    Returns:
        bool: True if export succeeded, False otherwise
    """
    output_path = notebook_path.replace(".py", ".html")

    cmd = ["marimo", "export", "html-wasm"]
    if as_app:
        print(f"Exporting {notebook_path} to {output_path} as app")
        cmd.extend(["--mode", "run", "--no-show-code"])
    else:
        print(f"Exporting {notebook_path} to {output_path} as notebook")
        cmd.extend(["--mode", "edit"])

    try:
        output_file = os.path.join(output_dir, output_path)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        cmd.extend([notebook_path, "-o", output_file])
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error exporting {notebook_path}:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error exporting {notebook_path}: {e}")
        return False


def generate_index(all_notebooks: List[str], output_dir: str) -> None:
    """Generate the index.html file with sorted notebooks in descending order."""
    print("Generating index.html")

    # Load notebook metadata from the YAML config file
    config_file = "notebook_metadata.yml"
    notebook_metadata = {}
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            notebook_metadata = config.get("notebooks", {})
    except FileNotFoundError:
        print(f"Config file {config_file} not found. Using default metadata.")
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")

    # Sort notebooks in descending order based on their filenames
    all_notebooks.sort(reverse=True, key=lambda x: Path(x).name)

    index_path = os.path.join(output_dir, "index.html")
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(index_path, "w") as f:
            f.write(
                """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>marimo Blog</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  </head>
  <body class="font-sans max-w-4xl mx-auto p-8 leading-relaxed bg-gray-900 text-white">
    <div class="mb-8">
      <img src="https://raw.githubusercontent.com/marimo-team/marimo/main/docs/_static/marimo-logotype-thick.svg" alt="marimo" class="h-20" />
    </div>
    <div class="grid gap-4">
"""
            )
            for notebook in all_notebooks:
                nb_filename = Path(notebook).name.replace(".py", "")
                # Remove a date prefix if present (e.g., 2025-03-15-)
                key = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", nb_filename)
                # Lookup metadata using the key
                meta = notebook_metadata.get(key, {})
                title = meta.get("title", key.replace("_", " ").title())
                description = meta.get("description", "")
                image = meta.get("image", "")

                # Build the HTML card for the notebook
                f.write(f'      <a href="{notebook.replace(".py", ".html")}" class="block p-6 border border-gray-700 rounded transition duration-200 hover:bg-gray-800">\n')
                if image:
                    f.write(f'        <img src="{image}" alt="{title}" class="w-full h-auto mb-4 rounded" />\n')
                f.write(f'        <h3 class="text-2xl font-semibold mb-2">{title}</h3>\n')
                if description:
                    f.write(f'        <p class="text-gray-300">{description}</p>\n')
                f.write('      </a>\n')
            f.write(
                """    </div>
  </body>
</html>"""
            )
    except IOError as e:
        print(f"Error generating index.html: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build marimo notebooks")
    parser.add_argument(
        "--output-dir", default="_site", help="Output directory for built files"
    )
    args = parser.parse_args()

    all_notebooks: List[str] = []
    for directory in ["notebooks", "apps"]:
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Warning: Directory not found: {dir_path}")
            continue

        all_notebooks.extend(str(path) for path in dir_path.rglob("*.py"))

    if not all_notebooks:
        print("No notebooks found!")
        return

    # Export notebooks sequentially
    for nb in all_notebooks:
        export_html_wasm(nb, args.output_dir, as_app=nb.startswith("apps/"))

    # Generate index only if all exports succeeded
    generate_index(all_notebooks, args.output_dir)


if __name__ == "__main__":
    main()