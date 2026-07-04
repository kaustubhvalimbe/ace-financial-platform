#!/bin/bash
echo ""
echo "========================================"
echo "  Ace Financial Services - Git Deploy"
echo "========================================"
echo ""

cd "/c/Kv/Ace/AIS/Claude Development/AFS Website/Ver 61"

echo "Checking for any changes made directly on GitHub..."
git pull
if [ $? -ne 0 ]; then
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

echo ""
echo "Staging changes..."
git add .

echo ""
git status --short

echo ""
read -p "Enter commit message (or press Enter for 'Update'): " msg
if [ -z "$msg" ]; then msg="Update"; fi

echo ""
echo "Committing: $msg"
git commit -m "$msg"

echo ""
echo "Pushing to GitHub..."
git push
if [ $? -ne 0 ]; then
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
echo "========================================"
echo ""
read -p "Press Enter to close..."
