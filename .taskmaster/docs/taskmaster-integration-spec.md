# TaskMaster AI Integration Specification

## Overview

Defines how sub-agents integrate with TaskMaster AI for state sharing, progress tracking, and workflow coordination while maintaining framework compliance.

## Core Integration Points

### 1. State Capture and Transfer

```typescript
interface TaskMasterState {
  // Current project context
  projectRoot: string
  currentTag: string
  
  // Active task context
  activeTask: {
    id: string
    title: string
    status: TaskStatus
    priority: Priority
    dependencies: string[]
    subtasks?: Subtask[]
  }
  
  // Project health
  projectHealth: {
    totalTasks: number
    completedTasks: number
    blockedTasks: string[]
    nextAvailableTask?: string
  }
  
  // Quality status
  qualityStatus: {
    lastQualityCheck: timestamp
    testStatus: 'passing' | 'failing'
    lintStatus: 'clean' | 'violations'
    ciStatus: 'green' | 'red'
  }
}
```

### 2. Sub-Agent Registration Protocol

```yaml
# Sub-agents must register with TaskMaster for coordination
registration:
  agent_type: string
  capabilities: string[]
  tool_requirements: string[]
  framework_compliance: boolean
  
# TaskMaster tracks active sub-agents
active_agents:
  - type: "git-workflow-specialist"
    status: "executing"
    task_id: "2"
    started_at: timestamp
  - type: "quality-enforcer"
    status: "waiting"
    task_id: "7"
    dependencies: ["2"]
```

### 3. Progress Synchronization

```typescript
interface ProgressSync {
  // Before sub-agent execution
  captureCurrentState(): TaskMasterState
  
  // During execution - sub-agent updates
  updateTaskProgress(
    taskId: string,
    progress: {
      status?: TaskStatus
      notes?: string
      subtaskUpdates?: SubtaskUpdate[]
      blockers?: string[]
    }
  ): void
  
  // After execution - state reconciliation
  reconcileState(
    agentType: string,
    updates: TaskUpdate[],
    qualityStatus: QualityStatus
  ): void
}
```

## TaskMaster MCP Tool Integration

### Required MCP Tools for Sub-Agents

```yaml
core_tools:
  - mcp__task-master-ai__get_tasks      # State capture
  - mcp__task-master-ai__get_task       # Task details
  - mcp__task-master-ai__set_task_status # Progress updates
  - mcp__task-master-ai__update_task    # Task modifications
  - mcp__task-master-ai__update_subtask # Subtask updates
  - mcp__task-master-ai__next_task      # Workflow coordination

coordination_tools:
  - mcp__task-master-ai__add_dependency # Task relationships
  - mcp__task-master-ai__validate_dependencies # Integrity checks
  - mcp__task-master-ai__expand_task    # Task breakdown

monitoring_tools:
  - mcp__task-master-ai__complexity_report # Health assessment
  - mcp__task-master-ai__research       # Context enrichment
```

### State Consistency Protocol

```yaml
consistency_rules:
  # Task status updates
  task_updates:
    - single_source_of_truth: taskmaster
    - atomic_updates: required
    - dependency_validation: automatic
    - conflict_resolution: escalate_to_main
  
  # Quality gate integration
  quality_gates:
    - pre_status_update: "pixi run quality"
    - status_change_trigger: quality_validation
    - failure_handling: block_progress_update
    - recovery_protocol: systematic_fix_first
  
  # Cross-agent coordination
  coordination:
    - shared_state_access: read_only_for_others
    - modification_rights: owning_agent_only
    - conflict_detection: automatic
    - resolution_strategy: dependency_priority
```

## Workflow Coordination Patterns

### 1. Sequential Task Execution

```typescript
interface SequentialWorkflow {
  // Main context orchestrates
  async executeTaskSequence(taskIds: string[]): Promise<void> {
    for (const taskId of taskIds) {
      const task = await taskmaster.getTask(taskId)
      const agent = selectOptimalAgent(task)
      
      const context = await captureTaskMasterState()
      const result = await executeSubAgent(agent, task, context)
      
      await reconcileTaskMasterState(result)
      await validateQualityGates()
    }
  }
}
```

