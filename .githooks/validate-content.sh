#!/bin/bash
# Shared validation script for all git hooks and CI/CD

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Build prohibited terms pattern dynamically to avoid false positives
# This constructs the pattern without containing the actual terms
P1=$(echo "Y2xhdWRlfGFudGhyb3BpY3xhaSBnZW5lcmF0ZWR8Z2VuZXJhdGVkIHdpdGh8" | base64 -d)
P2=$(echo "Y28tYXV0aG9yZWQtYnk6IGNsYXVkZXxvcGVuYWl8Z3B0fGNvcGlsb3R8" | base64 -d)
P3=$(echo "Y2hhdGdwdHxiYXJkfGdlbWluaXxsbG18bGFuZ3VhZ2UgbW9kZWw=" | base64 -d)
PROHIBITED_TERMS="${P1}${P2}${P3}"

# Build suspicious patterns
S1=$(echo "Z2VuZXJhdGVkIGJ5fGNyZWF0ZWQgd2l0aHxwb3dlcmVkIGJ5fA==" | base64 -d)
S2=$(echo "YXNzaXN0ZWQgYnl8d3JpdHRlbiBieSBhaXxhaS13cml0dGVufGJvdC1nZW5lcmF0ZWQ=" | base64 -d)
SUSPICIOUS_PATTERNS="${S1}${S2}"

# Function to check content for prohibited terms
check_content() {
    local content="$1"
    local context="$2"
    local found_violations=false

    # Check for prohibited terms
    if echo "$content" | grep -iE "$PROHIBITED_TERMS" > /dev/null 2>&1; then
        echo "${RED}Error: $context contains prohibited terms:${NC}"
        echo "$content" | grep -iE "$PROHIBITED_TERMS" --color=always | head -10
        found_violations=true
    fi

    # Check for suspicious patterns
    if echo "$content" | grep -iE "$SUSPICIOUS_PATTERNS" > /dev/null 2>&1; then
        echo "${YELLOW}Warning: $context contains suspicious patterns:${NC}"
        echo "$content" | grep -iE "$SUSPICIOUS_PATTERNS" --color=always | head -5
    fi

    # Check for suspicious emojis
    if echo "$content" | grep -E "🤖|🤯|🧠|🔮|🎯|⚡" > /dev/null 2>&1; then
        echo "${YELLOW}Warning: $context contains suspicious emojis${NC}"
    fi

    if $found_violations; then
        return 1
    fi
    return 0
}

# Function to validate a file
validate_file() {
    local file="$1"
    local file_content=""

    # Skip binary files
    if file --mime "$file" 2>/dev/null | grep -q "binary"; then
        return 0
    fi

    # Read file content
    if [ -f "$file" ]; then
        file_content=$(cat "$file" 2>/dev/null)
    else
        # For staged files in git
        file_content=$(git show ":$file" 2>/dev/null)
    fi

    if [ -z "$file_content" ]; then
        return 0
    fi

    check_content "$file_content" "File '$file'"
    return $?
}

# Function to validate all files in a directory
validate_directory() {
    local dir="${1:-.}"
    local found_violations=false

    echo "Validating files in $dir..."

    # Find all text files
    find "$dir" -type f \
        -not -path "*/\.git/*" \
        -not -path "*/node_modules/*" \
        -not -path "*/__pycache__/*" \
        -not -path "*/venv/*" \
        -not -path "*/\.venv/*" \
        -not -path "*/dist/*" \
        -not -path "*/build/*" \
        | while read -r file; do
        if ! validate_file "$file"; then
            found_violations=true
        fi
    done

    if $found_violations; then
        return 1
    fi
    return 0
}

# Function to validate PR description
validate_pr_description() {
    local pr_body="$1"

    echo "Validating PR description..."
    check_content "$pr_body" "PR description"
    return $?
}

# Main execution based on arguments
case "$1" in
    "file")
        validate_file "$2"
        ;;
    "directory")
        validate_directory "$2"
        ;;
    "pr")
        validate_pr_description "$2"
        ;;
    "content")
        check_content "$2" "$3"
        ;;
    *)
        echo "Usage: $0 {file|directory|pr|content} [argument]"
        exit 1
        ;;
esac