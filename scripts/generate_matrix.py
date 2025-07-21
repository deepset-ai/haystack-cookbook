import argparse
import json
import re
import requests

import tomllib


def read_index(path):
    with open(path, "rb") as f:
        return tomllib.load(f)

def get_latest_stable_haystack_version():
    url = "https://hub.docker.com/v2/repositories/deepset/haystack/tags/?page_size=25"
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    tags = response.json()

    if tags and tags.get('results'):
        # filter out tags that include 'main'
        stable_tags = [tag for tag in tags['results'] if 'main' not in tag['name']]
        if stable_tags:
            # assuming the first tag is the latest stable version
            latest_stable_tag = stable_tags[0]['name']
            return latest_stable_tag

    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""python generate_matrix.py"""
    )
    parser.add_argument("--index", dest="index", default="index.toml")
    parser.add_argument("--notebooks", dest="notebooks", nargs="+", default=[])
    parser.add_argument("--include-main", dest="main", action="store_true")

    args = parser.parse_args()
    index = read_index(args.index)

    matrix = []
    for tutorial in index["cookbook"]:
        if tutorial.get("hidden", False):
            # Do not waste CI time on hidden tutorials
            continue

        if tutorial.get("needs_gpu", False):
            # We're not running GPU tutorials on GitHub Actions
            # since we don't have a GPUs there
            continue

        if not tutorial.get("colab", True):
            # This tutorial doesn't have any runnable Python code
            # so there's nothing to test
            continue

        notebook = tutorial["notebook"]
        if args.notebooks and notebook not in args.notebooks:
            # If the user specified a list of notebooks to run, only run those
            # otherwise run all of them
            continue

        matrix.append(
            {
                "notebook": notebook[:-6],
                "dependencies": tutorial.get("dependencies", []),
            }
        )

        if args.main and "haystack_version" not in tutorial:
            # run all notebooks with the latest stable Haystack version
            matrix.append(
                {
                    "notebook": notebook[:-6],
                    "haystack_version": get_latest_stable_haystack_version(),
                    "dependencies": tutorial.get("dependencies", []),
                }
            )

    latest_haystack = get_latest_stable_haystack_version()

    # print(json.dumps(matrix))
    # debugging only -just to run selected cookbooks - uncomment line above and delete below to use dynamically
    # generated matrix
    notebooks = [
        {"notebook": "auto_merging_retriever",
         "haystack_version": latest_haystack,
          "dependencies": []
        },
        {"notebook": "metadata_extraction_with_llm_metadata_extractor",
         "haystack_version": latest_haystack,
         "dependencies": ["sentence-transformers>=4.1.0"]
        }
    ]

    print(json.dumps(notebooks))