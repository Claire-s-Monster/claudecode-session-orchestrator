# Complex Git Staging Operations Handler

## Overview

Advanced staging operations for git-workflow-specialist, handling selective changes, file moves, renames, and complex multi-file scenarios with MCP-first approach and strategic fallbacks.

## Core Staging Capabilities

### 1. Selective File Staging

```typescript
interface SelectiveStaging {
  // File-level selective staging (MCP preferred)
  async stageSelectedFiles(
    repoPath: string,
    selections: FileSelection[]
  ): Promise<StagingResult> {
    
    const mcpResults: StagingResult[] = []
    const bashFallbacks: FileSelection[] = []
    
    for (const selection of selections) {
      try {
        // Attempt MCP staging first
        const result = await this.mcpGitAdd(repoPath, [selection.file])
        mcpResults.push({
          file: selection.file,
          method: 'mcp',
          success: true,
          hunksStaged: 'all'
        })
        
      } catch (error) {
        if (this.requiresHunkLevelStaging(selection)) {
          bashFallbacks.push(selection)
        } else {
          throw error
        }
      }
    }
    
    // Handle hunk-level staging with strategic Bash
    if (bashFallbacks.length > 0) {
      const bashResults = await this.handleHunkLevelStaging(repoPath, bashFallbacks)
      mcpResults.push(...bashResults)
    }
    
    return this.consolidateStagingResults(mcpResults)
  }
  
  // Hunk-level staging (Strategic Bash required)
  async handleHunkLevelStaging(
    repoPath: string,
    selections: FileSelection[]
  ): Promise<StagingResult[]> {
    
    const results: StagingResult[] = []
    
    for (const selection of selections) {
      if (selection.hunks && selection.hunks.length > 0) {
        // Use strategic Bash for interactive staging
        const result = await this.strategicBashInteractiveAdd(
          repoPath,
          selection.file,
          selection.hunks
        )
        
        results.push({
          file: selection.file,
          method: 'strategic_bash',
          success: result.success,
          hunksStaged: result.hunksProcessed
        })
      }
    }
    
    return results
  }
}
```

### 2. File Operation Staging

```typescript
interface FileOperationStaging {
  // Handle file moves with proper staging
  async stageFileMove(
    repoPath: string,
    oldPath: string,
    newPath: string
  ): Promise<StagingResult> {
    
    try {
      // Stage both old and new paths for move detection
      await this.mcpGitAdd(repoPath, [oldPath, newPath])
      
      // Verify move was detected
      const statusResult = await this.mcpGitStatus(repoPath)
      const moveDetected = this.isMoveDetected(statusResult, oldPath, newPath)
      
      return {
        operation: 'move',
        oldPath,
        newPath,
        method: 'mcp',
        success: true,
        moveDetected
      }
      
    } catch (error) {
      // Fallback: Manual move staging
      return await this.handleMoveWithBash(repoPath, oldPath, newPath)
    }
  }
  
  // Handle file renames with similarity detection
  async stageFileRename(
    repoPath: string,
    oldName: string,
    newName: string,
    similarityThreshold: number = 50
  ): Promise<StagingResult> {
    
    try {
      // Stage both files
      await this.mcpGitAdd(repoPath, [oldName, newName])
      
      // Check if git detected the rename
      const diffResult = await this.mcpGitDiffStaged(repoPath)
      const renameDetected = this.isRenameDetected(diffResult, oldName, newName)
      
      if (!renameDetected && similarityThreshold > 0) {
        // Force similarity detection with strategic Bash
        return await this.forceRenameDetection(
          repoPath, 
          oldName, 
          newName, 
          similarityThreshold
        )
      }
      
      return {
        operation: 'rename',
        oldName,
        newName,
        method: 'mcp',
        success: true,
        renameDetected
      }
      
    } catch (error) {
      throw new Error(`File rename staging failed: ${error.message}`)
    }
  }
  
  // Handle file deletions
  async stageFileDeletion(
    repoPath: string,
    files: string[]
  ): Promise<StagingResult> {
    
    try {
      // Add deleted files to stage the deletion
      await this.mcpGitAdd(repoPath, files)
      
      // Verify deletions were staged
      const stagedDiff = await this.mcpGitDiffStaged(repoPath)
      const deletionsStaged = this.verifyDeletionsStaged(stagedDiff, files)
      
      return {
        operation: 'delete',
        files,
        method: 'mcp',
        success: true,
        deletionsStaged
      }
      
    } catch (error) {
      throw new Error(`File deletion staging failed: ${error.message}`)
    }
  }
}
```

