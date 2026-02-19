#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# setconfigurationproperties_AS3.py
# February 2026
#
# Minimal variant of setconfigurationproperties.py that preserves original behavior
# (keys, ignore lists, etc.) but adds support for reading target JSON from STDIN
# using -f - or implicit piped input.
#
# Change History
# 25NOV2025 Initial version
# February 2026 (AS edits: ability to pipe JSON code into setcondfigurationproperties in addition to a whole file)


import argparse
import json
import logging
import os
import sys
import tempfile

from deepdiff import DeepDiff
from sharedfunctions import (
    getinputjson,
    getconfigurationproperty,
    updateconfigurationproperty,
    getclicommand
)

# get cli location from properties, check that cli is there if not ERROR and stop
clicommand = getclicommand()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Import JSON files that update Viya configuration. Read JSON from a file (-f) "
            "or from STDIN (pipe) using -f - or by piping without -f."
        )
    )
    parser.add_argument("-o", "--output", choices=["csv", "json", "simple", "simplejson"], default="json")
    parser.add_argument("-f", "--file", help="The JSON configuration definition to import")
    parser.add_argument("--ignore-items-keys", nargs="*", default=["id", "links"])
    parser.add_argument("--ignore-metadata-keys", nargs="*", default=["createdBy", "creationTimeStamp", "modifiedBy", "modifiedTimeStamp"])
    parser.add_argument("--include-keys", nargs="*", default=["version", "accept", "name", "items"])  
    parser.add_argument("--dryrun", action="store_true", help="Simulate the operation without applying changes")
    return parser.parse_args()


# Extracts the config definition from a json file.
# Example sas.identities.providers.ldap.user

def extract_config_definition(data):
    media_type = data["items"][0]["metadata"]["mediaType"]
    return media_type.split(".config.")[-1].split("+")[0]


# Filters json by include top level keys, ignoring keys in items, and ignoring keys under metadata.

def filter_json(data, include_keys, ignore_items_keys=None, ignore_metadata_keys=None):
    result = {}
    for key in include_keys:
        if key not in data:
            continue
        if key == "items":
            result["items"] = [
                {
                    k: (
                        {mk: mv for mk, mv in v.items() if mk not in (ignore_metadata_keys or [])}
                        if k == "metadata" and isinstance(v, dict)
                        else v
                    )
                    for k, v in item.items() if k not in (ignore_items_keys or [])
                }
                for item in data["items"]
            ]
        else:
            result[key] = data[key]
    return result


# validate_changes
# Function to compare current to target json and validate the changes before processing

def validate_changes(diff):
    unexpected = [k for k in diff if k != "values_changed"]

    if unexpected:
        print("❌ Disallowed changes detected:")
        for key in unexpected:
            print(f" - {key}: {diff[key]}")
        raise SystemExit("Dry run failed: Only value changes are allowed.")

    for path, change in diff.get("values_changed", {}).items():
        if "metadata']['mediaType" in path:
            print("❌ mediaType has changed!")
            print(f"Old: {change['old_value']}")
            print(f"New: {change['new_value']}")
            raise SystemExit("❌ mediaType' cannot be modified. Please update the target JSON file with the correct mediaType before retrying.")

        print(f"{path}: {change['old_value']} → {change['new_value']}")

        if "root['version']" in path:
            old_version = change['old_value']
            new_version = change['new_value']
            if new_version <= old_version:
                raise SystemExit(
                    f"❌: Attempted to set version to {new_version}, but current version is {old_version}. The new version must be greater."
                )


def apply_changes(filtered_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "filtered_target.json")
        # write the JSON file
        with open(filepath, "w") as f:
            json.dump(filtered_data, f, indent=4)

        # build the command string
        command = clicommand + ' configuration configurations update --file ' + filepath

        # now open the tmp file you just wrote and print its contents
        with open(filepath, "r") as f:
            print(f.read())

        # run the update
        updateconfigurationproperty(command)


def _read_target_from_stdin():
    """
    Read all of STDIN and parse JSON.
    """
    try:
        text = sys.stdin.read()
        if not text.strip():
            return None
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"❌ Failed to parse JSON from STDIN: {e}")


def _load_target_data(args):
    """
    Load target JSON from:
      - file path (if -f provided and not '-'),
      - STDIN (if -f == '-' or if no file provided and STDIN is not a TTY).
    """
    # Case 1: explicit file path (preserve original behavior when a real path is provided)
    if args.file and args.file != "-":
        if not os.path.isfile(args.file):
            raise SystemExit(f"❌ File not found: {args.file}")
        return getinputjson(args.file)

    # Case 2: explicit '-' or implicit STDIN
    stdin_has_data = not sys.stdin.isatty()
    if args.file == "-" or (args.file is None and stdin_has_data):
        data = _read_target_from_stdin()
        if data is None:
            raise SystemExit("❌ No JSON detected on STDIN. Pipe JSON or provide -f <file>.")
        return data

    # Nothing provided
    raise SystemExit("❌ No input provided. Use -f <file>, -f -, or pipe JSON into STDIN.")


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    # IMPORTANT: Do not pre-check args.file here; _load_target_data handles '-' and STDIN cases correctly.
    target_data = _load_target_data(args)

    config_definition = extract_config_definition(target_data)
    logging.info(f"config definition = {config_definition}")

    current_data = getconfigurationproperty(config_definition)

    # Filter using ORIGINAL defaults (include version, accept, name, items; ignore id & links; ignore metadata audit keys)
    filtered_target = filter_json(target_data, args.include_keys, args.ignore_items_keys, args.ignore_metadata_keys)
    filtered_current = filter_json(current_data, args.include_keys, args.ignore_items_keys, args.ignore_metadata_keys)

    diff = DeepDiff(filtered_current, filtered_target, ignore_order=True)

    if not diff:
        logging.info("✅ No changes detected.")
    else:
        diff = diff.to_dict()  # convert only when differences exist
        validate_changes(diff)

        if args.dryrun:
            logging.info("✅ Dryrun detected, no changes will be applied")
        else:
            apply_changes(filtered_target)


if __name__ == "__main__":
    main()
