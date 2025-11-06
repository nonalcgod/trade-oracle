#!/bin/bash

################################################################################
# Trade Oracle - Progressive UI Refinement System
################################################################################
#
# Automated feedback loop for iterative UI improvements
# Uses dual-agent architecture (benai-ui-critic + benai-ui-implementer)
#
# Workflow:
#   1. Capture screenshots with Playwright
#   2. Analyze UI with benai-ui-critic agent → generate feedback
#   3. Implement fixes with benai-ui-implementer agent → make changes
#   4. Git commit iteration
#   5. Repeat until 95%+ compliance or 5 iterations complete
#
# Usage:
#   ./scripts/progressive-ui-refinement.sh [iteration_number]
#
# Example:
#   ./scripts/progressive-ui-refinement.sh 1  # Run iteration 1
#   ./scripts/progressive-ui-refinement.sh    # Auto-detect next iteration
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
SCREENSHOTS_DIR="$FRONTEND_DIR/tests/visual/screenshots"
ANALYSIS_DIR="$FRONTEND_DIR/tests/visual/analysis"
AGENTS_DIR="$PROJECT_ROOT/.claude/agents"

# Iteration tracking
MAX_ITERATIONS=5
TARGET_COMPLIANCE=95

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}ℹ ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if Vite dev server is running
    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
        log_error "Vite dev server not running on http://localhost:3000"
        log_info "Please run: cd frontend && npm run dev"
        exit 1
    fi
    log_success "Vite dev server is running"

    # Check if Playwright is installed
    if [ ! -d "$FRONTEND_DIR/node_modules/@playwright/test" ]; then
        log_error "Playwright not installed"
        log_info "Please run: cd frontend && npm install -D @playwright/test"
        exit 1
    fi
    log_success "Playwright is installed"

    # Check if agent definitions exist
    if [ ! -f "$AGENTS_DIR/benai-ui-critic.md" ]; then
        log_error "benai-ui-critic agent not found at $AGENTS_DIR/benai-ui-critic.md"
        exit 1
    fi
    log_success "benai-ui-critic agent found"

    if [ ! -f "$AGENTS_DIR/benai-ui-implementer.md" ]; then
        log_error "benai-ui-implementer agent not found at $AGENTS_DIR/benai-ui-implementer.md"
        exit 1
    fi
    log_success "benai-ui-implementer agent found"

    # Create analysis directory if it doesn't exist
    mkdir -p "$ANALYSIS_DIR"
    log_success "Analysis directory ready: $ANALYSIS_DIR"
}

detect_iteration_number() {
    # Auto-detect next iteration by counting existing analysis files
    local count=$(ls -1 "$ANALYSIS_DIR"/visual-analysis-iteration-*.md 2>/dev/null | wc -l)
    echo $((count + 1))
}

