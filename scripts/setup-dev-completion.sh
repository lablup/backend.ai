#!/bin/bash
# Backend.AI CLI Development Environment Completion Setup
# Usage: source scripts/setup-dev-completion.sh

set -e

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

# Check current shell
if [[ -n "$ZSH_VERSION" ]]; then
    SHELL_TYPE="zsh"
elif [[ -n "$BASH_VERSION" ]]; then
    SHELL_TYPE="bash"
elif [[ -n "$FISH_VERSION" ]]; then
    SHELL_TYPE="fish"
else
    # Fallback: check process name or $0
    case "$(ps -p $$ -o comm= 2>/dev/null || basename "$0")" in
        *fish*)
            SHELL_TYPE="fish"
            ;;
        *zsh*)
            SHELL_TYPE="zsh"
            ;;
        *bash*)
            SHELL_TYPE="bash"
            ;;
        *)
            echo -e "${YELLOW}⚠️  Warning: Shell type detection failed. Assuming bash.${NC}"
            SHELL_TYPE="bash"
            ;;
    esac
fi

echo -e "${GREEN}✅ Detected shell: $SHELL_TYPE${NC}"

# Set up alias (shell-specific)
if [[ "$SHELL_TYPE" == "fish" ]]; then
    # Fish uses different alias syntax in sourced scripts
    alias backend.ai "$BACKEND_AI_PATH"
    echo -e "${GREEN}✅ Created fish alias: backend.ai -> $BACKEND_AI_PATH${NC}"
else
    alias backend.ai="$BACKEND_AI_PATH"
    echo -e "${GREEN}✅ Created alias: backend.ai -> $BACKEND_AI_PATH${NC}"
fi

if [[ "$SHELL_TYPE" == "zsh" ]]; then
    # Initialize zsh completion system
    autoload -U compinit && compinit 2>/dev/null
    
    # Create custom completion function for zsh
    _backendai_dev_completion() {
        local -a completions
        local -a completions_with_descriptions
        local -a response
        
        # Use absolute path for completion
        response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _BACKEND_AI_COMPLETE=zsh_complete "$BACKEND_AI_PATH" 2>/dev/null)}")
        
        for type key descr in ${response}; do
            if [[ "$type" == "plain" ]]; then
                if [[ "$descr" == "_" ]]; then
                    completions+=("$key")
                else
                    completions_with_descriptions+=("$key":"$descr")
                fi
            elif [[ "$type" == "dir" ]]; then
                _path_files -/
                return 0
            elif [[ "$type" == "file" ]]; then
                _path_files -f
                return 0
            fi
        done
        
        if (( ${#completions_with_descriptions[@]} )); then
            _describe -V unsorted completions_with_descriptions -U
        fi
        
        if (( ${#completions[@]} )); then
            compadd -U -V unsorted -a completions
        fi
    }
    
    # Register completion for zsh
    compdef _backendai_dev_completion backend.ai
    echo -e "${GREEN}✅ Registered zsh completion function${NC}"
    
elif [[ "$SHELL_TYPE" == "bash" ]]; then
    # Load bash completion
    eval "$(_BACKEND_AI_COMPLETE=bash_source "$BACKEND_AI_PATH" 2>/dev/null | sed "s|backend\.ai|$BACKEND_AI_PATH|g")"
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
echo "  backend.ai <tab>              # Show all available commands"
echo "  backend.ai session <tab>      # Session management commands"
echo "  backend.ai admin <tab>        # Admin commands" 
echo "  backend.ai mgr <tab>          # Manager commands"
echo "  backend.ai --<tab>            # Global options"
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