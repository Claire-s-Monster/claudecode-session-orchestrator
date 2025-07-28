/**
 * git-workflow-specialist Sub-Agent Implementation
 * 
 * Handles complex git operations with 95% MCP compliance and strategic Bash fallback.
 * Maintains framework compliance and TaskMaster integration.
 */

interface GitWorkflowContext {
  projectRoot: string
  currentTask?: {
    id: string
    title: string
    priority: string
  }
  qualityStatus: {
    tests: 'passing' | 'failing'
    lint: 'clean' | 'violations'
    ci: 'green' | 'red'
  }
  mcpUsageRatio: number // Target: 0.95
}

interface GitOperationResult {
  success: boolean
  method: 'mcp' | 'strategic_bash'
  output: string
  contextTokensUsed: number
  qualityStatus: 'maintained' | 'degraded'
}

class GitWorkflowSpecialist {
  private mcpUsageCount = 0
  private bashUsageCount = 0
  private readonly MCP_TARGET_RATIO = 0.95

  constructor(private context: GitWorkflowContext) {}

  /**
   * Primary MCP Git Operations (95% target)
   */
  async mcpGitStatus(repoPath: string): Promise<GitOperationResult> {
    try {
      this.incrementMcpUsage()
      
      const result = await this.callMcpTool('mcp__git__git_status', {
        repo_path: repoPath
      })
      
      return {
        success: true,
        method: 'mcp',
        output: result,
        contextTokensUsed: this.estimateTokenUsage(result),
        qualityStatus: 'maintained'
      }
      
    } catch (error) {
      return await this.handleMcpFailure('git_status', error)
    }
  }

  async mcpGitAdd(repoPath: string, files: string[]): Promise<GitOperationResult> {
    try {
      this.incrementMcpUsage()
      
      const result = await this.callMcpTool('mcp__git__git_add', {
        repo_path: repoPath,
        files: files
      })
      
      return {
        success: true,
        method: 'mcp',
        output: result,
        contextTokensUsed: this.estimateTokenUsage(result),
        qualityStatus: 'maintained'
      }
      
    } catch (error) {
      return await this.handleMcpFailure('git_add', error)
    }
  }

  async mcpGitCommit(
    repoPath: string, 
    message: string, 
    gpgSign: boolean = true
  ): Promise<GitOperationResult> {
    try {
      this.incrementMcpUsage()
      
      // Enforce quality gates before commit
      const qualityCheck = await this.enforceQualityGates()
      if (!qualityCheck.passed) {
        throw new Error(`Quality gates failed: ${qualityCheck.violations.join(', ')}`)
      }
      
      const result = await this.callMcpTool('mcp__git__git_commit', {
        repo_path: repoPath,
        message: message,
        gpg_sign: gpgSign
      })
      
      // Update TaskMaster after successful commit
      if (this.context.currentTask) {
        await this.updateTaskProgress(this.context.currentTask.id, 'commit_completed')
      }
      
      return {
        success: true,
        method: 'mcp',
        output: result,
        contextTokensUsed: this.estimateTokenUsage(result),
        qualityStatus: 'maintained'
      }
      
    } catch (error) {
      return await this.handleMcpFailure('git_commit', error)
    }
  }

  async mcpGitMerge(
    repoPath: string, 
    sourceBranch: string, 
    strategy?: string
  ): Promise<GitOperationResult> {
    try {
      this.incrementMcpUsage()
      
      const result = await this.callMcpTool('mcp__git__git_merge', {
        repo_path: repoPath,
        source_branch: sourceBranch,
        strategy: strategy || 'merge'
      })
      
      return {
        success: true,
        method: 'mcp',
        output: result,
        contextTokensUsed: this.estimateTokenUsage(result),
        qualityStatus: 'maintained'
      }
      
    } catch (error) {
      return await this.handleMcpFailure('git_merge', error)
    }
  }

  /**
   * Strategic Bash Fallback (5% allowance)
   */
  async strategicBashGitOperation(
    operation: string,
    args: string[]
  ): Promise<GitOperationResult> {
    
    // Verify we're within 5% Bash allowance
    if (!this.canUseStrategicBash()) {
      throw new Error('Strategic Bash usage limit exceeded (5% target)')
    }
    
    this.incrementBashUsage()
    
    try {
      const command = `git ${operation} ${args.join(' ')}`
      const result = await this.callBashTool(command)
      
      // Log strategic usage for monitoring
      await this.logStrategicBashUsage(operation, 'fallback_successful')
      
      return {
        success: true,
        method: 'strategic_bash',
        output: result,
        contextTokensUsed: this.estimateTokenUsage(result),
        qualityStatus: 'maintained'
      }
      
    } catch (error) {
      await this.logStrategicBashUsage(operation, 'fallback_failed')
      throw error
    }
  }

