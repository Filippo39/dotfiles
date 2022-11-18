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
    currentBranch = git.branch("--show-current")
    if currentBranch != DEVELOP:
        print(f"You must be on {DEVELOP} branch, but you are on {currentBranch}")
        return False
    # TODO:Uncomment
    # if (repo.is_dirty(untracked_files=True)):
    #     print("Your repo is dirty, please commit or stash your changes")
    #     return True
    logging.info(currentBranch)
    logging.info(repo.is_dirty())
    return True
        
# Check for json libary
def update_version_and_changelog() -> None:
    # with open("android/gradle.properties", "r+") as file:
    #     lines = file.readlines()
    #     file.seek(0)
    #     file.read(0)
    #     for line in lines:
    #         file.write(re.sub(r'^versionName=.*', f'versionName={version}', line))

    with open("package.json", "r+") as packageJsonFile:
        data = json.load(packageJsonFile)
        data["version"] = version
        packageJsonFile.seek(0)
        json.dump(data, packageJsonFile, indent=2)

    with open("app.json", "r+") as appJsonFile:
        data = json.load(appJsonFile)
        data["expo"]["version"] = version
        appJsonFile.seek(0)
        json.dump(data, appJsonFile, indent=2)
    
'''
    Create a new release branch with the given version, commit new changes,
    tag the commit and push the branch and the tag
'''
def commit_and_push_release_branch() -> None:
    git.checkout("HEAD", b=f"release/{version}")
    git.add(".")
    git.commit("-m", "Update version")
    git.push("origin", f"release/{version}")
    git.tag(version)
    git.push("origin", version)

'''
    Open merge request from release branch into master and ask user for confirmation
'''
# TODO: pensare ad un restore in caso di rifuto
# TODO: cosi non viene aperta alcuna MR
def merge_release_branch_into_master() -> None:
    merge = input(f"Do you want to merge release/{version} branch into {MASTER}? [y/n] ")
    if merge.lower() in ("y", "yes"):
        git.checkout(MASTER)
        git.merge(f"release/{version}")
        git.push("origin", MASTER)
        git.push("origin", "--delete", f"release/{version}")
        git.branch("-D", f"release/{version}")
        git.checkout(DEVELOP)
        git.merge(MASTER)
        git.push("origin", DEVELOP)
   

# TODO:
#echo '  -> updating iOS project'
#(cd ios && xcrun agvtool new-marketing-version ${NEW_VERSION}) > /dev/null


def main() -> int:
    
    # TODO: uncomment
    # if not check_current_branch_status():
    #     return 1

    # TODO: manca l'update del changelog
    update_version_and_changelog()

    commit_and_push_release_branch()

    merge_release_branch_into_master()

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)6s | %(message)s')
    
    parser = argparse.ArgumentParser(description="Segway Geofences creator")
    parser.add_argument("-v", "--version", help="Release version", required=True, type=str)

    args = parser.parse_args()
    version = args.version
    
    raise exit(main())