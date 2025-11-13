#!/usr/bin/env bash

# The following script prints differences in the upstream configuration schema between two tags.

# exit when any command fails
set -e

GITHUB_REPO_URL="https://github.com/bmewburn/vscode-intelephense"
CONFIGURATION_FILE_PATH="package.json"
PACKAGE_CONFIGURATION_FILE="LSP-intelephense.sublime-settings"

REPO_DIR=$(echo "${GITHUB_REPO_URL}" | command grep -oE '[^/]*$')
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LSP_REPO_DIR="$SCRIPT_DIR/.."

if [ "$#" -ne 2 ]; then
   echo 'You must provide 2 arguments - two tags between which to check for diffrences in settings.'
   exit 1
fi

function download_asset_by_tag {
   tag=$1

   if [ ! "$tag" ]; then
      exit "No tag provided"
   fi

   pushd "${LSP_REPO_DIR}" > /dev/null || exit

   temp_zip="src-${tag}.zip"
   curl -L "${GITHUB_REPO_URL}/archive/${tag}.zip" -o "${temp_zip}" --silent --show-error
   unzip -q "${temp_zip}"
   rm -f "${temp_zip}" || exit
   mv "${REPO_DIR}-"* "${REPO_DIR}"
}

tag_from=$1
tag_to=$2

download_asset_by_tag "$tag_from"
settings_from=$(jq ".contributes.configuration" "${REPO_DIR}/${CONFIGURATION_FILE_PATH}")
rm -rf "${REPO_DIR}"

download_asset_by_tag "$tag_to"
settings_to=$(jq ".contributes.configuration" "${REPO_DIR}/${CONFIGURATION_FILE_PATH}")
rm -rf "${REPO_DIR}"

# Returns with error code when there are changes.
echo "Following are the [configuration schema](${GITHUB_REPO_URL}/blob/${tag_to}/${CONFIGURATION_FILE_PATH}) changes between tags \`${tag_from}\` and \`${tag_to}\`. Make sure that those are reflected in \`${PACKAGE_CONFIGURATION_FILE}\` and \`sublime-package.json\` files."
changes=$(diff -u <(echo "$settings_from") <(echo "$settings_to") || echo "")
if [ "$changes" = "" ]; then
   echo "No changes"
else
   echo "$changes"
fi
