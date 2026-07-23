#!/bin/bash
# Keep this file INSIDE the website folder (e.g. Ver 61).
# It deploys whichever folder it is sitting in - so when you move to
# Ver 62, just copy this file across. Nothing to edit.

echo ""
echo "========================================"
echo "  Ace Financial Services - Git Deploy"
echo "========================================"
echo ""

# --- Work in this script's own folder ------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)" || {
  echo "  STOP: Could not work out this script's folder."
  echo ""
  read -p "Press Enter to exit..."
  exit 1
}
cd "$SCRIPT_DIR" || {
  echo "  STOP: Could not open $SCRIPT_DIR"
  echo ""
  read -p "Press Enter to exit..."
  exit 1
}

# --- Make sure this folder really is the git repo ------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "========================================"
  echo "  STOP: This folder is not a git repo."
  echo ""
  echo "  $(pwd)"
  echo ""
  echo "  Move this script into your website"
  echo "  folder (the one with index.html in it)."
  echo "========================================"
  echo ""
  read -p "Press Enter to exit..."
  exit 1
fi

echo "Deploying from: $(pwd)"
echo ""

# --- Pull first, so we never overwrite changes made on GitHub ------------
echo "Checking for any changes made directly on GitHub..."
if ! git pull; then
  echo ""
  echo "========================================"
  echo "  STOP: git pull ran into a problem."
  echo "  This usually means a file was changed"
  echo "  both on GitHub and on this computer."
  echo "  Do NOT continue until this is resolved -"
  echo "  ask Claude for help before proceeding."
  echo "========================================"
  echo ""
  read -p "Press Enter to exit..."
  exit 1
fi

# --- Stage everything ----------------------------------------------------
echo ""
echo "Staging changes..."
git add .

# --- If nothing changed, stop here quietly -------------------------------
if git diff --cached --quiet; then
  echo ""
  echo "========================================"
  echo "  Nothing to deploy - no files changed."
  echo "  Your site is already up to date."
  echo "========================================"
  echo ""
  read -p "Press Enter to close..."
  exit 0
fi

echo ""
echo "These files will be published:"
git status --short
echo ""

# --- Gentle note if this script itself is being published ----------------
if git ls-files --error-unmatch "$(basename "$0")" >/dev/null 2>&1; then
  echo "  Note: $(basename "$0") is tracked by git, so it goes"
  echo "  live on your site. Harmless, but to stop that, add a"
  echo "  file called .gitignore containing: $(basename "$0")"
  echo ""
fi

# --- Commit --------------------------------------------------------------
read -p "Enter commit message (or press Enter for 'Update'): " msg
if [ -z "$msg" ]; then msg="Update"; fi

echo ""
echo "Committing: $msg"
if ! git commit -m "$msg"; then
  echo ""
  echo "========================================"
  echo "  STOP: The commit failed."
  echo "  Nothing has been pushed. Ask Claude."
  echo "========================================"
  echo ""
  read -p "Press Enter to exit..."
  exit 1
fi

# --- Push ----------------------------------------------------------------
echo ""
echo "Pushing to GitHub..."
if ! git push; then
  echo ""
  echo "========================================"
  echo "  PUSH FAILED."
  echo "  GitHub has changes this computer doesn't"
  echo "  have. Run this script again to pull them"
  echo "  in, or ask Claude for help if unsure."
  echo "========================================"
  echo ""
  read -p "Press Enter to exit..."
  exit 1
fi

echo ""
echo "========================================"
echo "  DONE! Site will update in 1-2 mins"
echo ""
echo "  Then check in a private/incognito window:"
echo "  https://acefinservices.com"
echo "========================================"
echo ""
read -p "Press Enter to close..."
