#!/bin/bash
# Backend.AI CLI Development Environment Completion Setup
# 
# IMPORTANT: This script must be SOURCED, not executed!
# Usage: source scripts/setup-dev-completion.sh
#        NOT: ./scripts/setup-dev-completion.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up Backend.AI CLI completion for development environment...${NC}"

# Check if we're in the right directory
if [[ ! -f "./backend.ai" ]]; then
    echo -e "${RED}❌ Error: backend.ai script not found in current directory${NC}"
    echo -e "${YELLOW}Please run this from the Backend.AI repository root directory:${NC}"
    echo -e "${YELLOW}  cd /path/to/backend.ai && source scripts/setup-dev-completion.sh${NC}"
    return 1 2>/dev/null || exit 1
fi

# Get absolute path
BACKEND_AI_PATH="$(pwd)/backend.ai"
echo -e "${GREEN}✅ Found backend.ai at: $BACKEND_AI_PATH${NC}"

# Check current shell by detecting shell-specific environment variables
if [[ -n "$BASH_VERSION" ]]; then
    SHELL_TYPE="bash"
elif [[ -n "$ZSH_VERSION" ]]; then
    SHELL_TYPE="zsh"
elif [[ -n "$FISH_VERSION" ]]; then
    SHELL_TYPE="fish"
else
    echo -e "${RED}❌ Error: Unsupported shell detected${NC}"
    echo -e "${YELLOW}This script supports bash, zsh, and fish only.${NC}"
    echo -e "${YELLOW}Current shell: $SHELL${NC}"
    return 1 2>/dev/null || exit 1
fi

echo -e "${GREEN}✅ Detected shell: $SHELL_TYPE${NC}"

# Clean up any existing completions to avoid conflicts
unset -f _backendai_completion 2>/dev/null || true

if [[ "$SHELL_TYPE" == "zsh" ]]; then
    # Reinitialize zsh completion system to avoid conflicts
    unfunction compdef 2>/dev/null || true
    autoload -U compdef
    autoload -U compinit && compinit -D 2>/dev/null
    
    # Ensure Click's completion system is available
    # Try to load basic Click completion infrastructure first
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import click" 2>/dev/null || echo -e "${YELLOW}⚠️  Click not available, completion may be limited${NC}"
    fi
    
    # Generate and load zsh completion using the full path
    # Replace 'backend.ai' with the full path in all places
    COMP_CODE=$(_BACKEND_AI_COMPLETE=zsh_source "$BACKEND_AI_PATH" 2>/dev/null | \
        sed '/^#compdef/d' | \
        sed '/(( ! \$+commands\[backend\.ai\] ))/d' | \
        sed "s|_BACKEND_AI_COMPLETE=zsh_complete backend\.ai|_BACKEND_AI_COMPLETE=zsh_complete \"$BACKEND_AI_PATH\"|g")
    eval "$COMP_CODE" 2>/dev/null

    # Create alias to make 'backend.ai' command available for interactive use
    alias backend.ai="$BACKEND_AI_PATH"

    # Verify completion function was loaded
    if type _backendai_completion >/dev/null 2>&1; then
        # Register completion for both 'backend.ai' (alias) and './backend.ai' (script)
        compdef _backendai_completion backend.ai 2>/dev/null
        compdef _backendai_completion ./backend.ai 2>/dev/null
    else
        echo -e "${RED}❌ Failed to load completion function${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Loaded zsh completion${NC}"
    echo -e "${BLUE}💡 If tab completion doesn't work, try this in a new terminal:${NC}"
    echo "   zsh -f"
    echo "   cd $(pwd)"
    echo "   source scripts/setup-dev-completion.sh"
    
elif [[ "$SHELL_TYPE" == "bash" ]]; then
    # Load bash completion using the full path
    # Replace 'backend.ai' with the full path in all places
    COMP_CODE=$(_BACKEND_AI_COMPLETE=bash_source "$BACKEND_AI_PATH" 2>/dev/null | \
        sed "s|_BACKEND_AI_COMPLETE=bash_complete backend\.ai|_BACKEND_AI_COMPLETE=bash_complete \"$BACKEND_AI_PATH\"|g")
    eval "$COMP_CODE"

    # Create alias to make 'backend.ai' command available for interactive use
    alias backend.ai="$BACKEND_AI_PATH"

    # Verify completion function was loaded and register for both forms
    if type _backendai_completion &>/dev/null; then
        complete -o nosort -F _backendai_completion backend.ai
        complete -o nosort -F _backendai_completion ./backend.ai
        echo -e "${GREEN}✅ Loaded bash completion${NC}"
    else
        echo -e "${RED}❌ Failed to load completion function${NC}"
        return 1
    fi
    
elif [[ "$SHELL_TYPE" == "fish" ]]; then
    echo -e "${YELLOW}🐟 Fish shell detected. Please use the fish-specific script:${NC}"
    echo -e "${BLUE}    source scripts/setup-dev-completion.fish${NC}"
    echo ""
    return 0 2>/dev/null || exit 0
fi

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Usage:${NC}"
echo "  ./backend.ai <tab>            # Show all available commands"
echo "  ./backend.ai session <tab>    # Session management commands"
echo "  ./backend.ai admin <tab>      # Admin commands" 
echo "  ./backend.ai mgr <tab>        # Manager commands"
echo "  ./backend.ai --<tab>          # Global options"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "• This setup is temporary and only applies to the current shell session"
echo "• Run this script again if you start a new terminal session"
echo "• For permanent setup, add the following to your shell config file:"
echo ""
if [[ "$SHELL_TYPE" == "zsh" ]]; then
    echo "  echo 'alias bai-dev=\"cd $(pwd) && source scripts/setup-dev-completion.sh\"' >> ~/.zshrc"
elif [[ "$SHELL_TYPE" == "fish" ]]; then
    echo "  echo 'alias bai-dev=\"cd $(pwd); and source scripts/setup-dev-completion.sh\"' >> ~/.config/fish/config.fish"
else
    echo "  echo 'alias bai-dev=\"cd $(pwd) && source scripts/setup-dev-completion.sh\"' >> ~/.bashrc"
fi
echo ""
echo -e "${BLUE}🔗 Then use: ${NC}${YELLOW}bai-dev${NC} ${BLUE}to quickly activate Backend.AI development environment${NC}"