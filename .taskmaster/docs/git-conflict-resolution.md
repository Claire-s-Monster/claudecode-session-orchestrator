# Git Merge Conflict Resolution Workflows

## Overview

Systematic merge conflict detection and resolution for git-workflow-specialist, with specialized handling for CLAUDE.md cycles and framework-specific conflicts.

## Conflict Detection and Classification

### 1. Automated Conflict Detection

```typescript
interface ConflictDetection {
  // Primary conflict detection using MCP
  async detectConflicts(repoPath: string): Promise<ConflictAnalysis> {
    
    // Get repository status
    const statusResult = await this.mcpGitStatus(repoPath)
    const conflicts = this.parseConflictsFromStatus(statusResult)
    
    if (conflicts.length === 0) {
      return { hasConflicts: false, conflicts: [] }
    }
    
    // Analyze conflict types and patterns
    const analysis = await this.analyzeConflictPatterns(conflicts)
    
    return {
      hasConflicts: true,
      conflicts,
      patterns: analysis.patterns,
      claudeMdCycles: analysis.claudeMdCycles,
      resolutionStrategy: analysis.recommendedStrategy
    }
  }
  
  // Parse conflict information from git status
  private parseConflictsFromStatus(statusOutput: string): ConflictInfo[] {
    const conflicts: ConflictInfo[] = []
    const lines = statusOutput.split('\n')
    
    for (const line of lines) {
      if (line.includes('both modified:') || line.includes('added by us:') || line.includes('added by them:')) {
        const filePath = line.replace(/^\s*(both modified:|added by us:|added by them:)\s*/, '')
        
        conflicts.push({
          file: filePath,
          type: this.determineConflictType(line),
          status: 'unresolved',
          markers: [] // Will be populated by detailed analysis
        })
      }
    }
    
    return conflicts
  }
  
  // Analyze conflict patterns for systematic resolution
  async analyzeConflictPatterns(conflicts: ConflictInfo[]): Promise<ConflictPatternAnalysis> {
    
    const patterns: ConflictPattern[] = []
    const claudeMdCycles: CLAUDEMdCycle[] = []
    
    for (const conflict of conflicts) {
      // Read conflict file content
      const content = await this.readConflictFile(conflict.file)
      conflict.markers = this.parseConflictMarkers(content)
      
      // Check for CLAUDE.md cycles
      if (conflict.file.includes('CLAUDE.md')) {
        const cycle = this.detectCLAUDEMdCycle(content, conflict.markers)
        if (cycle) {
          claudeMdCycles.push(cycle)
        }
      }
      
      // Detect other patterns
      const pattern = this.detectConflictPattern(content, conflict.markers)
      if (pattern) {
        patterns.push(pattern)
      }
    }
    
    return {
      patterns,
      claudeMdCycles,
      recommendedStrategy: this.determineResolutionStrategy(patterns, claudeMdCycles)
    }
  }
}
```

### 2. CLAUDE.md Cycle Detection

```typescript
interface CLAUDEMdCycleDetection {
  // Detect cyclical conflict patterns in CLAUDE.md
  detectCLAUDEMdCycle(
    content: string,
    markers: ConflictMarker[]
  ): CLAUDEMdCycle | null {
    
    for (const marker of markers) {
      const ourSection = this.extractSection(content, marker.start, marker.middle)
      const theirSection = this.extractSection(content, marker.middle, marker.end)
      
      // Check for cyclical patterns
      if (this.isCyclicalUpdate(ourSection, theirSection)) {
        return {
          type: 'cyclical_update',
          ourVersion: ourSection,
          theirVersion: theirSection,
          detectedPattern: this.analyzeCyclePattern(ourSection, theirSection),
          resolutionStrategy: this.determineCycleResolution(ourSection, theirSection)
        }
      }
      
      // Check for duplicate content patterns
      if (this.isDuplicateContent(ourSection, theirSection)) {
        return {
          type: 'duplicate_content',
          ourVersion: ourSection,
          theirVersion: theirSection,
          duplicateElements: this.findDuplicateElements(ourSection, theirSection),
          resolutionStrategy: 'deduplicate_and_merge'
        }
      }
      
      // Check for version conflict patterns
      if (this.isVersionConflict(ourSection, theirSection)) {
        return {
          type: 'version_conflict',
          ourVersion: ourSection,
          theirVersion: theirSection,
          versionComparison: this.compareVersions(ourSection, theirSection),
          resolutionStrategy: 'prefer_newer_systematic'
        }
      }
    }
    
    return null
  }
  
  // Analyze specific cycle patterns
  private analyzeCyclePattern(ourSection: string, theirSection: string): CyclePattern {
    
    // Framework update cycles
    if (this.isFrameworkUpdateCycle(ourSection, theirSection)) {
      return {
        type: 'framework_update',
        description: 'Conflicting framework configuration updates',
        commonElements: this.findCommonFrameworkElements(ourSection, theirSection),
        differences: this.findFrameworkDifferences(ourSection, theirSection)
      }
    }
    
    // Instruction addition cycles
    if (this.isInstructionAdditionCycle(ourSection, theirSection)) {
      return {
        type: 'instruction_addition',
        description: 'Conflicting instruction additions',
        newInstructions: this.extractNewInstructions(ourSection, theirSection),
        conflicts: this.findInstructionConflicts(ourSection, theirSection)
      }
    }
    
    // Tool integration cycles
    if (this.isToolIntegrationCycle(ourSection, theirSection)) {
      return {
        type: 'tool_integration',
        description: 'Conflicting tool integration updates',
        toolUpdates: this.extractToolUpdates(ourSection, theirSection),
        integrationConflicts: this.findToolConflicts(ourSection, theirSection)
      }
    }
    
    return {
      type: 'unknown',
      description: 'Unrecognized cycle pattern',
      rawDifferences: this.extractRawDifferences(ourSection, theirSection)
    }
  }
}
```

