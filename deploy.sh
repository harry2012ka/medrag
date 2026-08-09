#!/usr/bin/env bash
set -e

if [ $# -lt 2 ]; then
  echo "Usage: ./deploy.sh <repo-name> <public|private>"
  exit 1
fi

REPO_NAME="$1"
VISIBILITY="$2"

if [[ "$VISIBILITY" != "public" && "$VISIBILITY" != "private" ]]; then
  echo "Error: second argument must be 'public' or 'private'"
  exit 1
fi

if ! command -v gh &> /dev/null; then
  echo "Error: GitHub CLI (gh) is not installed. Install it from https://cli.github.com/ and run 'gh auth login' first."
  exit 1
fi

cd "$(dirname "$0")"

if [ ! -d ".git" ]; then
  echo "Initializing git repository..."
  git init
  git add .
  git commit -m "Initial commit: MedRAG clinical PDF Q&A app"
fi

echo "Creating GitHub repo '$REPO_NAME' ($VISIBILITY)..."
gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push

REPO_URL=$(gh repo view "$REPO_NAME" --json url -q .url)
echo ""
echo "Deployed! Repo URL: $REPO_URL"
