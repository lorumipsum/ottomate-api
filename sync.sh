#!/bin/bash

# OttoMate Sync Helper Script
# This script helps maintain sync between local development and GitHub repository

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[SYNC]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository. Please run this script from the ottomate-api directory."
    exit 1
fi

# Function to sync from GitHub (pull)
sync_from_github() {
    print_status "Pulling latest changes from GitHub..."
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "You have uncommitted changes. Please commit or stash them first."
        git status --short
        exit 1
    fi
    
    git pull origin main
    print_status "Successfully synced from GitHub!"
}

# Function to sync to GitHub (push)
sync_to_github() {
    print_status "Syncing changes to GitHub..."
    
    # Check if there are changes to commit
    if [ -z "$(git status --porcelain)" ]; then
        print_status "No changes to commit."
        return 0
    fi
    
    # Show what will be committed
    print_status "Changes to be committed:"
    git status --short
    
    # Add all changes
    git add .
    
    # Get commit message
    if [ -z "$1" ]; then
        echo -n "Enter commit message: "
        read commit_message
    else
        commit_message="$1"
    fi
    
    # Commit and push
    git commit -m "$commit_message"
    git push origin main
    
    print_status "Successfully synced to GitHub!"
}

# Function to show status
show_status() {
    print_status "Repository status:"
    echo
    echo "Branch: $(git branch --show-current)"
    echo "Remote: $(git remote get-url origin)"
    echo
    
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Uncommitted changes:"
        git status --short
    else
        print_status "Working directory clean"
    fi
    
    echo
    print_status "Recent commits:"
    git log --oneline -5
}

# Main script logic
case "$1" in
    "pull"|"from")
        sync_from_github
        ;;
    "push"|"to")
        sync_to_github "$2"
        ;;
    "status"|"")
        show_status
        ;;
    "help"|"-h"|"--help")
        echo "OttoMate Sync Helper"
        echo
        echo "Usage: $0 [command] [message]"
        echo
        echo "Commands:"
        echo "  pull, from     Pull latest changes from GitHub"
        echo "  push, to       Push local changes to GitHub"
        echo "  status         Show repository status (default)"
        echo "  help           Show this help message"
        echo
        echo "Examples:"
        echo "  $0 pull                    # Pull latest changes"
        echo "  $0 push \"Fix lint rules\"   # Push with commit message"
        echo "  $0 status                  # Show current status"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac
