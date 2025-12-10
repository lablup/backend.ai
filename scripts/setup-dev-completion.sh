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

# Check current shell using $SHELL environment variable
SHELL_TYPE=$(basename "$SHELL")

echo -e "${GREEN}✅ Detected shell: $SHELL_TYPE${NC}"

# Clean up any existing completions to avoid conflicts
unset -f _backendai_completion 2>/dev/null || true

if [[ "$SHELL_TYPE" == "zsh" ]]; then
    # Reinitialize zsh completion system to avoid conflicts
    unfunction compdef 2>/dev/null || true
    autoload -U compdef
    autoload -U compinit && compinit -D 2>/dev/null
    
    # Generate and load zsh completion
    COMP_CODE=$(_BACKEND_AI_COMPLETE=zsh_source "$BACKEND_AI_PATH" 2>/dev/null | sed '/^#compdef/d')
    eval "$COMP_CODE" 2>/dev/null
    
    # Register completion manually in _comps array to avoid compdef issues
    if type _backendai_completion >/dev/null 2>&1; then
        _comps[./backend.ai]=_backendai_completion 2>/dev/null || echo -e "${YELLOW}⚠️  Direct registration failed, but completion function is loaded${NC}"
    else
        echo -e "${RED}❌ Failed to load completion function${NC}"
        return 1
    fi
    echo -e "${GREEN}✅ Loaded zsh completion${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Note: Your zsh completion system has conflicts.${NC}"
    echo -e "${BLUE}💡 If tab completion doesn't work, try this in a new terminal:${NC}"
    echo "   zsh -f"
    echo "   cd $(pwd)"
    echo "   source scripts/setup-dev-completion.sh"
    
elif [[ "$SHELL_TYPE" == "bash" ]]; then
    # Load bash completion
    eval $(_BACKEND_AI_COMPLETE=bash_source "$BACKEND_AI_PATH" 2>/dev/null | sed "s|backend\\.ai|$BACKEND_AI_PATH|g")
    echo -e "${GREEN}✅ Loaded bash completion${NC}"
    
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