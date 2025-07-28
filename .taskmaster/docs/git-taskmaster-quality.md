# Git Workflow TaskMaster Integration & Quality Gates

## TaskMaster Integration

### State Synchronization

```typescript
interface GitTaskMasterSync {
  // Capture pre-operation state
  async captureGitOperationState(
    repoPath: string,
    taskId: string
  ): Promise<GitOperationContext> {
    
    const [taskMasterState, gitStatus, qualityStatus] = await Promise.all([
      this.mcpTaskMasterGetTask(taskId),
      this.mcpGitStatus(repoPath),
      this.checkQualityGates()
    ])
    
    return {
      taskMasterState,
      gitStatus: this.parseGitStatus(gitStatus),
      qualityStatus,
      timestamp: new Date(),
      operation: 'pre_git_operation'
    }
  }
  
  // Update progress during operations
  async updateGitProgress(
    taskId: string,
    operation: GitOperation,
    status: 'started' | 'in_progress' | 'completed' | 'failed',
    details?: GitProgressDetails
  ): Promise<void> {
    
    const progressUpdate = {
      operation: `Git: ${operation.type}`,
      status,
      details: details || {},
      agent: 'git-workflow-specialist',
      timestamp: new Date()
    }
    
    await this.mcpTaskMasterUpdateTask(taskId, progressUpdate)
  }
}
```

### Quality Gate Enforcement

```typescript
interface GitQualityGates {
  // Pre-commit quality validation
  async enforcePreCommitQuality(): Promise<QualityGateResult> {
    
    const checks = await this.runQualityChecks([
      { command: 'pixi run test', critical: true },
      { command: 'pixi run quality', critical: true },
      { command: 'pixi run lint', critical: true }
    ])
    
    const failed = checks.filter(c => !c.passed)
    
    if (failed.length > 0) {
      // Emergency fix attempt
      const fixResult = await this.runEmergencyFix()
      
      if (fixResult.success) {
        return await this.revalidateQuality()
      }
      
      return {
        passed: false,
        violations: failed.map(f => f.error),
        emergencyFixAttempted: true,
        commitBlocked: true
      }
    }
    
    return { passed: true, violations: [], commitBlocked: false }
  }
  
  // Emergency fix execution
  async runEmergencyFix(): Promise<EmergencyFixResult> {
    
    if (await this.fileExists('scripts/fix-lint-violations.sh')) {
      const result = await this.runCommand('./scripts/fix-lint-violations.sh')
      return { 
        success: result.includes('Fixed') || result.includes('Success'),
        method: 'emergency_script',
        output: result
      }
    }
    
    return { success: false, method: 'none_available' }
  }
}
```

## GPG-Signed Commits with Claude Attribution

```typescript
interface GPGCommitOperations {
  // Standard Claude Code commit format
  async createClaudeAttributedCommit(
    repoPath: string,
    message: string,
    taskId?: string
  ): Promise<CommitResult> {
    
    // Quality gates first
    const qualityResult = await this.enforcePreCommitQuality()
    if (!qualityResult.passed) {
      throw new Error(`Quality gates failed: ${qualityResult.violations.join(', ')}`)
    }
    
    // Build standardized message
    const standardMessage = this.buildClaudeCommitMessage(message, taskId)
    
    try {
      // Attempt GPG-signed commit
      await this.mcpGitCommit(repoPath, standardMessage, true)
      
      return {
        success: true,
        gpgSigned: true,
        message: standardMessage,
        taskId
      }
      
    } catch (error) {
      if (this.isGpgError(error)) {
        // Fallback to unsigned with note
        const fallbackMessage = standardMessage + '\n\n[GPG signing unavailable in environment]'
        await this.mcpGitCommit(repoPath, fallbackMessage, false)
        
        return {
          success: true,
          gpgSigned: false,
          message: fallbackMessage,
          taskId,
          warning: 'GPG signing failed, committed unsigned'
        }
      }
      throw error
    }
  }
  
  // Build Claude Code standard commit message
  buildClaudeCommitMessage(message: string, taskId?: string): string {
    const taskRef = taskId ? ` Task ${taskId} -` : ''
    
    return `feat: implement${taskRef} ${message}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>`
  }
}
```

## Test Validation Framework

```typescript
interface GitWorkflowTesting {
  // Validate git-workflow-specialist functionality
  async validateGitWorkflowImplementation(): Promise<ValidationResult> {
    
    const testResults = await Promise.all([
      this.testMcpCompliance(),
      this.testStrategicBashFallbacks(),
      this.testConflictResolution(),
      this.testQualityGateIntegration(),
      this.testTaskMasterSync()
    ])
    
    const passed = testResults.filter(r => r.passed).length
    const total = testResults.length
    
    return {
      passed: passed === total,
      successRate: passed / total,
      testResults,
      compliance: {
        mcpUsage: await this.measureMcpUsage(),
        qualityMaintenance: await this.validateQualityMaintenance(),
        frameworkAdherence: await this.checkFrameworkCompliance()
      }
    }
  }
  
  // Test MCP compliance (95% target)
  async testMcpCompliance(): Promise<TestResult> {
    const operations = [
      'git_status', 'git_add', 'git_commit', 'git_merge', 
      'git_push', 'git_pull', 'git_branch_ops'
    ]
    
    let mcpSuccessful = 0
    let bashFallbacks = 0
    
    for (const op of operations) {
      const result = await this.testOperation(op)
      if (result.method === 'mcp') mcpSuccessful++
      if (result.method === 'bash') bashFallbacks++
    }
    
    const mcpRatio = mcpSuccessful / (mcpSuccessful + bashFallbacks)
    
    return {
      test: 'mcp_compliance',
      passed: mcpRatio >= 0.95,
      metrics: { mcpRatio, target: 0.95 },
      details: `MCP usage: ${mcpRatio * 100}%, Bash fallbacks: ${bashFallbacks}`
    }
  }
}
```

This completes the git-workflow-specialist implementation with full TaskMaster integration, quality gate enforcement, and framework compliance validation.