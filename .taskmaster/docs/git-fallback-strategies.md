# Git Workflow Strategic Bash Fallback Strategies

## Overview

Strategic Bash fallback mechanisms for git-workflow-specialist when MCP git tools have limitations. Maintains 95% MCP compliance with systematic 5% strategic Bash usage.

## Fallback Decision Matrix

### Level 1: Interactive Operations (MCP Unavailable)

```yaml
interactive_git_operations:
  mcp_limitation: "MCP tools cannot handle interactive interfaces"
  bash_necessity: true
  usage_category: strategic_required
  
  operations:
    selective_staging:
      command: "git add -p"
      scenario: "User needs to stage specific hunks from modified files"
      mcp_alternative: "mcp__git__git_add (file-level only)"
      fallback_justification: "Hunk-level precision requires interactive mode"
      
    interactive_rebase:
      command: "git rebase -i"
      scenario: "Squashing commits or reordering commit history"
      mcp_alternative: "mcp__git__git_rebase (non-interactive only)"
      fallback_justification: "Commit editing requires interactive interface"
      
    interactive_add:
      command: "git add -i"
      scenario: "Complex staging workflow with multiple file operations"
      mcp_alternative: "mcp__git__git_add (simple file adds)"
      fallback_justification: "Menu-driven interface not available via MCP"
```

### Level 2: Advanced Git Operations (MCP Insufficient)

```yaml
advanced_git_operations:
  mcp_limitation: "MCP tools lack advanced git functionality"
  bash_necessity: conditional
  usage_category: strategic_enhancement
  
  operations:
    reflog_operations:
      command: "git reflog"
      scenario: "Recovery from lost commits or branch operations"
      mcp_alternative: "mcp__git__git_log (limited history)"
      fallback_justification: "Reflog access not exposed via MCP"
      
    bisect_operations:
      command: "git bisect start/good/bad"
      scenario: "Binary search for bug introduction"
      mcp_alternative: "None available"
      fallback_justification: "Bisect workflow not implemented in MCP"
      
    worktree_management:
      command: "git worktree add/remove"
      scenario: "Multiple working directories for same repository"
      mcp_alternative: "None available"
      fallback_justification: "Worktree management not exposed via MCP"
      
    advanced_log_queries:
      command: "git log --graph --oneline --decorate"
      scenario: "Visual commit history with branch relationships"
      mcp_alternative: "mcp__git__git_log (basic format)"
      fallback_justification: "Advanced formatting options unavailable"
```

### Level 3: Configuration and Hooks (MCP Limited)

```yaml
configuration_operations:
  mcp_limitation: "MCP tools cannot modify git configuration"
  bash_necessity: environment_dependent
  usage_category: strategic_setup
  
  operations:
    user_configuration:
      command: "git config user.name/user.email"
      scenario: "Setting up commit attribution"
      mcp_alternative: "None available"
      fallback_justification: "Configuration modification not in MCP scope"
      
    gpg_configuration:
      command: "git config user.signingkey/gpg.program"
      scenario: "Setting up GPG signing for commits"
      mcp_alternative: "mcp__git__git_commit (gpg_sign parameter)"
      fallback_justification: "GPG setup requires configuration access"
      
    hook_management:
      command: "cp pre-commit .git/hooks/"
      scenario: "Installing git hooks for quality enforcement"
      mcp_alternative: "None available"
      fallback_justification: "File system operations in .git directory"
```

### Level 4: Emergency Recovery (MCP Unavailable)

```yaml
emergency_operations:
  mcp_limitation: "MCP tools cannot handle repository corruption"
  bash_necessity: critical
  usage_category: strategic_emergency
  
  operations:
    repository_repair:
      command: "git fsck --full"
      scenario: "Detecting and reporting repository corruption"
      mcp_alternative: "None available"
      fallback_justification: "Low-level repository integrity checks"
      
    garbage_collection:
      command: "git gc --aggressive"
      scenario: "Optimizing repository after corruption recovery"
      mcp_alternative: "None available"
      fallback_justification: "Repository maintenance not exposed"
      
    index_recovery:
      command: "git reset --mixed HEAD"
      scenario: "Recovering from index corruption"
      mcp_alternative: "mcp__git__git_reset (limited options)"
      fallback_justification: "Specific reset modes may not be available"
      
    reference_recovery:
      command: "git reflog expire --expire=now --all"
      scenario: "Cleaning up after reference corruption"
      mcp_alternative: "None available"
      fallback_justification: "Reference management not in MCP scope"
```