  /**
   * Complex Staging Operations
   */
  async handleComplexStaging(
    repoPath: string,
    operations: StagingOperation[]
  ): Promise<GitOperationResult> {
    
    const results: GitOperationResult[] = []
    
    for (const op of operations) {
      switch (op.type) {
        case 'selective_add':
          const addResult = await this.handleSelectiveAdd(repoPath, op.files, op.hunks)
          results.push(addResult)
          break
          
        case 'file_move':
          const moveResult = await this.handleFileMove(repoPath, op.oldPath, op.newPath)
          results.push(moveResult)
          break
          
        case 'file_delete':
          const deleteResult = await this.mcpGitAdd(repoPath, [op.path])
          results.push(deleteResult)
          break
      }
    }
    
    const allSuccessful = results.every(r => r.success)
    const totalTokens = results.reduce((sum, r) => sum + r.contextTokensUsed, 0)
    
    return {
      success: allSuccessful,
      method: results[0]?.method || 'mcp',
      output: results.map(r => r.output).join('\n'),
      contextTokensUsed: totalTokens,
      qualityStatus: allSuccessful ? 'maintained' : 'degraded'
    }
  }

  private async handleSelectiveAdd(
    repoPath: string,
    files: string[],
    hunks?: HunkSelection[]
  ): Promise<GitOperationResult> {
    
    try {
      // Attempt MCP first
      return await this.mcpGitAdd(repoPath, files)
      
    } catch (error) {
      if (this.isMcpLimitation(error) && hunks) {
        // Strategic Bash for interactive staging
        return await this.strategicBashGitOperation('add', ['-p', ...files])
      }
      throw error
    }
  }

  /**
   * Merge Conflict Resolution
   */
  async resolveConflicts(
    repoPath: string,
    strategy: ConflictStrategy = 'systematic'
  ): Promise<ConflictResolutionResult> {
    
    // Detect conflicts using MCP
    const statusResult = await this.mcpGitStatus(repoPath)
    const conflicts = this.parseConflictsFromStatus(statusResult.output)
    
    if (conflicts.length === 0) {
      return { resolved: 0, strategy: 'none_detected' }
    }
    
    // Handle CLAUDE.md cycles specifically
    const claudeMdConflicts = conflicts.filter(c => c.file.includes('CLAUDE.md'))
    if (claudeMdConflicts.length > 0) {
      return await this.resolveCLAUDEMdCycles(repoPath, claudeMdConflicts)
    }
    
    // Standard conflict resolution
    return await this.resolveStandardConflicts(repoPath, conflicts, strategy)
  }

  private async resolveCLAUDEMdCycles(
    repoPath: string,
    conflicts: ConflictInfo[]
  ): Promise<ConflictResolutionResult> {
    
    let resolvedCount = 0
    
    for (const conflict of conflicts) {
      // Read conflict file
      const content = await this.readFile(conflict.file)
      
      // Detect cycle patterns
      if (this.isCyclicCLAUDEMdConflict(content)) {
        // Apply systematic resolution (prefer newer, non-duplicate content)
        const resolved = this.resolveCLAUDEMdCycle(content)
        await this.writeFile(conflict.file, resolved)
        
        // Stage the resolution
        await this.mcpGitAdd(repoPath, [conflict.file])
        resolvedCount++
      }
    }
    
    return {
      resolved: resolvedCount,
      strategy: 'claude_md_cycle',
      details: `Resolved ${resolvedCount} CLAUDE.md cyclic conflicts`
    }
  }

  /**
   * TaskMaster AI Integration
   */
  async updateTaskProgress(
    taskId: string,
    operation: string,
    details?: string
  ): Promise<void> {
    
    try {
      await this.callMcpTool('mcp__task-master-ai__update_task', {
        projectRoot: this.context.projectRoot,
        id: taskId,
        prompt: `Git operation: ${operation}${details ? ` - ${details}` : ''}`
      })
      
    } catch (error) {
      // Log but don't fail operation for TaskMaster sync issues
      console.warn(`TaskMaster sync failed: ${error.message}`)
    }
  }

  /**
   * Quality Gate Enforcement
   */
  async enforceQualityGates(): Promise<QualityGateResult> {
    
    const checks = await Promise.all([
      this.runQualityCheck('pixi run test'),
      this.runQualityCheck('pixi run quality'),
      this.runQualityCheck('pixi run lint')
    ])
    
    const failed = checks.filter(c => !c.passed)
    
    if (failed.length > 0) {
      // Attempt emergency fix
      const fixResult = await this.runEmergencyFix()
      
      if (fixResult.success) {
        // Re-run failed checks
        return await this.revalidateQuality(failed.map(f => f.command))
      }
      
      return {
        passed: false,
        violations: failed.map(f => f.error),
        emergencyFixAttempted: true
      }
    }
    
    return { passed: true, violations: [] }
  }