### 2. Parallel Task Execution

```typescript
interface ParallelWorkflow {
  // Independent tasks can run concurrently
  async executeParallelTasks(taskIds: string[]): Promise<void> {
    const independentTasks = await validateTaskIndependence(taskIds)
    
    const promises = independentTasks.map(async (taskId) => {
      const context = await captureTaskMasterState()
      const agent = selectOptimalAgent(await taskmaster.getTask(taskId))
      return executeSubAgent(agent, taskId, context)
    })
    
    const results = await Promise.all(promises)
    await reconcileAllResults(results)
  }
}
```

### 3. Dependency-Aware Coordination

```typescript
interface DependencyCoordination {
  // Respects task dependencies
  async executeDependencyAwareWorkflow(): Promise<void> {
    while (hasAvailableTasks()) {
      const nextTask = await taskmaster.nextTask()
      
      if (canExecuteInParallel(nextTask)) {
        await startParallelExecution(nextTask)
      } else {
        await executeSequentially(nextTask)
      }
      
      await updateDependencyGraph()
    }
  }
}
```

## Error Handling and Recovery

### TaskMaster State Protection

```yaml
state_protection:
  backup_strategy:
    - pre_execution_snapshot: automatic
    - incremental_backups: every_status_change
    - rollback_capability: full_state_restore
  
  corruption_prevention:
    - atomic_operations: required
    - validation_before_commit: mandatory
    - integrity_checks: continuous
  
  recovery_protocols:
    - partial_failure: rollback_to_checkpoint
    - complete_failure: restore_from_backup
    - data_corruption: escalate_to_manual_recovery
```

### Cross-Agent Conflict Resolution

```yaml
conflict_resolution:
  detection:
    - concurrent_modifications: automatic
    - dependency_violations: real_time
    - state_inconsistencies: periodic_check
  
  resolution_priority:
    1. framework_compliance
    2. dependency_integrity
    3. task_priority_order
    4. agent_execution_time
  
  escalation_matrix:
    - minor_conflicts: automatic_resolution
    - major_conflicts: pause_and_review
    - critical_conflicts: escalate_to_main_context
```

## Quality Integration

### Pre-Execution Validation

```yaml
pre_execution:
  taskmaster_health:
    - dependency_integrity: validate
    - task_consistency: verify
    - no_circular_dependencies: check
  
  project_quality:
    - current_quality_status: assess
    - blocking_quality_issues: identify
    - quality_gate_readiness: confirm
```

### Post-Execution Validation

```yaml
post_execution:
  taskmaster_updates:
    - status_changes: validate
    - dependency_updates: verify
    - subtask_modifications: check
  
  quality_compliance:
    - quality_gates: "pixi run quality"
    - test_status: "pixi run test"
    - framework_standards: verify
  
  state_consistency:
    - cross_reference_validation: automatic
    - integrity_verification: complete
    - conflict_detection: thorough
```

## Implementation Guidelines

### Sub-Agent TaskMaster Integration Checklist

```yaml
integration_requirements:
  initialization:
    - [ ] Capture current TaskMaster state
    - [ ] Validate task dependencies
    - [ ] Verify quality gate status
    - [ ] Register with coordination system
  
  during_execution:
    - [ ] Update progress incrementally
    - [ ] Maintain dependency integrity
    - [ ] Respect other agent operations
    - [ ] Monitor quality status
  
  completion:
    - [ ] Update final task status
    - [ ] Validate quality gates
    - [ ] Reconcile state changes
    - [ ] Trigger next task if appropriate
```

### Quality Gate Integration

```bash
# Mandatory quality validation before TaskMaster updates
quality_check_sequence:
  1. pixi run test        # 100% pass rate required
  2. pixi run quality     # Zero critical violations
  3. pixi run lint        # Zero F,E9 violations
  4. taskmaster_update    # Only after quality passes
```

This integration specification ensures all sub-agents maintain TaskMaster synchronization while preserving framework quality standards and enabling efficient workflow coordination.