capture_screenshots() {
    local iteration=$1

    print_header "Step 1: Capturing Screenshots (Iteration $iteration)"

    cd "$FRONTEND_DIR"

    log_info "Running Playwright screenshot capture..."
    npm run test:visual:capture

    if [ $? -eq 0 ]; then
        log_success "Screenshots captured successfully"
        log_info "Screenshots saved to: $SCREENSHOTS_DIR"
        ls -lh "$SCREENSHOTS_DIR"/*.png 2>/dev/null || log_warning "No .png files found"
    else
        log_error "Screenshot capture failed"
        exit 1
    fi

    cd "$PROJECT_ROOT"
}

analyze_ui() {
    local iteration=$1

    print_header "Step 2: UI Analysis (benai-ui-critic)"

    log_info "Launching benai-ui-critic agent..."
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  MANUAL STEP REQUIRED${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "1. Open a NEW terminal or Claude Code session"
    echo "2. Run the following command:"
    echo ""
    echo -e "   ${GREEN}claude${NC}"
    echo ""
    echo "3. In Claude Code, type:"
    echo ""
    echo -e "   ${GREEN}@benai-ui-critic analyze the screenshots in tests/visual/screenshots/dashboard-full-desktop.png${NC}"
    echo -e "   ${GREEN}and create a detailed analysis report. Save it as tests/visual/analysis/visual-analysis-iteration-$iteration.md${NC}"
    echo ""
    echo "4. Wait for the agent to complete the analysis"
    echo "5. The agent will create: $ANALYSIS_DIR/visual-analysis-iteration-$iteration.md"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""

    read -p "Press ENTER when analysis is complete and the file exists..."

    # Verify analysis file was created
    if [ ! -f "$ANALYSIS_DIR/visual-analysis-iteration-$iteration.md" ]; then
        log_error "Analysis file not found: $ANALYSIS_DIR/visual-analysis-iteration-$iteration.md"
        log_info "Please ensure the benai-ui-critic agent saved the file in the correct location"
        exit 1
    fi

    log_success "Analysis report found: $ANALYSIS_DIR/visual-analysis-iteration-$iteration.md"
}

implement_fixes() {
    local iteration=$1

    print_header "Step 3: Implementing Fixes (benai-ui-implementer)"

    log_info "Launching benai-ui-implementer agent..."
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  MANUAL STEP REQUIRED${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "1. In the same Claude Code session (or open a new one)"
    echo "2. Type:"
    echo ""
    echo -e "   ${GREEN}@benai-ui-implementer read the feedback from tests/visual/analysis/visual-analysis-iteration-$iteration.md${NC}"
    echo -e "   ${GREEN}and implement the top 3-5 high-priority fixes. Make targeted, component-level changes only.${NC}"
    echo ""
    echo "3. Wait for the agent to complete the implementation"
    echo "4. Verify changes in your browser at http://localhost:3000"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""

    read -p "Press ENTER when implementation is complete..."

    log_success "Implementation complete"
}

commit_iteration() {
    local iteration=$1

    print_header "Step 4: Git Commit (Iteration $iteration)"

    cd "$PROJECT_ROOT"

    # Check if there are changes to commit
    if git diff --quiet && git diff --cached --quiet; then
        log_warning "No changes to commit"
        return 0
    fi

    log_info "Files changed:"
    git status --short

    echo ""
    read -p "Review the changes above. Commit this iteration? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Creating git commit..."

        # Add all frontend changes
        git add frontend/src/ frontend/tests/visual/screenshots/ frontend/tests/visual/analysis/

        # Create commit with descriptive message
        git commit -m "UI: Iteration $iteration - Progressive refinement (benai feedback)

Implemented high-priority fixes from visual-analysis-iteration-$iteration.md:
- (agent will have listed specific changes)

Analysis report: frontend/tests/visual/analysis/visual-analysis-iteration-$iteration.md
Screenshots: frontend/tests/visual/screenshots/

Co-Authored-By: benai-ui-critic <noreply@anthropic.com>
Co-Authored-By: benai-ui-implementer <noreply@anthropic.com>"

        log_success "Iteration $iteration committed to git"

        # Show commit
        git log -1 --oneline
    else
        log_warning "Skipped git commit"
    fi
}

check_completion() {
    local iteration=$1

    print_header "Step 5: Progress Check"

    log_info "Iteration $iteration complete"

    echo ""
    echo "Next steps:"
    echo ""

    if [ $iteration -lt $MAX_ITERATIONS ]; then
        echo "  Option 1: Run next iteration"
        echo -e "    ${GREEN}./scripts/progressive-ui-refinement.sh $((iteration + 1))${NC}"
        echo ""
        echo "  Option 2: Review changes and stop"
        echo "    - Check browser at http://localhost:3000"
        echo "    - Review analysis: $ANALYSIS_DIR/visual-analysis-iteration-$iteration.md"
        echo ""
    else
        log_warning "Maximum iterations ($MAX_ITERATIONS) reached"
        echo ""
        echo "Review final state:"
        echo "  - Browser: http://localhost:3000"
        echo "  - Analysis reports: $ANALYSIS_DIR/"
        echo "  - Screenshots: $SCREENSHOTS_DIR/"
        echo ""
    fi
}

show_summary() {
    print_header "Progressive UI Refinement Summary"

    local total_analyses=$(ls -1 "$ANALYSIS_DIR"/visual-analysis-iteration-*.md 2>/dev/null | wc -l)

    echo "Iterations completed: $total_analyses"
    echo "Analysis reports: $ANALYSIS_DIR/"
    echo "Screenshots: $SCREENSHOTS_DIR/"
    echo ""

    if [ $total_analyses -gt 0 ]; then
        log_success "UI refinement in progress!"
        echo ""
        echo "View latest analysis:"
        echo -e "  ${GREEN}cat $ANALYSIS_DIR/visual-analysis-iteration-$total_analyses.md${NC}"
    fi
}

################################################################################
# Main Workflow
################################################################################

main() {
    # Parse iteration number (auto-detect if not provided)
    ITERATION=${1:-$(detect_iteration_number)}

    print_header "Trade Oracle - Progressive UI Refinement"
    echo "Iteration: $ITERATION / $MAX_ITERATIONS"
    echo "Target Compliance: $TARGET_COMPLIANCE%"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Run iteration workflow
    capture_screenshots $ITERATION
    analyze_ui $ITERATION
    implement_fixes $ITERATION
    commit_iteration $ITERATION
    check_completion $ITERATION

    # Show summary
    show_summary
}

# Run main workflow
main "$@"