## Systematic Conflict Resolution

### 1. CLAUDE.md Cycle Resolution

```typescript
interface CLAUDEMdResolution {
  // Systematic resolution of CLAUDE.md cycles
  async resolveCLAUDEMdCycles(
    repoPath: string,
    cycles: CLAUDEMdCycle[]
  ): Promise<ResolutionResult> {
    
    const resolutions: CycleResolution[] = []
    
    for (const cycle of cycles) {
      let resolution: CycleResolution
      
      switch (cycle.resolutionStrategy) {
        case 'deduplicate_and_merge':
          resolution = await this.deduplicateAndMerge(cycle)
          break
          
        case 'prefer_newer_systematic':
          resolution = await this.preferNewerSystematic(cycle)
          break
          
        case 'merge_framework_updates':
          resolution = await this.mergeFrameworkUpdates(cycle)
          break
          
        case 'consolidate_instructions':
          resolution = await this.consolidateInstructions(cycle)
          break
          
        default:
          resolution = await this.manualResolutionRequired(cycle)
      }
      
      resolutions.push(resolution)
    }
    
    // Apply all resolutions
    const finalContent = await this.applyResolutions(cycles, resolutions)
    await this.writeResolvedContent('CLAUDE.md', finalContent)
    
    // Stage the resolution
    await this.mcpGitAdd(repoPath, ['CLAUDE.md'])
    
    return {
      cyclesResolved: resolutions.length,
      strategy: 'systematic_claude_md',
      requiresReview: resolutions.some(r => r.requiresManualReview)
    }
  }
  
  // Deduplicate and merge conflicting content
  private async deduplicateAndMerge(cycle: CLAUDEMdCycle): Promise<CycleResolution> {
    
    if (!cycle.duplicateElements) {
      throw new Error('No duplicate elements found for deduplication')
    }
    
    const mergedContent = this.buildDeduplicatedContent(
      cycle.ourVersion,
      cycle.theirVersion,
      cycle.duplicateElements
    )
    
    return {
      type: 'deduplicated',
      originalConflict: cycle,
      resolvedContent: mergedContent,
      confidence: 'high',
      requiresManualReview: false
    }
  }
  
  // Prefer newer content with systematic approach
  private async preferNewerSystematic(cycle: CLAUDEMdCycle): Promise<CycleResolution> {
    
    if (!cycle.versionComparison) {
      throw new Error('Version comparison required for systematic preference')
    }
    
    const preferredContent = cycle.versionComparison.newerVersion === 'ours' 
      ? cycle.ourVersion 
      : cycle.theirVersion
      
    // Merge non-conflicting elements from both versions
    const enhancedContent = this.enhanceWithNonConflictingElements(
      preferredContent,
      cycle.versionComparison.newerVersion === 'ours' ? cycle.theirVersion : cycle.ourVersion
    )
    
    return {
      type: 'systematic_preference',
      originalConflict: cycle,
      resolvedContent: enhancedContent,
      confidence: 'medium',
      requiresManualReview: cycle.versionComparison.hasSignificantDifferences
    }
  }
  
  // Merge framework updates systematically
  private async mergeFrameworkUpdates(cycle: CLAUDEMdCycle): Promise<CycleResolution> {
    
    const pattern = cycle.detectedPattern as CyclePattern
    
    if (pattern.type !== 'framework_update') {
      throw new Error('Framework update pattern required')
    }
    
    // Merge framework elements systematically
    const mergedFramework = this.mergeFrameworkElements(
      pattern.commonElements,
      pattern.differences
    )
    
    const resolvedContent = this.rebuildCLAUDEMdWithFramework(
      cycle.ourVersion,
      cycle.theirVersion,
      mergedFramework
    )
    
    return {
      type: 'framework_merge',
      originalConflict: cycle,
      resolvedContent,
      confidence: 'high',
      requiresManualReview: false
    }
  }
}
```

