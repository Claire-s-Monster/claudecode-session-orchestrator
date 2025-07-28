#\!/bin/bash
# ClaudeCode Session Orchestrator - Framework Compliance Checker
# Universal Development Framework Compliance Baseline

set -euo pipefail

# ANSI color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global compliance tracking
VIOLATIONS=0
WARNINGS=0
START_TIME=$(date +%s)

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPLIANCE_LOG_DIR="${PROJECT_ROOT}/logs/compliance"
COMPLIANCE_REPORT="${COMPLIANCE_LOG_DIR}/compliance-report-$(date +%Y%m%d-%H%M%S).json"

# Ensure compliance log directory exists
mkdir -p "${COMPLIANCE_LOG_DIR}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅ PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠️ WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_critical() {
    echo -e "${RED}[❌ CRITICAL]${NC} $1"
    VIOLATIONS=$((VIOLATIONS + 1))
}

log_section() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

# Initialize compliance report
init_compliance_report() {
    cat > "${COMPLIANCE_REPORT}" << 'JSON_EOF'
{
  "compliance_check": {
    "timestamp": "",
    "project_root": "",
    "framework_version": "1.0.0",
    "compliance_score": 0,
    "violations": [],
    "warnings": [],
    "mcp_usage_analysis": {},
    "quality_gates": {},
    "security_compliance": {},
    "pixi_compliance": {}
  }
}
JSON_EOF
}

# Update compliance report with results
update_compliance_report() {
    local section="$1"
    local status="$2"
    local message="$3"
    local severity="${4:-info}"
    
    # Update JSON report (simplified for bash implementation)
    # In production, use jq or Python for proper JSON manipulation
    log_info "Logging to compliance report: $section - $status"
}

