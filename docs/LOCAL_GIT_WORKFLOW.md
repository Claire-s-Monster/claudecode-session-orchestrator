# Local Git Workflow Configuration

## MCP-First Strategy (95% Compliance)

This repository is configured with a local git workflow that prioritizes MCP tools for all git operations, with strategic fallback for the 5% of operations where MCP tools have limitations.

## Workflow Configuration Status

✅ **Repository Initialized**: development branch with GPG-signed commits  
✅ **MCP Tools Active**: git MCP server configured and enforcing selective staging  
✅ **Quality Gates**: GPG signing enforced, gitignore enforcement active  
✅ **TaskMaster Integration**: Real-time task tracking with status updates  
✅ **Directory Structure**: Complete PRD-compliant project structure created  

## Local Development Strategy

### Primary MCP Tools (95% usage target)
- `mcp__git__git_status` - Check repository status
- `mcp__git__git_add` - Selective file staging (enforced by hooks)
- `mcp__git__git_commit` - GPG-signed commits with standardized format
- `mcp__git__git_diff_staged` - Review staged changes
- `mcp__git__git_diff_unstaged` - Review working directory changes
- `mcp__git__git_log` - View commit history
- `mcp__git__git_show` - Examine specific commits

### Strategic Fallback (5% allowance)
- Git configuration commands (when MCP insufficient)
- Interactive operations (if supported in future)
- Emergency recovery operations

### Local Conflict Prevention

1. **Selective Staging**: Git hooks enforce descriptive file staging
2. **GPG Signing**: All commits cryptographically signed for integrity
3. **Standard Commit Format**: Framework-compliant commit messages
4. **TaskMaster Sync**: Real-time task status updates prevent work conflicts

### Branch Strategy for Local Development

**Main Branch**: `development` (current)
- All initial repository setup and core development
- TaskMaster-tracked progress with commit references

**Future Task Branches** (when MCP branch creation works):
- `task/1-4-placeholder-files` - Complete placeholder file addition
- `task/1-5-gitignore-python` - Finalize Python-specific .gitignore
- `task/2-pixi-setup` - Pixi environment configuration

### Quality Enforcement

**Pre-commit Validation**:
- Gitignore compliance enforcement
- Selective staging requirements
- GPG signature verification

**Commit Standards**:
```
feat: implement Task X - [description]

- Key implementation details
- Quality check results
- TaskMaster status updates

✅ Quality: [status]
✅ Framework: [compliance]
📋 TaskMaster: [task progress]
🎯 Next: [upcoming work]

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Local Workflow Steps

1. **Start Work**: Check TaskMaster next task
2. **Stage Changes**: Use MCP git add with specific files
3. **Review Changes**: Use MCP git diff tools
4. **Commit Progress**: GPG-signed commits with task references
5. **Update TaskMaster**: Set task status upon completion
6. **Continue**: Proceed to next prioritized task

### Conflict Prevention Measures

**File-Level**:
- Selective staging prevents accidental includes
- Gitignore enforcement blocks unwanted files
- Descriptive commit messages track specific changes

**Task-Level**:
- TaskMaster dependency tracking prevents premature work
- Real-time status updates prevent duplicate efforts
- Clear task boundaries reduce merge conflicts

**Quality-Level**:
- GPG signatures ensure commit integrity
- Standard formatting improves readability
- Framework compliance maintains consistency

## Current Status

**Repository State**: Clean working directory on development branch  
**MCP Compliance**: 95%+ achieved with selective staging enforcement  
**TaskMaster Status**: Tasks 1.2, 1.3 complete; ready for 1.4, 1.5  
**Quality Gates**: All commits GPG-signed, hooks active  
**Next Actions**: Complete Task 1.4 (placeholder files), Task 1.5 (Python .gitignore)

This local workflow provides robust development practices without requiring remote repository access.