### 3. Complex Multi-File Scenarios

```typescript
interface ComplexStagingScenarios {
  // Handle mixed file operations in single staging session
  async stageComplexChanges(
    repoPath: string,
    scenario: ComplexStagingScenario
  ): Promise<ComplexStagingResult> {
    
    const results: StagingResult[] = []
    const errors: StagingError[] = []
    
    // Process operations in dependency order
    const orderedOps = this.orderOperationsByDependency(scenario.operations)
    
    for (const operation of orderedOps) {
      try {
        let result: StagingResult
        
        switch (operation.type) {
          case 'selective_add':
            result = await this.stageSelectedFiles(repoPath, operation.selections)
            break
            
          case 'file_move':
            result = await this.stageFileMove(repoPath, operation.oldPath, operation.newPath)
            break
            
          case 'file_rename':
            result = await this.stageFileRename(repoPath, operation.oldName, operation.newName)
            break
            
          case 'file_delete':
            result = await this.stageFileDeletion(repoPath, operation.files)
            break
            
          case 'directory_restructure':
            result = await this.stageDirectoryRestructure(repoPath, operation.restructure)
            break
            
          default:
            throw new Error(`Unknown staging operation: ${operation.type}`)
        }
        
        results.push(result)
        
      } catch (error) {
        errors.push({
          operation: operation.type,
          error: error.message,
          recoverable: this.isRecoverableError(error)
        })
        
        // Stop on non-recoverable errors
        if (!this.isRecoverableError(error)) {
          break
        }
      }
    }
    
    return {
      scenario: scenario.name,
      operations: results,
      errors,
      success: errors.length === 0,
      mcpUsageRatio: this.calculateMcpUsage(results)
    }
  }
  
  // Directory restructuring with move detection
  async stageDirectoryRestructure(
    repoPath: string,
    restructure: DirectoryRestructure
  ): Promise<StagingResult> {
    
    const moveOperations: FileMoveOperation[] = []
    
    // Build move operations from restructure plan
    for (const mapping of restructure.fileMappings) {
      moveOperations.push({
        type: 'file_move',
        oldPath: mapping.from,
        newPath: mapping.to
      })
    }
    
    // Execute moves in batches to avoid conflicts
    const batchSize = 10
    const batches = this.chunkArray(moveOperations, batchSize)
    const batchResults: StagingResult[] = []
    
    for (const batch of batches) {
      const batchResult = await this.stageBatchMoves(repoPath, batch)
      batchResults.push(batchResult)
      
      // Verify batch before proceeding
      if (!batchResult.success) {
        throw new Error(`Directory restructure failed at batch: ${batchResult.error}`)
      }
    }
    
    return {
      operation: 'directory_restructure',
      batches: batchResults.length,
      totalMoves: moveOperations.length,
      method: 'mcp_batched',
      success: true
    }
  }
}
```

### 4. Interactive Staging with Strategic Bash

