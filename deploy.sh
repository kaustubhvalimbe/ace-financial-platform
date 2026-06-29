#!/bin/bash
echo ""
echo "========================================"
echo "  Ace Financial Services - Git Deploy"
echo "========================================"
echo ""

cd "/c/Kv/Ace/AIS/Claude Development/AFS Website/Ver 61"

git add .

echo ""
read -p "Enter commit message (or press Enter for 'Update'): " msg
if [ -z "$msg" ]; then msg="Update"; fi

echo ""
echo "Committing: $msg"
git commit -m "$msg"

echo ""
echo "Pushing to GitHub..."
git push --force

echo ""
echo "========================================"
echo "  DONE! Site will update in 1-2 mins"
echo "========================================"
echo ""