## Strategic Fallback Implementation

### Usage Monitoring and Compliance

```typescript
class StrategicBashManager {
  private mcpOperations = 0
  private bashOperations = 0
  private readonly TARGET_MCP_RATIO = 0.95
  
  // Pre-execution validation
  async validateStrategicBashUsage(operation: string): Promise<boolean> {
    const currentRatio = this.getMcpRatio()
    
    // Always allow if we're above target ratio
    if (currentRatio >= this.TARGET_MCP_RATIO) {
      return true
    }
    
    // Only allow for strategic scenarios when below target
    return this.isStrategicOperation(operation)
  }
  
  // Execute with usage tracking
  async executeStrategicBash(
    operation: string,
    args: string[],
    justification: string
  ): Promise<BashResult> {
    
    // Validate usage allowance
    if (!await this.validateStrategicBashUsage(operation)) {
      throw new Error(`Strategic Bash usage limit exceeded for non-critical operation: ${operation}`)
    }
    
    // Log strategic usage
    await this.logStrategicUsage(operation, justification)
    
    // Execute with monitoring
    const result = await this.executeBashCommand(`git ${operation}`, args)
    
    // Track usage
    this.bashOperations++
    
    return result
  }
  
  private isStrategicOperation(operation: string): boolean {
    const strategicOperations = [
      'add -p',      // Interactive staging
      'rebase -i',   // Interactive rebase
      'fsck',        // Repository repair
      'reflog',      // Reference recovery
      'config'       // Configuration
    ]
    
    return strategicOperations.some(strategic => 
      operation.includes(strategic)
    )
  }
}
```

### Fallback Decision Logic

```typescript
interface FallbackDecision {
  useBash: boolean
  justification: string
  category: 'required' | 'enhancement' | 'setup' | 'emergency'
  mcpAlternative?: string
}

class FallbackDecisionEngine {
  
  async evaluateFallbackNeed(
    operation: string,
    mcpError?: Error
  ): Promise<FallbackDecision> {
    
    // Level 1: Interactive operations (no MCP alternative)
    if (this.isInteractiveOperation(operation)) {
      return {
        useBash: true,
        justification: 'Interactive interface required, no MCP alternative',
        category: 'required'
      }
    }
    
    // Level 2: Advanced operations (MCP insufficient)
    if (this.isAdvancedOperation(operation)) {
      return {
        useBash: true,
        justification: 'Advanced git functionality not available in MCP',
        category: 'enhancement',
        mcpAlternative: this.getMcpAlternative(operation)
      }
    }
    
    // Level 3: Configuration operations (MCP limited)
    if (this.isConfigurationOperation(operation)) {
      return {
        useBash: true,
        justification: 'Git configuration modification required',
        category: 'setup'
      }
    }
    
    // Level 4: Emergency operations (MCP unavailable)
    if (this.isEmergencyOperation(operation)) {
      return {
        useBash: true,
        justification: 'Emergency repository recovery required',
        category: 'emergency'
      }
    }
    
    // Default: Try to use MCP
    return {
      useBash: false,
      justification: 'MCP tool should handle this operation',
      category: 'required'
    }
  }
  
  private isInteractiveOperation(operation: string): boolean {
    return [
      'add -p', 'add -i',
      'rebase -i',
      'checkout -p'
    ].some(interactive => operation.includes(interactive))
  }
  
  private isAdvancedOperation(operation: string): boolean {
    return [
      'reflog', 'bisect', 'worktree',
      'log --graph', 'log --oneline',
      'cherry-pick --continue'
    ].some(advanced => operation.includes(advanced))
  }
  
  private isConfigurationOperation(operation: string): boolean {
    return [
      'config user.', 'config gpg.',
      'config core.', 'config remote.'
    ].some(config => operation.includes(config))
  }
  
  private isEmergencyOperation(operation: string): boolean {
    return [
      'fsck', 'gc --aggressive',
      'reflog expire', 'reset --hard'
    ].some(emergency => operation.includes(emergency))
  }
}
```

## MCP Limitation Documentation and Reporting

### Automatic Limitation Logging