# MANDATORY: ZERO-TOLERANCE QUALITY POLICY
check_quality_gates() {
    log_section "ZERO-TOLERANCE QUALITY POLICY VALIDATION"
    
    local quality_violations=0
    
    # Check if pixi.toml or pyproject.toml exists
    if [[ \! -f "${PROJECT_ROOT}/pixi.toml" && \! -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
        log_critical "No pixi.toml or pyproject.toml found - PIXI-ONLY policy violated"
        quality_violations=$((quality_violations + 1))
    else
        log_success "PIXI configuration file found"
    fi
    
    # Check for pip violations (if Python files exist)
    if find "${PROJECT_ROOT}" -name "*.py" -type f | head -1 | grep -q .; then
        if find "${PROJECT_ROOT}" -name "requirements.txt" -o -name "setup.py" -o -name "pip" | head -1 | grep -q .; then
            log_critical "pip dependencies detected - PIXI-ONLY policy violated"
            quality_violations=$((quality_violations + 1))
        else
            log_success "PIXI-ONLY compliance verified - no pip dependencies"
        fi
    else
        log_info "No Python files found - skipping pip dependency check"
    fi
    
    # Test framework check (when tests exist)
    if [[ -d "${PROJECT_ROOT}/tests" ]]; then
        if command -v pixi >/dev/null 2>&1; then
            cd "${PROJECT_ROOT}"
            if pixi info >/dev/null 2>&1; then
                log_info "Pixi environment detected - checking quality commands"
                
                # Check if quality commands are defined
                if pixi task list | grep -q "test\|quality\|lint"; then
                    log_success "Quality commands found in pixi configuration"
                else
                    log_warning "Quality commands not found in pixi configuration"
                fi
            else
                log_warning "Pixi environment not properly initialized"
            fi
        else
            log_warning "Pixi not installed - cannot verify quality commands"
        fi
    else
        log_info "No tests directory found - project in early development phase"
    fi
    
    return $quality_violations
}

# MCP-FIRST STRATEGY COMPLIANCE (TARGET: 95% MCP Usage)
check_mcp_compliance() {
    log_section "MCP-FIRST STRATEGY COMPLIANCE"
    
    local mcp_violations=0
    
    # Check .mcp.json configuration
    if [[ -f "${PROJECT_ROOT}/.mcp.json" ]]; then
        log_success "MCP configuration found: .mcp.json"
        
        # Validate MCP server configurations
        local mcp_servers=$(grep -o '"[^"]*":' "${PROJECT_ROOT}/.mcp.json" | grep -v "mcpServers" | wc -l)
        if [[ $mcp_servers -gt 0 ]]; then
            log_success "MCP servers configured: $mcp_servers servers detected"
        else
            log_warning "No MCP servers detected in configuration"
        fi
    else
        log_critical "MCP configuration missing - MCP-first strategy violated"
        mcp_violations=$((mcp_violations + 1))
    fi
    
    # Check for TaskMaster AI integration
    if grep -q "task-master-ai" "${PROJECT_ROOT}/.mcp.json" 2>/dev/null; then
        log_success "TaskMaster AI MCP integration detected"
    else
        log_warning "TaskMaster AI MCP integration not found"
    fi
    
    # Validate MCP usage patterns in source code (when exists)
    if find "${PROJECT_ROOT}" -name "*.py" -type f | head -1 | grep -q .; then
        local bash_usage=$(find "${PROJECT_ROOT}" -name "*.py" -exec grep -l "subprocess\|os\.system\|shell=True" {} \; 2>/dev/null | wc -l)
        local mcp_usage=$(find "${PROJECT_ROOT}" -name "*.py" -exec grep -l "mcp__\|MCP" {} \; 2>/dev/null | wc -l)
        
        if [[ $bash_usage -gt 0 ]]; then
            log_warning "Direct shell usage detected in $bash_usage files - review for MCP alternatives"
        fi
        
        if [[ $mcp_usage -gt 0 ]]; then
            log_success "MCP tool usage detected in $mcp_usage files"
        fi
    fi
    
    return $mcp_violations
}

# GIT WORKFLOW STANDARDS
check_git_workflow_compliance() {
    log_section "GIT WORKFLOW STANDARDS"
    
    local git_violations=0
    
    # Check if git repository is initialized
    if [[ -d "${PROJECT_ROOT}/.git" ]]; then
        log_success "Git repository initialized"
        
        # Check git configuration
        cd "${PROJECT_ROOT}"
        
        # Verify git hooks (if any)
        if [[ -d ".git/hooks" ]]; then
            local hook_count=$(find .git/hooks -name "*.sample" -o -name "*" -type f | grep -v "\.sample$" | wc -l)
            if [[ $hook_count -gt 0 ]]; then
                log_success "Git hooks configured: $hook_count hooks"
            else
                log_info "No custom git hooks found"
            fi
        fi
        
        # Check for .gitignore
        if [[ -f ".gitignore" ]]; then
            log_success "Gitignore file present"
            
            # Validate gitignore patterns for Python/Node.js
            if grep -q "__pycache__\|*.pyc\|node_modules" ".gitignore"; then
                log_success "Standard ignore patterns found"
            else
                log_warning "Standard ignore patterns missing from .gitignore"
            fi
        else
            log_warning "No .gitignore file found"
        fi
    else
        log_critical "Git repository not initialized"
        git_violations=$((git_violations + 1))
    fi
    
    return $git_violations
}

# TASKMASTER AI INTEGRATION
check_taskmaster_integration() {
    log_section "TASKMASTER AI INTEGRATION"
    
    local taskmaster_violations=0
    
    # Check TaskMaster directory structure
    if [[ -d "${PROJECT_ROOT}/.taskmaster" ]]; then
        log_success "TaskMaster directory found"
        
        # Check essential TaskMaster files
        local required_files=("config.json" "tasks/tasks.json" "docs/prd.txt")
        for file in "${required_files[@]}"; do
            if [[ -f "${PROJECT_ROOT}/.taskmaster/$file" ]]; then
                log_success "TaskMaster file found: $file"
            else
                log_warning "TaskMaster file missing: $file"
            fi
        done
    else
        log_critical "TaskMaster not initialized - run 'task-master init'"
        taskmaster_violations=$((taskmaster_violations + 1))
    fi
    
    # Check TaskMaster MCP integration
    if command -v npx >/dev/null 2>&1; then
        if npx -y --package=task-master-ai task-master-ai --version >/dev/null 2>&1; then
            log_success "TaskMaster AI CLI accessible"
        else
            log_warning "TaskMaster AI CLI not accessible via npx"
        fi
    else
        log_warning "npx not available - cannot verify TaskMaster CLI"
    fi
    
    return $taskmaster_violations
}

# SECURITY COMPLIANCE
check_security_compliance() {
    log_section "SECURITY COMPLIANCE"
    
    local security_violations=0
    
    # Check for sensitive files
    local sensitive_patterns=("*.key" "*.pem" "*.p12" "*.pfx" "private_key*")
    for pattern in "${sensitive_patterns[@]}"; do
        if find "${PROJECT_ROOT}" -name "$pattern" -type f | head -1 | grep -q .; then
            log_critical "Sensitive files detected: $pattern"
            security_violations=$((security_violations + 1))
        fi
    done
    
    # Check .env file security
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        log_info "Environment file found - checking security"
        
        # Check if .env is in .gitignore
        if grep -q "\.env" "${PROJECT_ROOT}/.gitignore" 2>/dev/null; then
            log_success "Environment file properly ignored in git"
        else
            log_critical "Environment file not in .gitignore - security risk"
            security_violations=$((security_violations + 1))
        fi
        
        # Check for hardcoded secrets (basic patterns)
        if grep -i "password\|secret\|key" "${PROJECT_ROOT}/.env" | grep -v "your_.*_here" | head -1 | grep -q .; then
            log_warning "Potential secrets detected in .env file"
        fi
    fi
    
    # Check for TODO/FIXME security items
    if find "${PROJECT_ROOT}" -name "*.py" -o -name "*.js" -o -name "*.ts" | xargs grep -i "TODO.*security\|FIXME.*security" 2>/dev/null | head -1 | grep -q .; then
        log_warning "Security-related TODO/FIXME items found"
    fi
    
    return $security_violations
}

# PERFORMANCE COMPLIANCE
check_performance_compliance() {
    log_section "PERFORMANCE COMPLIANCE"
    
    # Check for performance monitoring setup
    if find "${PROJECT_ROOT}" -name "*.py" -exec grep -l "time\|perf\|profile" {} \; 2>/dev/null | head -1 | grep -q .; then
        log_success "Performance monitoring patterns detected"
    else
        log_info "No performance monitoring detected - consider adding for production"
    fi
    
    # Check for async patterns (Python)
    if find "${PROJECT_ROOT}" -name "*.py" -exec grep -l "async\|await" {} \; 2>/dev/null | head -1 | grep -q .; then
        log_success "Async patterns detected for performance"
    else
        log_info "No async patterns detected"
    fi
}

# FRAMEWORK ADHERENCE CHECK
check_framework_adherence() {
    log_section "UNIVERSAL DEVELOPMENT FRAMEWORK ADHERENCE"
    
    # Check for CLAUDE.md
    if [[ -f "${PROJECT_ROOT}/CLAUDE.md" ]]; then
        log_success "Project instructions file (CLAUDE.md) found"
    else
        log_warning "Project instructions file (CLAUDE.md) missing"
    fi
    
    # Check for .claude directory
    if [[ -d "${PROJECT_ROOT}/.claude" ]]; then
        log_success "Claude Code configuration directory found"
        
        # Check for custom commands
        if [[ -d "${PROJECT_ROOT}/.claude/commands" ]]; then
            local command_count=$(find "${PROJECT_ROOT}/.claude/commands" -name "*.md" | wc -l)
            log_success "Claude Code custom commands found: $command_count commands"
        fi
    else
        log_warning "Claude Code configuration directory missing"
    fi
    
    # Check directory structure compliance
    local expected_dirs=("src" "tests" "scripts" "docs")
    for dir in "${expected_dirs[@]}"; do
        if [[ -d "${PROJECT_ROOT}/$dir" ]]; then
            log_success "Standard directory found: $dir"
        else
            log_info "Standard directory missing: $dir (may be created as needed)"
        fi
    done
}

# GENERATE COMPLIANCE SCORE
calculate_compliance_score() {
    local total_checks=50  # Approximate number of checks
    local failed_checks=$((VIOLATIONS * 2 + WARNINGS))  # Weight violations more heavily
    local score=$(( (total_checks - failed_checks) * 100 / total_checks ))
    
    if [[ $score -lt 0 ]]; then
        score=0
    fi
    
    echo $score
}

# MAIN COMPLIANCE CHECK FUNCTION
main() {
    log_section "CLAUDECODE SESSION ORCHESTRATOR - FRAMEWORK COMPLIANCE CHECK"
    echo "Project Root: ${PROJECT_ROOT}"
    echo "Report: ${COMPLIANCE_REPORT}"
    echo "Started: $(date)"
    
    # Initialize compliance report
    init_compliance_report
    
    # Run all compliance checks
    check_quality_gates
    check_mcp_compliance
    check_git_workflow_compliance
    check_taskmaster_integration
    check_security_compliance
    check_performance_compliance
    check_framework_adherence
    
    # Calculate final score
    local compliance_score=$(calculate_compliance_score)
    
    # Generate summary
    log_section "COMPLIANCE SUMMARY"
    echo -e "Compliance Score: ${CYAN}${compliance_score}/100${NC}"
    echo -e "Critical Violations: ${RED}${VIOLATIONS}${NC}"
    echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
    
    # Compliance status
    if [[ $VIOLATIONS -eq 0 ]]; then
        if [[ $WARNINGS -eq 0 ]]; then
            log_success "FULL COMPLIANCE - All checks passed"
            exit 0
        else
            log_warning "PARTIAL COMPLIANCE - $WARNINGS warnings to address"
            exit 1
        fi
    else
        log_critical "NON-COMPLIANT - $VIOLATIONS critical violations must be fixed"
        exit 2
    fi
}

# Execute main function
main "$@"
EOF < /dev/null