### 2. Standard Conflict Resolution

```typescript
interface StandardConflictResolution {
  // Resolve non-CLAUDE.md conflicts
  async resolveStandardConflicts(
    repoPath: string,
    conflicts: ConflictInfo[],
    strategy: ConflictStrategy
  ): Promise<ConflictResolutionResult> {
    
    const resolutions: StandardResolution[] = []
    
    for (const conflict of conflicts) {
      let resolution: StandardResolution
      
      switch (strategy) {
        case 'systematic':
          resolution = await this.resolveSystematically(conflict)
          break
          
        case 'ours':
          resolution = await this.preferOurs(conflict)
          break
          
        case 'theirs':
          resolution = await this.preferTheirs(conflict)
          break
          
        case 'manual':
          resolution = await this.prepareManualResolution(conflict)
          break
          
        default:
          throw new Error(`Unknown resolution strategy: ${strategy}`)
      }
      
      resolutions.push(resolution)
    }
    
    // Apply resolutions
    await this.applyStandardResolutions(repoPath, resolutions)
    
    return {
      resolved: resolutions.filter(r => r.status === 'resolved').length,
      requiresManual: resolutions.filter(r => r.status === 'manual_required').length,
      strategy,
      files: resolutions.map(r => r.file)
    }
  }
  
  // Systematic resolution based on content analysis
  private async resolveSystematically(conflict: ConflictInfo): Promise<StandardResolution> {
    
    const content = await this.readConflictFile(conflict.file)
    const analysis = await this.analyzeConflictContent(content, conflict.markers)
    
    // Determine best resolution approach
    if (analysis.hasOnlyAdditions) {
      // Merge additions from both sides
      const merged = this.mergeAdditions(analysis.ourChanges, analysis.theirChanges)
      return {
        file: conflict.file,
        strategy: 'merge_additions',
        resolvedContent: merged,
        status: 'resolved',
        confidence: 'high'
      }
    }
    
    if (analysis.hasCompatibleChanges) {
      // Merge compatible changes
      const merged = this.mergeCompatibleChanges(analysis.ourChanges, analysis.theirChanges)
      return {
        file: conflict.file,
        strategy: 'merge_compatible',
        resolvedContent: merged,
        status: 'resolved',
        confidence: 'medium'
      }
    }
    
    if (analysis.hasConflictingLogic) {
      // Requires manual resolution
      return {
        file: conflict.file,
        strategy: 'manual_required',
        reason: 'Conflicting logic changes detected',
        status: 'manual_required',
        confidence: 'low'
      }
    }
    
    // Default to preferring newer changes
    const preferred = analysis.newerChangesSide || 'ours'
    return this.preferSide(conflict, preferred)
  }
  
  // Analyze conflict content for systematic resolution
  private async analyzeConflictContent(
    content: string,
    markers: ConflictMarker[]
  ): Promise<ConflictContentAnalysis> {
    
    const analysis: ConflictContentAnalysis = {
      hasOnlyAdditions: true,
      hasCompatibleChanges: false,
      hasConflictingLogic: false,
      ourChanges: [],
      theirChanges: [],
      newerChangesSide: null
    }
    
    for (const marker of markers) {
      const ourSection = this.extractSection(content, marker.start, marker.middle)
      const theirSection = this.extractSection(content, marker.middle, marker.end)
      
      // Analyze change types
      const ourChangeType = this.analyzeChangeType(ourSection)
      const theirChangeType = this.analyzeChangeType(theirSection)
      
      analysis.ourChanges.push(ourChangeType)
      analysis.theirChanges.push(theirChangeType)
      
      // Check for non-addition changes
      if (ourChangeType.type !== 'addition' || theirChangeType.type !== 'addition') {
        analysis.hasOnlyAdditions = false
      }
      
      // Check for compatible changes
      if (this.areChangesCompatible(ourChangeType, theirChangeType)) {
        analysis.hasCompatibleChanges = true
      }
      
      // Check for conflicting logic
      if (this.areChangesConflicting(ourChangeType, theirChangeType)) {
        analysis.hasConflictingLogic = true
      }
      
      // Determine newer changes
      const newerSide = this.determineNewerChanges(ourChangeType, theirChangeType)
      if (newerSide) {
        analysis.newerChangesSide = newerSide
      }
    }
    
    return analysis
  }
}
```

