#!/usr/bin/env python3

import os
import subprocess
import argparse
from typing import List
from pathlib import Path
import re
import yaml  # For reading YAML config

# Global settings for the blog. Update these manually as desired.
BLOG_TITLE = "Crazy Treyn Blog"  # Set the main blog title manually
BLOG_SUBTITLE = "A different kind of Data Analytics blog."  # Set the subtitle manually


def export_html_wasm(notebook_path: str, output_dir: str, as_app: bool = False) -> bool:
    """
    Export a single marimo notebook to HTML format.

    Args:
        notebook_path (str): Path to the .py notebook file.
        output_dir (str): Directory to place the exported HTML file.
        as_app (bool): Whether to export as an app (run mode) or as a notebook (edit mode).

    Returns:
        bool: True if export succeeded, False otherwise.
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
    """
    Generate the index.html file with sorted notebooks in descending order.
    Applies a dark theme to match the desired style.
    The blog title and subtitle are set manually via global constants.
    Additionally, ensures the image is left aligned next to the title/description and limits card widths.
    """
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
            # Start of HTML with a centered container to limit width
            f.write(
                """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>""" + BLOG_TITLE + """</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-[#282c34] text-[#abb2bf] font-sans p-8">
    <div class="max-w-4xl mx-auto">
      <div class="mb-8 text-center">
        <!-- Manually set blog title and subtitle -->
        <h1 class="text-3xl font-bold mb-2 text-[#abb2bf]">""" + BLOG_TITLE + """</h1>
        <p class="text-[#5c6370]">""" + BLOG_SUBTITLE + """</p>
      </div>
      <div class="grid gap-4 grid-cols-1">\n"""
            )

            # Build cards for each notebook
            for notebook in all_notebooks:
                nb_filename = Path(notebook).name.replace(".py", "")
                # Remove a date prefix if present (e.g., 2025-03-15-)
                key = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", nb_filename)

                # Lookup metadata using the key
                meta = notebook_metadata.get(key, {})
                title = meta.get("title", key.replace("_", " ").title())
                description = meta.get("description", "")
                image = meta.get("image", "")

                # Begin card container with limited width
                f.write(
                    f'      <a href="{notebook.replace(".py", ".html")}" '
                    'class="block w-full p-6 border border-[#5c6370] rounded transition duration-200 hover:bg-[#3E4451] max-w-xl mx-auto">\n'
                )

                # Create a flex container so the image is on the right side
                f.write('        <div class="flex items-start space-x-4">\n')

                # Title + description on the left
                f.write('          <div>\n')
                f.write(f'            <h3 class="text-2xl font-semibold mb-2 text-[#61afef]">{title}</h3>\n')
                if description:
                    f.write(f'            <p class="text-[#abb2bf]">{description}</p>\n')
                f.write('          </div>\n')

                # Image on the right
                if image:
                    f.write(
                        f'          <img src="{image}" alt="{title}" '
                        'class="w-32 h-auto rounded" />\n'
                    )

                f.write('        </div>\n')
                f.write('      </a>\n')

            # End of HTML
            f.write(
                """      </div>\n    </div>\n  </body>\n</html>"""
            )
    except IOError as e:
        print(f"Error generating index.html: {e}")


def main() -> None:
    """
    Main entry point for the build script. Exports notebooks from the
    'notebooks' and 'apps' directories, then generates index.html if
    any notebooks are found.
    """
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

    # Generate index only if there is at least one notebook
    generate_index(all_notebooks, args.output_dir)


if __name__ == "__main__":
    main()