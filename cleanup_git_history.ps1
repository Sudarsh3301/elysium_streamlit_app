# Git History Cleanup Script (PowerShell)
# Removes GROQ_MIGRATION_SUMMARY.md from entire git history
# 
# ⚠️ WARNING: This rewrites git history!
# - Coordinate with your team before running
# - All team members will need to re-clone or reset their repos
# - This is a destructive operation - make a backup first!

$ErrorActionPreference = "Stop"

Write-Host "🔐 Git History Cleanup for Leaked API Key" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  WARNING: This will rewrite git history!" -ForegroundColor Yellow
Write-Host "This script will:"
Write-Host "  1. Remove GROQ_MIGRATION_SUMMARY.md from ALL commits"
Write-Host "  2. Require force-push to remote"
Write-Host "  3. Require team members to re-clone or reset"
Write-Host ""

$confirm = Read-Host "Are you sure you want to continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "❌ Aborted by user" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Pre-flight checks..." -ForegroundColor Cyan

# Check if git-filter-repo is installed
try {
    $null = git filter-repo --version 2>&1
} catch {
    Write-Host "❌ git-filter-repo not found" -ForegroundColor Red
    Write-Host "Installing git-filter-repo..." -ForegroundColor Yellow
    pip install git-filter-repo
}

# Check if we're in a git repository
try {
    $null = git rev-parse --git-dir 2>&1
} catch {
    Write-Host "❌ Not in a git repository" -ForegroundColor Red
    exit 1
}

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "❌ You have uncommitted changes" -ForegroundColor Red
    Write-Host "Please commit or stash your changes first" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Pre-flight checks passed" -ForegroundColor Green
Write-Host ""

# Create a backup branch
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupBranch = "backup-before-cleanup-$timestamp"
Write-Host "📦 Creating backup branch: $backupBranch" -ForegroundColor Cyan
git branch $backupBranch
Write-Host "✅ Backup created" -ForegroundColor Green
Write-Host ""

# Remove the file from history
Write-Host "🗑️  Removing GROQ_MIGRATION_SUMMARY.md from git history..." -ForegroundColor Cyan
git filter-repo --path elysium_streamlit_app/GROQ_MIGRATION_SUMMARY.md --invert-paths --force

Write-Host "✅ File removed from history" -ForegroundColor Green
Write-Host ""

# Show summary
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  - Backup branch created: $backupBranch"
Write-Host "  - File removed from all commits"
Write-Host "  - Local history rewritten"
Write-Host ""

Write-Host "🚀 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Verify the changes: git log --all --oneline"
Write-Host "  2. Force push to remote: git push origin --force --all"
Write-Host "  3. Notify team members to re-clone or reset their repos"
Write-Host "  4. Verify on GitHub: Settings → Security → Secret scanning"
Write-Host "  5. Rotate the compromised API key in Groq Console"
Write-Host ""

Write-Host "⚠️  To force push, run:" -ForegroundColor Yellow
Write-Host "     git push origin --force --all"
Write-Host ""

Write-Host "✅ Cleanup complete!" -ForegroundColor Green

