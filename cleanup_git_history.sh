#!/bin/bash
# Git History Cleanup Script
# Removes GROQ_MIGRATION_SUMMARY.md from entire git history
# 
# ⚠️ WARNING: This rewrites git history!
# - Coordinate with your team before running
# - All team members will need to re-clone or reset their repos
# - This is a destructive operation - make a backup first!

set -e  # Exit on error

echo "🔐 Git History Cleanup for Leaked API Key"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "This script will:"
echo "  1. Remove GROQ_MIGRATION_SUMMARY.md from ALL commits"
echo "  2. Require force-push to remote"
echo "  3. Require team members to re-clone or reset"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted by user"
    exit 1
fi

echo ""
echo "📋 Pre-flight checks..."

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo "❌ git-filter-repo not found"
    echo "Installing git-filter-repo..."
    pip install git-filter-repo
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ You have uncommitted changes"
    echo "Please commit or stash your changes first"
    exit 1
fi

echo "✅ Pre-flight checks passed"
echo ""

# Create a backup branch
BACKUP_BRANCH="backup-before-cleanup-$(date +%Y%m%d-%H%M%S)"
echo "📦 Creating backup branch: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"
echo "✅ Backup created"
echo ""

# Remove the file from history
echo "🗑️  Removing GROQ_MIGRATION_SUMMARY.md from git history..."
git filter-repo --path elysium_streamlit_app/GROQ_MIGRATION_SUMMARY.md --invert-paths --force

echo "✅ File removed from history"
echo ""

# Show summary
echo "📊 Summary:"
echo "  - Backup branch created: $BACKUP_BRANCH"
echo "  - File removed from all commits"
echo "  - Local history rewritten"
echo ""

echo "🚀 Next steps:"
echo "  1. Verify the changes: git log --all --oneline"
echo "  2. Force push to remote: git push origin --force --all"
echo "  3. Notify team members to re-clone or reset their repos"
echo "  4. Verify on GitHub: Settings → Security → Secret scanning"
echo "  5. Rotate the compromised API key in Groq Console"
echo ""

echo "⚠️  To force push, run:"
echo "     git push origin --force --all"
echo ""

echo "✅ Cleanup complete!"