### 3. Prevention and Recovery

```typescript
interface ConflictPrevention {
  // Analyze potential conflicts before operations
  async analyzeConflictRisk(
    repoPath: string,
    operation: GitOperation
  ): Promise<ConflictRiskAnalysis> {
    
    // Get current state
    const currentStatus = await this.mcpGitStatus(repoPath)
    const currentBranch = this.extractCurrentBranch(currentStatus)
    
    switch (operation.type) {
      case 'merge':
        return await this.analyzeMergeRisk(repoPath, operation.sourceBranch, currentBranch)
        
      case 'rebase':
        return await this.analyzeRebaseRisk(repoPath, operation.targetBranch, currentBranch)
        
      case 'cherry_pick':
        return await this.analyzeCherryPickRisk(repoPath, operation.commitHash)
        
      default:
        return { risk: 'low', conflicts: [] }
    }
  }
  
  // Implement conflict prevention strategies
  async implementConflictPrevention(
    repoPath: string,
    riskAnalysis: ConflictRiskAnalysis
  ): Promise<PreventionResult> {
    
    if (riskAnalysis.risk === 'low') {
      return { preventionNeeded: false }
    }
    
    const preventionStrategies: PreventionStrategy[] = []
    
    // CLAUDE.md cycle prevention
    if (riskAnalysis.hasCLAUDEMdRisk) {
      preventionStrategies.push(await this.preventCLAUDEMdCycles(repoPath))
    }
    
    // Framework conflict prevention
    if (riskAnalysis.hasFrameworkRisk) {
      preventionStrategies.push(await this.preventFrameworkConflicts(repoPath))
    }
    
    // Code conflict prevention
    if (riskAnalysis.hasCodeRisk) {
      preventionStrategies.push(await this.preventCodeConflicts(repoPath))
    }
    
    return {
      preventionNeeded: true,
      strategies: preventionStrategies,
      riskReduction: this.calculateRiskReduction(preventionStrategies)
    }
  }
  
  // CLAUDE.md cycle prevention
  private async preventCLAUDEMdCycles(repoPath: string): Promise<PreventionStrategy> {
    
    // Create backup of current CLAUDE.md
    const currentCLAUDE = await this.readFile('CLAUDE.md')
    const backup = await this.createCLAUDEMdBackup(currentCLAUDE)
    
    // Normalize CLAUDE.md format to reduce conflicts
    const normalized = this.normalizeCLAUDEMdFormat(currentCLAUDE)
    
    if (normalized !== currentCLAUDE) {
      await this.writeFile('CLAUDE.md', normalized)
      await this.mcpGitAdd(repoPath, ['CLAUDE.md'])
      
      // Create prevention commit
      await this.mcpGitCommit(repoPath, 'feat: normalize CLAUDE.md format to prevent cycles\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>')
    }
    
    return {
      type: 'claude_md_normalization',
      implemented: normalized !== currentCLAUDE,
      backup: backup.path,
      riskReduction: 0.7
    }
  }
}
```

## Framework Integration

### Quality Gate Integration

```yaml
conflict_resolution_quality_gates:
  pre_resolution:
    - backup_conflicted_files: automatic
    - validate_conflict_detection: complete
    - analyze_resolution_strategy: systematic
  
  during_resolution:
    - maintain_file_integrity: continuous
    - validate_resolution_logic: per_conflict
    - preserve_functional_code: mandatory
  
  post_resolution:
    - run_quality_checks: "pixi run quality"
    - validate_test_suite: "pixi run test"
    - verify_no_new_conflicts: git_status_check
    - confirm_taskmaster_sync: progress_update
```

### TaskMaster Integration

```typescript
interface ConflictResolutionTaskMaster {
  // Update TaskMaster during conflict resolution
  async updateConflictResolutionProgress(
    taskId: string,
    phase: ConflictResolutionPhase,
    details: ConflictResolutionDetails
  ): Promise<void> {
    
    const update = {
      operation: `Conflict Resolution: ${phase}`,
      details: {
        conflictsDetected: details.conflictCount,
        claudeMdCycles: details.claudeMdCycles,
        resolutionStrategy: details.strategy,
        automaticResolutions: details.automaticResolutions,
        manualResolutionsRequired: details.manualRequired
      },
      status: this.determineTaskStatus(phase, details),
      timestamp: new Date()
    }
    
    await this.mcpTaskMasterUpdateTask(taskId, update)
  }
}
```

This conflict resolution system provides systematic handling of merge conflicts with specialized support for CLAUDE.md cycles and framework-specific scenarios, maintaining high success rates while preserving framework compliance.