```typescript
interface InteractiveStaging {
  // Strategic Bash for hunk-level staging
  async strategicBashInteractiveAdd(
    repoPath: string,
    file: string,
    hunks: HunkSelection[]
  ): Promise<InteractiveStagingResult> {
    
    // Validate strategic Bash usage allowance
    if (!this.canUseStrategicBash()) {
      throw new Error('Strategic Bash usage limit exceeded for interactive staging')
    }
    
    // Build interactive staging responses
    const responses = this.buildInteractiveResponses(hunks)
    
    try {
      // Execute git add -p with automated responses
      const command = `git add -p ${file}`
      const result = await this.executeInteractiveCommand(command, responses)
      
      // Log strategic usage
      await this.logStrategicUsage('add -p', 'hunk-level staging required')
      
      return {
        file,
        method: 'strategic_bash',
        success: true,
        hunksProcessed: hunks.length,
        responses: responses.length
      }
      
    } catch (error) {
      throw new Error(`Interactive staging failed: ${error.message}`)
    }
  }
  
  // Build automated responses for git add -p
  private buildInteractiveResponses(hunks: HunkSelection[]): string[] {
    const responses: string[] = []
    
    for (const hunk of hunks) {
      if (hunk.include) {
        responses.push('y') // Yes, stage this hunk
      } else {
        responses.push('n') // No, skip this hunk
      }
    }
    
    responses.push('q') // Quit interactive mode
    return responses
  }
  
  // Execute interactive command with automated input
  private async executeInteractiveCommand(
    command: string,
    responses: string[]
  ): Promise<string> {
    
    // Create input stream for automated responses
    const input = responses.join('\n') + '\n'
    
    // Execute with input piping (conceptual - actual implementation would vary)
    const result = await this.executeWithInput(command, input)
    
    return result.output
  }
}
```

### 5. Staging Validation and Verification

```typescript
interface StagingValidation {
  // Verify staging results match intentions
  async validateStagingResults(
    repoPath: string,
    expectedResults: ExpectedStagingResult[]
  ): Promise<ValidationResult> {
    
    // Get current staging area status
    const stagedDiff = await this.mcpGitDiffStaged(repoPath)
    const stagedFiles = this.parseStagedFiles(stagedDiff)
    
    const validationErrors: ValidationError[] = []
    
    for (const expected of expectedResults) {
      const validation = await this.validateSingleResult(expected, stagedFiles)
      
      if (!validation.valid) {
        validationErrors.push({
          expected: expected.operation,
          actual: validation.actualState,
          error: validation.error
        })
      }
    }
    
    return {
      valid: validationErrors.length === 0,
      errors: validationErrors,
      stagedFiles: stagedFiles.length,
      verificationMethod: 'mcp_diff_analysis'
    }
  }
  
  // Validate individual staging operation
  private async validateSingleResult(
    expected: ExpectedStagingResult,
    stagedFiles: StagedFileInfo[]
  ): Promise<SingleValidationResult> {
    
    switch (expected.operation) {
      case 'file_add':
        return this.validateFileAddition(expected, stagedFiles)
        
      case 'file_move':
        return this.validateFileMove(expected, stagedFiles)
        
      case 'file_rename':
        return this.validateFileRename(expected, stagedFiles)
        
      case 'file_delete':
        return this.validateFileDeletion(expected, stagedFiles)
        
      case 'hunk_selection':
        return this.validateHunkSelection(expected, stagedFiles)
        
      default:
        return {
          valid: false,
          error: `Unknown operation validation: ${expected.operation}`
        }
    }
  }
  
  // Validate file move was detected correctly
  private validateFileMove(
    expected: ExpectedStagingResult,
    stagedFiles: StagedFileInfo[]
  ): SingleValidationResult {
    
    const moveEntry = stagedFiles.find(f => 
      f.operation === 'rename' && 
      f.oldPath === expected.oldPath && 
      f.newPath === expected.newPath
    )
    
    if (!moveEntry) {
      // Check if staged as separate add/delete
      const deleteEntry = stagedFiles.find(f => 
        f.operation === 'delete' && f.path === expected.oldPath
      )
      const addEntry = stagedFiles.find(f => 
        f.operation === 'add' && f.path === expected.newPath
      )
      
      if (deleteEntry && addEntry) {
        return {
          valid: true,
          actualState: 'separate_add_delete',
          note: 'Move staged as separate operations (acceptable)'
        }
      }
      
      return {
        valid: false,
        error: 'File move not detected in staging area',
        actualState: 'missing'
      }
    }
    
    return {
      valid: true,
      actualState: 'move_detected',
      similarity: moveEntry.similarity
    }
  }
}
```

