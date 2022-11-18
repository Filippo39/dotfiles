#!/usr/bin/env python
from sys import exit
import argparse
import logging
from git import Repo, Git
import re
import json

MASTER = "fakeMaster" # FIXME: master
DEVELOP = "fakeDevelop" # FIXME: develop

repo = Repo('.')
git = Git()
version = ''

'''
    Check if the current branch is the develop branch and if there are no changes
'''
def check_current_branch_status() -> bool:
    current_branch = git.branch("--show-current")
    if current_branch != DEVELOP:
        logging.error(f"You must be on {DEVELOP} branch, but you are on {current_branch}")
        exit(1)
    if (repo.is_dirty(untracked_files=True)):
        logging.error("Your repo is dirty, please commit or stash your changes")
        exit(1)
        
def update_version_and_changelog() -> None:
    with open("android/gradle.properties", "r+") as gradle_properties_file:
        file_content = gradle_properties_file.read()
        gradle_properties_file.seek(0)
        gradle_properties_file.write(re.sub(r'versionName=.*', f'versionName={version}', file_content))
        gradle_properties_file.truncate()

    with open("ios/BIT/Info.plist", "r+") as info_plist_file:
        file_content = info_plist_file.read()
        info_plist_file.seek(0)
        key = "<key>CFBundleShortVersionString</key>"
        info_plist_file.write(re.sub(r'{}\n\t<string>.*</string>'.format(key), f'{key}\n\t<string>{version}</string>', file_content))
        info_plist_file.truncate()

    with open("package.json", "r+") as package_json_file:
        data = json.load(package_json_file)
        data["version"] = version
        package_json_file.seek(0)
        json.dump(data, package_json_file, indent=2)

    with open("app.json", "r+") as app_json_file:
        data = json.load(app_json_file)
        data["expo"]["version"] = version
        app_json_file.seek(0)
        json.dump(data, app_json_file, indent=2)

    # TODO: update changelog
    
'''
    Create a new release branch with the given version, commit new changes,
    tag the commit and push the branch and the tag
'''
def commit_and_push_release_branch() -> None:

    if not repo.is_dirty(untracked_files=True):
        logging.warning("Your repo is clean, nothing to commit")
        exit(1)

    git.checkout("-b", f"release/{version}")
    git.add(".")
    git.commit("-m", "Update version")
    git.push("origin", f"release/{version}")
    git.tag(version)
    git.push("origin", version) # Push remote tag

def merge_release_branch_into_master() -> None:
    merge = input(f"Do you want to merge release/{version} branch into {MASTER}? [y/n] ")
    if merge.lower() in ("y", "yes"):
        git.checkout(MASTER)
        git.merge(f"release/{version}", "--no-ff")
        git.push("origin", MASTER)
        git.push("origin", "--delete", f"release/{version}")
    else:
        print("Merge aborted, rollbacking...")
        git.push("origin", "--delete", version) # Delete remote tag
        git.tag("-d", version)
        git.push("origin", "--delete", f"release/{version}")
        git.branch("-D", f"release/{version}")
        git.checkout(DEVELOP)
        exit(1)

def merge_master_into_develop() -> None:
    git.checkout(DEVELOP)
    git.merge(MASTER, "--no-ff")
    git.push("origin", DEVELOP)


def main() -> int:

    logging.info("Starting release flow")
    
    check_current_branch_status()
    update_version_and_changelog()
    commit_and_push_release_branch()
    merge_release_branch_into_master()
    merge_master_into_develop()

    logging.info("Release flow completed")
    exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)6s | %(message)s')
    
    parser = argparse.ArgumentParser(description="Segway Geofences creator")
    parser.add_argument("-v", "--version", help="Release version", required=True, type=str)

    args = parser.parse_args()
    version = args.version
    
    main()