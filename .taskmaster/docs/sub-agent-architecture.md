# Sub-Agent Architecture and Communication Protocol

## Overview

This document defines the foundational architecture for specialized sub-agents in Claude Code, enabling 70% context reduction and 3-5x task completion capability through fresh 25K token contexts.

## Core Architecture

### Sub-Agent Types

Based on Claude Code's Task tool capabilities, we define these specialized agent types:

```yaml
# Available sub-agent types in Claude Code Task tool
subagent_types:
  - general-purpose    # Built-in: Complex multi-step tasks
  - code-reviewer     # Built-in: Code quality and security
  - git-workflow-specialist    # Custom: Git operations and MCP limitations
  - conflict-resolver         # Custom: Merge conflict resolution
  - action-reorganizer        # Custom: GitHub Actions restructuring
  - cross-platform-implementer # Custom: Platform-specific testing
  - pixi-optimizer           # Custom: Pixi environment management
  - quality-enforcer         # Custom: Enhanced code-reviewer
  - taskmaster-coordinator   # Custom: TaskMaster orchestration
  - ci-framework-maintainer  # Custom: Framework maintenance
```

### YAML Frontmatter Template

```yaml
---
name: [specialist-name]
description: [Purpose and trigger conditions]. Use when [specific scenarios].
subagent_type: [specialist-name]
tools: [Required MCP tools list]
framework_compliance:
  mcp_first: true          # 95% MCP usage
  quality_gates: true      # Zero-tolerance policy
  taskmaster_integration: true
  pixi_only: true         # ZERO pip dependencies
communication:
  response_format: concise # <4 lines unless detail requested
  no_hyperbole: true      # Professional tone
  status_reporting: true   # Clear success/failure
---
```

## Communication Protocol

### Context Transfer Standard

```typescript
interface SubAgentContext {
  // Core workflow state
  projectRoot: string
  currentTask: {
    id: string
    title: string
    priority: string
    dependencies: string[]
  }
  
  // Framework state
  frameworkCompliance: {
    qualityStatus: 'passing' | 'failing'
    mcpCoverage: number  // Target: 95%
    lastQualityCheck: timestamp
  }
  
  // TaskMaster state
  taskmaster: {
    currentTag: string
    nextTaskId?: string
    blockedTasks: string[]
  }
  
  // Critical context (max 500 tokens)
  criticalContext?: string
  
  // Sub-agent specific data
  specialistData?: Record<string, any>
}
```

### Request/Response Format

```typescript
// Sub-agent invocation
interface SubAgentRequest {
  type: 'task_execution' | 'analysis' | 'coordination'
  context: SubAgentContext
  prompt: string
  expectedOutput: 'implementation' | 'analysis' | 'status'
}

// Sub-agent response
interface SubAgentResponse {
  success: boolean
  result: {
    summary: string        // <4 lines max
    actions_taken: string[]
    quality_status: 'pass' | 'fail'
    next_actions?: string[]
  }
  context_updates: Partial<SubAgentContext>
  errors?: string[]
}
```

## TaskMaster AI Integration

### State Sharing Protocol

```typescript
interface TaskMasterIntegration {
  // Before sub-agent execution
  capture_state(): {
    current_task: Task
    project_status: ProjectStatus
    quality_metrics: QualityMetrics
  }
  
  // During sub-agent execution
  update_progress(taskId: string, status: TaskStatus): void
  
  // After sub-agent execution
  sync_changes(updates: TaskUpdate[]): void
}
```

### Quality Gate Integration

```yaml
quality_gates:
  pre_execution:
    - verify_taskmaster_sync: true
    - check_dependency_status: true
  
  during_execution:
    - maintain_mcp_first: 95%
    - enforce_pixi_only: true
    - track_progress: continuous
  
  post_execution:
    - run_quality_checks: "pixi run quality"
    - update_task_status: required
    - verify_framework_compliance: true
```

## Error Handling and Recovery

### Graceful Degradation Strategy

```yaml
error_handling:
  mcp_tool_failures:
    strategy: "fallback_to_bash"  # Strategic 5% usage
    documentation: "file_github_issues"
    recovery: "maintain_taskmaster_sync"
  
  context_transfer_failures:
    strategy: "minimal_context_retry"
    escalation: "return_to_main_context"
    state_preservation: "taskmaster_backup"
  
  quality_gate_failures:
    strategy: "immediate_stop"
    investigation: "root_cause_analysis"
    recovery: "systematic_fix_before_proceed"
```

### Recovery Mechanisms

```typescript
interface RecoveryProtocol {
  // Isolation protection
  isolate_failure(agentType: string): void
  
  // State recovery
  restore_from_taskmaster(): SubAgentContext
  
  // Rollback strategies
  rollback_to_last_good_state(): void
  
  // Escalation paths
  escalate_to_main_context(reason: string): void
}
```

## Framework Compliance Verification

### MCP-First Strategy Enforcement

```yaml
mcp_compliance:
  target_coverage: 95%
  allowed_bash_usage: 5%  # Strategic only
  monitoring:
    - track_tool_usage_per_agent
    - measure_mcp_vs_bash_ratio
    - document_mcp_limitations
  
  fallback_criteria:
    - mcp_tool_unavailable
    - mcp_functionality_insufficient
    - emergency_fix_required
```

### Quality Standards Integration

```yaml
quality_standards:
  zero_tolerance_policy:
    - no_f_e9_violations: true
    - 100_percent_test_coverage: true
    - all_ci_checks_green: true
  
  validation_commands:
    - "pixi run test"      # 100% pass rate
    - "pixi run quality"   # Zero critical violations
    - "pixi run lint"      # Zero F,E9 violations
  
  emergency_protocols:
    - "scripts/fix-lint-violations.sh"  # CI failures
    - immediate_investigation: true
    - systematic_resolution: required
```

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Implement basic context transfer protocol
2. Create YAML frontmatter template system
3. Establish TaskMaster integration points
4. Build error handling framework

### Phase 2: Quality Integration
1. Implement framework compliance verification
2. Create quality gate enforcement
3. Build MCP-first strategy monitoring
4. Establish recovery mechanisms

### Phase 3: Sub-Agent Development
1. Implement critical path agents (git-workflow, conflict-resolver)
2. Build optimization agents (action-reorganizer, pixi-optimizer)
3. Create coordination agents (taskmaster-coordinator)
4. Develop maintenance agents (ci-framework-maintainer)

### Success Metrics
- **Context Efficiency**: 70% reduction in main context usage
- **Task Completion**: 3-5x increase in complex task capability
- **Framework Compliance**: 95% MCP usage, zero quality violations
- **Parallel Execution**: 3-4 concurrent sub-agent operations

## Usage Examples

### Git Workflow Specialist
```yaml
Task(
  description="Complex git merge resolution",
  prompt="Resolve CLAUDE.md merge conflicts with systematic approach",
  subagent_type="git-workflow-specialist"
)
```

### Action Reorganizer
```yaml
Task(
  description="GitHub Actions restructuring",
  prompt="Reorganize actions directory maintaining all references",
  subagent_type="action-reorganizer"
)
```

This architecture enables systematic, framework-compliant sub-agent operations with fresh contexts while maintaining quality standards and TaskMaster integration.