```typescript
interface McpLimitation {
  operation: string
  mcpTool: string
  error: string
  fallbackUsed: boolean
  timestamp: Date
  frequency: number
}

class McpLimitationTracker {
  private limitations = new Map<string, McpLimitation>()
  
  async logMcpLimitation(
    operation: string,
    mcpTool: string,
    error: Error,
    fallbackResult?: BashResult
  ): Promise<void> {
    
    const key = `${mcpTool}:${operation}`
    const existing = this.limitations.get(key)
    
    const limitation: McpLimitation = {
      operation,
      mcpTool,
      error: error.message,
      fallbackUsed: !!fallbackResult,
      timestamp: new Date(),
      frequency: existing ? existing.frequency + 1 : 1
    }
    
    this.limitations.set(key, limitation)
    
    // Report to improvement tracking
    if (limitation.frequency >= 3) {
      await this.reportRecurringLimitation(limitation)
    }
  }
  
  private async reportRecurringLimitation(limitation: McpLimitation): Promise<void> {
    const report = {
      title: `MCP Limitation: ${limitation.operation}`,
      description: `
MCP tool ${limitation.mcpTool} repeatedly fails for operation: ${limitation.operation}

Error: ${limitation.error}
Frequency: ${limitation.frequency} occurrences
Fallback available: ${limitation.fallbackUsed ? 'Yes' : 'No'}

Suggested improvement: Add ${limitation.operation} support to ${limitation.mcpTool}
      `,
      category: 'mcp_enhancement',
      priority: limitation.fallbackUsed ? 'medium' : 'high'
    }
    
    // Log for framework improvement
    console.log(`MCP Improvement Needed: ${JSON.stringify(report)}`)
    
    // Could also file GitHub issue automatically
    // await this.fileGitHubIssue(report)
  }
  
  generateLimitationReport(): McpLimitationReport {
    const limitations = Array.from(this.limitations.values())
    
    return {
      totalLimitations: limitations.length,
      recurringLimitations: limitations.filter(l => l.frequency >= 3).length,
      criticalLimitations: limitations.filter(l => !l.fallbackUsed).length,
      mcpCoverage: this.calculateMcpCoverage(),
      recommendedImprovements: this.generateRecommendations(limitations)
    }
  }
}
```

### Framework Integration Guidelines

```yaml
strategic_bash_integration:
  usage_principles:
    - maintain_95_percent_mcp_target
    - document_every_fallback_usage
    - justify_bash_necessity
    - monitor_usage_ratios
    - report_mcp_limitations
  
  quality_assurance:
    - validate_bash_commands_before_execution
    - ensure_framework_compliance_maintained
    - verify_taskmaster_integration_preserved
    - confirm_quality_gates_still_enforced
  
  escalation_criteria:
    - mcp_ratio_below_90_percent: review_usage_patterns
    - recurring_limitations: file_improvement_requests
    - critical_failures: escalate_to_main_context
    - quality_degradation: immediate_investigation
```

## Usage Examples

### Interactive Staging Fallback

```typescript
// Scenario: Stage specific hunks from large file changes
async handleSelectiveStaging(files: string[]): Promise<GitResult> {
  try {
    // Attempt MCP first
    return await this.mcpGitAdd(files)
    
  } catch (error) {
    if (this.requiresHunkLevelPrecision(error)) {
      // Strategic Bash fallback justified
      return await this.strategicBashManager.executeStrategicBash(
        'add -p',
        files,
        'Hunk-level staging requires interactive interface'
      )
    }
    throw error
  }
}
```

### Emergency Recovery Fallback

```typescript
// Scenario: Repository corruption detected
async handleRepositoryCorruption(): Promise<RecoveryResult> {
  // This requires strategic Bash - no MCP alternative
  const fsckResult = await this.strategicBashManager.executeStrategicBash(
    'fsck --full',
    [],
    'Repository integrity check requires low-level access'
  )
  
  if (fsckResult.detectedCorruption) {
    // Additional emergency operations
    await this.strategicBashManager.executeStrategicBash(
      'gc --aggressive',
      [],
      'Repository optimization after corruption detection'
    )
  }
  
  return { repaired: true, method: 'strategic_bash_emergency' }
}
```

This strategic fallback system ensures git-workflow-specialist maintains 95% MCP compliance while handling the 5% of operations that require Bash due to MCP limitations, with comprehensive monitoring and improvement feedback.