#\!/bin/bash
# MCP Usage Monitor - Track MCP-first strategy compliance
# Target: 95% MCP tool usage vs strategic Bash usage

set -euo pipefail

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MONITOR_LOG="${PROJECT_ROOT}/logs/compliance/mcp-usage-$(date +%Y%m%d).log"
USAGE_REPORT="${PROJECT_ROOT}/logs/compliance/mcp-usage-report.json"

# Ensure log directory exists
mkdir -p "$(dirname "$MONITOR_LOG")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_usage() {
    local tool_type="$1"
    local tool_name="$2"
    local operation="$3"
    local timestamp=$(date -Iseconds)
    
    echo "${timestamp},${tool_type},${tool_name},${operation}" >> "$MONITOR_LOG"
}

analyze_mcp_usage() {
    echo -e "${BLUE}[MCP USAGE ANALYSIS]${NC}"
    
    if [[ \! -f "$MONITOR_LOG" ]]; then
        echo -e "${YELLOW}No usage data found for today${NC}"
        return 1
    fi
    
    local total_operations=$(wc -l < "$MONITOR_LOG" 2>/dev/null || echo "0")
    local mcp_operations=$(grep ",mcp," "$MONITOR_LOG" 2>/dev/null | wc -l || echo "0")
    local bash_operations=$(grep ",bash," "$MONITOR_LOG" 2>/dev/null | wc -l || echo "0")
    
    if [[ $total_operations -eq 0 ]]; then
        echo "No operations recorded today"
        return 0
    fi
    
    local mcp_percentage=$(( mcp_operations * 100 / total_operations ))
    local bash_percentage=$(( bash_operations * 100 / total_operations ))
    
    echo "Total Operations: $total_operations"
    echo "MCP Operations: $mcp_operations ($mcp_percentage%)"
    echo "Bash Operations: $bash_operations ($bash_percentage%)"
    
    # Compliance check
    if [[ $mcp_percentage -ge 95 ]]; then
        echo -e "${GREEN}✅ MCP-FIRST COMPLIANCE: $mcp_percentage% >= 95% target${NC}"
    elif [[ $mcp_percentage -ge 90 ]]; then
        echo -e "${YELLOW}⚠️ MCP USAGE WARNING: $mcp_percentage% < 95% target${NC}"
    else
        echo -e "${RED}❌ MCP COMPLIANCE VIOLATION: $mcp_percentage% << 95% target${NC}"
    fi
    
    # Generate JSON report
    cat > "$USAGE_REPORT" << JSON_EOF
{
  "date": "$(date -Idate)",
  "mcp_usage_analysis": {
    "total_operations": $total_operations,
    "mcp_operations": $mcp_operations,
    "bash_operations": $bash_operations,
    "mcp_percentage": $mcp_percentage,
    "bash_percentage": $bash_percentage,
    "target_mcp_percentage": 95,
    "compliant": $(if [[ $mcp_percentage -ge 95 ]]; then echo "true"; else echo "false"; fi)
  }
}
JSON_EOF
}

# Track specific tool usage patterns
analyze_tool_patterns() {
    echo -e "\n${BLUE}[TOOL USAGE PATTERNS]${NC}"
    
    if [[ \! -f "$MONITOR_LOG" ]]; then
        return 1
    fi
    
    echo "Most used MCP tools:"
    grep ",mcp," "$MONITOR_LOG" 2>/dev/null | cut -d',' -f3 | sort | uniq -c | sort -nr | head -5 || echo "No MCP tools recorded"
    
    echo -e "\nMost used Bash commands:"
    grep ",bash," "$MONITOR_LOG" 2>/dev/null | cut -d',' -f3 | sort | uniq -c | sort -nr | head -5 || echo "No Bash commands recorded"
    
    # Check for strategic vs non-strategic bash usage
    echo -e "\n${BLUE}[STRATEGIC BASH ANALYSIS]${NC}"
    local strategic_commands=("git" "pixi" "npm" "docker" "ssh" "scp")
    local strategic_count=0
    local non_strategic_count=0
    
    while IFS= read -r line; do
        if echo "$line" | grep -q ",bash,"; then
            local command=$(echo "$line" | cut -d',' -f3)
            local is_strategic=false
            
            for strategic_cmd in "${strategic_commands[@]}"; do
                if echo "$command" | grep -q "^$strategic_cmd"; then
                    is_strategic=true
                    break
                fi
            done
            
            if $is_strategic; then
                strategic_count=$((strategic_count + 1))
            else
                non_strategic_count=$((non_strategic_count + 1))
            fi
        fi
    done < "$MONITOR_LOG" 2>/dev/null || true
    
    echo "Strategic Bash usage: $strategic_count commands"
    echo "Non-strategic Bash usage: $non_strategic_count commands"
    
    if [[ $non_strategic_count -gt 0 ]]; then
        echo -e "${YELLOW}⚠️ Consider MCP alternatives for non-strategic Bash commands${NC}"
    fi
}

# Monitor real-time usage (background process)
start_monitoring() {
    echo "Starting MCP usage monitoring..."
    echo "Monitoring log: $MONITOR_LOG"
    
    # This would be implemented as a background service in production
    # For now, provide instructions for manual usage tracking
    cat << 'INSTRUCTIONS'

MCP Usage Monitoring Instructions:
==================================

To track tool usage, log operations using:
  log_usage "mcp" "tool_name" "operation"
  log_usage "bash" "command" "operation"

Examples:
  log_usage "mcp" "task-master-ai" "get_tasks"
  log_usage "mcp" "git" "status"
  log_usage "bash" "pixi run test" "quality_check"

Run analysis with:
  ./scripts/compliance/mcp-usage-monitor.sh analyze

INSTRUCTIONS
}

# Main function
main() {
    case "${1:-analyze}" in
        "start")
            start_monitoring
            ;;
        "analyze")
            analyze_mcp_usage
            analyze_tool_patterns
            ;;
        "log")
            if [[ $# -lt 4 ]]; then
                echo "Usage: $0 log <tool_type> <tool_name> <operation>"
                exit 1
            fi
            log_usage "$2" "$3" "$4"
            echo "Logged: $2 $3 $4"
            ;;
        *)
            echo "Usage: $0 {start|analyze|log}"
            echo "  start   - Start monitoring (shows instructions)"
            echo "  analyze - Analyze current usage patterns"
            echo "  log     - Log a tool usage event"
            exit 1
            ;;
    esac
}

main "$@"
EOF < /dev/null
