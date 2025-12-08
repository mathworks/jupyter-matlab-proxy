#!/bin/bash
# Copyright 2025 The MathWorks, Inc.
# Pre-commit hook to replace MathWorks NPM registry URLs with public NPM registry

# Find all package.json, .npmrc, and other relevant files
echo "Executing pre-commit hook: sanitize-npm-registry"
FILES=$( git diff --cached --name-only --diff-filter=ACM | grep -E '(.*.json)')

if [ -z "$FILES" ]; then
    exit 0
fi

# Replace the MathWorks NPM registry URL with the public NPM registry
for FILE in $FILES; do
    # Skip if file doesn't exist (it may have been deleted)
    [ -f "$FILE" ] || continue

    echo "Sanitizing NPM registry URL in $FILE"

    # Replace the URL in the file
    sed -i.bak 's|https://.*/artifactory/api/npm/npm-repos/|https://registry.npmjs.org/|g' "$FILE"

    # Remove backup file
    rm -f "${FILE}.bak"

    # Stage the modified file
    git add "$FILE"

    echo "Sanitization complete for $FILE"
done

exit 0