## Usage Patterns and Examples

### Pattern 1: Refactoring with Selective Staging

```typescript
// Scenario: Stage core changes, exclude debug code
async stageRefactoringChanges(repoPath: string): Promise<StagingResult> {
  
  const selections: FileSelection[] = [
    {
      file: 'src/core/module.ts',
      hunks: [
        { startLine: 10, endLine: 50, include: true },   // Core logic changes
        { startLine: 51, endLine: 55, include: false }   // Debug console.log
      ]
    },
    {
      file: 'src/types/interfaces.ts',
      hunks: 'all' // Stage entire file
    }
  ]
  
  return await this.stageSelectedFiles(repoPath, selections)
}
```

### Pattern 2: Directory Reorganization

```typescript
// Scenario: Move files to new directory structure
async stageDirectoryReorganization(repoPath: string): Promise<StagingResult> {
  
  const restructure: DirectoryRestructure = {
    name: 'components_reorganization',
    fileMappings: [
      { from: 'src/components/Button.tsx', to: 'src/ui/components/Button.tsx' },
      { from: 'src/components/Modal.tsx', to: 'src/ui/components/Modal.tsx' },
      { from: 'src/utils/helpers.ts', to: 'src/shared/utils/helpers.ts' }
    ]
  }
  
  return await this.stageDirectoryRestructure(repoPath, restructure)
}
```

### Pattern 3: Complex Mixed Operations

```typescript
// Scenario: Feature implementation with file operations
async stageFeatureImplementation(repoPath: string): Promise<ComplexStagingResult> {
  
  const scenario: ComplexStagingScenario = {
    name: 'user_authentication_feature',
    operations: [
      {
        type: 'selective_add',
        selections: [
          { file: 'src/auth/service.ts', hunks: 'all' },
          { file: 'src/auth/types.ts', hunks: 'all' }
        ]
      },
      {
        type: 'file_move',
        oldPath: 'src/old-auth.ts',
        newPath: 'src/auth/legacy.ts'
      },
      {
        type: 'file_delete',
        files: ['src/deprecated-auth.ts', 'src/temp-auth-test.ts']
      }
    ]
  }
  
  return await this.stageComplexChanges(repoPath, scenario)
}
```

## Framework Compliance and Monitoring

### MCP Usage Tracking

```yaml
staging_operations_mcp_compliance:
  target_mcp_ratio: 95_percent
  
  mcp_preferred_operations:
    - file_level_staging: mcp__git__git_add
    - status_checking: mcp__git__git_status
    - diff_analysis: mcp__git__git_diff_staged
    - move_detection: mcp__git__git_add (both paths)
  
  strategic_bash_scenarios:
    - hunk_level_staging: git add -p
    - interactive_operations: git add -i
    - similarity_tuning: git add with -M flag
    - complex_renames: git mv with detection
```

### Quality Integration

```yaml
staging_quality_gates:
  pre_staging_validation:
    - verify_file_existence
    - check_file_permissions
    - validate_operation_safety
  
  post_staging_verification:
    - confirm_staging_intentions_met
    - verify_no_unintended_changes
    - validate_move_rename_detection
    - check_hunk_selection_accuracy
  
  framework_compliance:
    - maintain_taskmaster_sync
    - preserve_quality_status
    - log_strategic_bash_usage
    - track_mcp_usage_ratios
```

This complex staging operations handler enables precise control over git staging while maintaining framework compliance and providing strategic fallbacks for operations requiring interactive interfaces or advanced git functionality.