  private async runEmergencyFix(): Promise<{ success: boolean }> {
    
    try {
      const scriptExists = await this.fileExists('scripts/fix-lint-violations.sh')
      
      if (scriptExists) {
        const result = await this.callBashTool('./scripts/fix-lint-violations.sh')
        return { success: result.includes('Fixed') || result.includes('Success') }
      }
      
      return { success: false }
      
    } catch (error) {
      return { success: false }
    }
  }

  /**
   * GPG-Signed Commits with Claude Attribution
   */
  async createStandardizedCommit(
    repoPath: string,
    message: string,
    taskId?: string
  ): Promise<GitOperationResult> {
    
    const standardizedMessage = this.buildClaudeCommitMessage(message, taskId)
    
    try {
      // Attempt GPG-signed commit
      return await this.mcpGitCommit(repoPath, standardizedMessage, true)
      
    } catch (error) {
      if (this.isGpgSigningError(error)) {
        // Fallback to unsigned commit with note
        const fallbackMessage = standardizedMessage + '\n\n[GPG signing unavailable in environment]'
        return await this.mcpGitCommit(repoPath, fallbackMessage, false)
      }
      throw error
    }
  }

  private buildClaudeCommitMessage(message: string, taskId?: string): string {
    const taskRef = taskId ? ` Task ${taskId} -` : ''
    
    return `feat: implement${taskRef} ${message}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>`
  }

  /**
   * Error Handling and MCP Limitation Management
   */
  private async handleMcpFailure(
    operation: string,
    error: Error
  ): Promise<GitOperationResult> {
    
    // Log MCP limitation for tracking
    await this.logMcpLimitation(operation, error.message)
    
    // Check for strategic fallback availability
    if (this.hasStrategicFallback(operation) && this.canUseStrategicBash()) {
      try {
        return await this.executeStrategicFallback(operation, error)
      } catch (fallbackError) {
        // Both MCP and fallback failed
        throw new Error(`MCP and strategic fallback failed for ${operation}`)
      }
    }
    
    // No fallback available - escalate
    throw new Error(`MCP limitation without fallback: ${operation} - ${error.message}`)
  }

  private async logMcpLimitation(operation: string, error: string): Promise<void> {
    const logEntry = {
      timestamp: new Date().toISOString(),
      operation,
      error,
      agent: 'git-workflow-specialist',
      mcpUsageRatio: this.getCurrentMcpRatio()
    }
    
    // Log to monitoring system for MCP improvement feedback
    console.log(`MCP Limitation: ${JSON.stringify(logEntry)}`)
  }

  /**
   * Usage Ratio Monitoring
   */
  private incrementMcpUsage(): void {
    this.mcpUsageCount++
  }

  private incrementBashUsage(): void {
    this.bashUsageCount++
  }

  private getCurrentMcpRatio(): number {
    const total = this.mcpUsageCount + this.bashUsageCount
    return total > 0 ? this.mcpUsageCount / total : 1.0
  }

  private canUseStrategicBash(): boolean {
    const currentRatio = this.getCurrentMcpRatio()
    return currentRatio >= this.MCP_TARGET_RATIO
  }

  /**
   * Utility Methods
   */
  private async callMcpTool(toolName: string, params: any): Promise<string> {
    // Implementation would call actual MCP tool
    throw new Error('MCP tool integration not implemented in this specification')
  }

  private async callBashTool(command: string): Promise<string> {
    // Implementation would execute Bash command
    throw new Error('Bash tool integration not implemented in this specification')
  }

  private estimateTokenUsage(content: string): number {
    // Rough estimation: 4 characters per token
    return Math.ceil(content.length / 4)
  }

  private isMcpLimitation(error: Error): boolean {
    const mcpLimitationPatterns = [
      'MCP tool unavailable',
      'Interactive operation not supported',
      'Complex git operation limitation'
    ]
    
    return mcpLimitationPatterns.some(pattern => 
      error.message.includes(pattern)
    )
  }

  private isGpgSigningError(error: Error): boolean {
    return error.message.includes('gpg') || 
           error.message.includes('signing') ||
           error.message.includes('secret key')
  }
}

/**
 * Supporting Types
 */
interface StagingOperation {
  type: 'selective_add' | 'file_move' | 'file_delete'
  files?: string[]
  path?: string
  oldPath?: string
  newPath?: string
  hunks?: HunkSelection[]
}

interface HunkSelection {
  file: string
  startLine: number
  endLine: number
  include: boolean
}

interface ConflictInfo {
  file: string
  type: 'merge' | 'rebase' | 'cherry-pick'
  markers: ConflictMarker[]
}

interface ConflictMarker {
  start: number
  middle: number
  end: number
  content: string
}

type ConflictStrategy = 'systematic' | 'ours' | 'theirs' | 'manual'

interface ConflictResolutionResult {
  resolved: number
  strategy: string
  details?: string
}

interface QualityGateResult {
  passed: boolean
  violations: string[]
  emergencyFixAttempted?: boolean
}

export { GitWorkflowSpecialist, GitWorkflowContext, GitOperationResult }