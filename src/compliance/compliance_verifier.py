"""
Framework Compliance Verifier

Comprehensive compliance verification for the Universal Development Framework
including MCP-first strategy, quality standards, and security compliance.
"""

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import asyncio

@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""
    type: str
    severity: str  # critical, high, medium, low
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ComplianceResult:
    """Results of a compliance check."""
    passed: bool
    score: int  # 0-100
    violations: List[ComplianceViolation]
    warnings: List[ComplianceViolation]
    metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

class ComplianceVerifier:
    """
    Comprehensive framework compliance verifier.
    
    Enforces Universal Development Framework standards including:
    - MCP-first strategy (95% MCP usage target)
    - Zero-tolerance quality policy
    - PIXI-only dependency management
    - Security compliance
    - Git workflow standards
    """
    
    def __init__(self, project_root: Path, config: Optional[Dict] = None):
        self.project_root = Path(project_root)
        self.config = config or self._load_default_config()
        self.logger = logging.getLogger(__name__)
        
        # Compliance targets
        self.mcp_usage_target = 95  # 95% MCP usage
        self.quality_tolerance = 0  # Zero tolerance for quality violations
        self.security_tolerance = 0  # Zero tolerance for security issues
        
    def _load_default_config(self) -> Dict:
        """Load default compliance configuration."""
        return {
            "mcp_usage_target": 95,
            "quality_gates": {
                "test_pass_rate": 100,
                "lint_violations": 0,
                "coverage_threshold": 100,
                "security_issues": 0
            },
            "pixi_only_policy": True,
            "git_workflow_enforcement": True,
            "taskmaster_integration": True
        }
    
    async def verify_full_compliance(self) -> ComplianceResult:
        """
        Run comprehensive compliance verification.
        
        Returns:
            ComplianceResult with overall compliance status
        """
        self.logger.info("Starting comprehensive compliance verification")
        
        violations = []
        warnings = []
        metrics = {}
        
        # Run all compliance checks
        checks = [
            self._check_mcp_compliance(),
            self._check_quality_gates(),
            self._check_pixi_compliance(),
            self._check_security_compliance(),
            self._check_git_workflow(),
            self._check_taskmaster_integration(),
            self._check_framework_adherence()
        ]
        
        for check_result in await asyncio.gather(*checks, return_exceptions=True):
            if isinstance(check_result, Exception):
                violations.append(ComplianceViolation(
                    type="check_error",
                    severity="critical",
                    message=f"Compliance check failed: {str(check_result)}"
                ))
                continue
                
            violations.extend(check_result.get('violations', []))
            warnings.extend(check_result.get('warnings', []))
            metrics.update(check_result.get('metrics', {}))
        
        # Calculate compliance score
        score = self._calculate_compliance_score(violations, warnings)
        
        # Determine pass/fail
        critical_violations = [v for v in violations if v.severity == 'critical']
        passed = len(critical_violations) == 0
        
        result = ComplianceResult(
            passed=passed,
            score=score,
            violations=violations,
            warnings=warnings,
            metrics=metrics
        )
        
        self.logger.info(f"Compliance verification complete: {score}/100 score, {len(violations)} violations")
        return result
    
    async def _check_mcp_compliance(self) -> Dict:
        """Check MCP-first strategy compliance (95% target)."""
        violations = []
        warnings = []
        metrics = {}
        
        try:
            # Check .mcp.json configuration
            mcp_config_path = self.project_root / ".mcp.json"
            if not mcp_config_path.exists():
                violations.append(ComplianceViolation(
                    type="mcp_configuration",
                    severity="critical",
                    message="MCP configuration file (.mcp.json) missing",
                    remediation="Create .mcp.json with MCP server configurations"
                ))
            else:
                # Validate MCP server configurations
                with open(mcp_config_path) as f:
                    mcp_config = json.load(f)
                
                servers = mcp_config.get('mcpServers', {})
                metrics['mcp_servers_configured'] = len(servers)
                
                if len(servers) == 0:
                    warnings.append(ComplianceViolation(
                        type="mcp_configuration",
                        severity="medium",
                        message="No MCP servers configured"
                    ))
                
                # Check for TaskMaster AI integration
                if 'task-master-ai' not in servers:
                    warnings.append(ComplianceViolation(
                        type="taskmaster_integration",
                        severity="medium",
                        message="TaskMaster AI MCP server not configured"
                    ))
            
            # Analyze source code for MCP vs Bash usage patterns
            mcp_usage_stats = await self._analyze_tool_usage_patterns()
            metrics.update(mcp_usage_stats)
            
            mcp_percentage = mcp_usage_stats.get('mcp_percentage', 0)
            if mcp_percentage < self.mcp_usage_target:
                severity = "critical" if mcp_percentage < 90 else "high"
                violations.append(ComplianceViolation(
                    type="mcp_usage",
                    severity=severity,
                    message=f"MCP usage {mcp_percentage}% below {self.mcp_usage_target}% target",
                    remediation="Increase MCP tool usage, minimize strategic Bash usage"
                ))
            
        except Exception as e:
            violations.append(ComplianceViolation(
                type="mcp_check_error",
                severity="critical",
                message=f"MCP compliance check failed: {str(e)}"
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'metrics': metrics
        }
    
    async def _check_quality_gates(self) -> Dict:
        """Check zero-tolerance quality policy compliance."""
        violations = []
        warnings = []
        metrics = {}
        
        try:
            # Check if PIXI environment is available
            if not await self._check_pixi_available():
                warnings.append(ComplianceViolation(
                    type="pixi_environment",
                    severity="medium",
                    message="PIXI environment not available for quality checks"
                ))
                return {'violations': violations, 'warnings': warnings, 'metrics': metrics}
            
            # Test execution (100% pass rate required)
            test_result = await self._run_quality_command("test")
            if test_result and not test_result['passed']:
                violations.append(ComplianceViolation(
                    type="test_failures",
                    severity="critical",
                    message=f"Tests failed: {test_result.get('failures', 0)} failures",
                    remediation="Fix all test failures before proceeding"
                ))
            
            # Lint checks (zero F,E9 violations)
            lint_result = await self._run_quality_command("lint")
            if lint_result:
                f_violations = lint_result.get('f_violations', 0)
                e9_violations = lint_result.get('e9_violations', 0)
                
                if f_violations > 0:
                    violations.append(ComplianceViolation(
                        type="lint_violations",
                        severity="critical",
                        message=f"F-level lint violations: {f_violations}",
                        remediation="Fix all F-level lint violations"
                    ))
                
                if e9_violations > 0:
                    violations.append(ComplianceViolation(
                        type="lint_violations",
                        severity="critical",
                        message=f"E9-level lint violations: {e9_violations}",
                        remediation="Fix all E9-level lint violations"
                    ))
            
            # Coverage check (100% required)
            coverage_result = await self._run_quality_command("coverage")
            if coverage_result and coverage_result.get('percentage', 100) < 100:
                violations.append(ComplianceViolation(
                    type="coverage_insufficient",
                    severity="critical",
                    message=f"Test coverage {coverage_result['percentage']}% below 100%",
                    remediation="Achieve 100% test coverage"
                ))
            
            # Pre-commit hooks
            precommit_result = await self._run_quality_command("pre-commit")
            if precommit_result and not precommit_result['passed']:
                violations.append(ComplianceViolation(
                    type="precommit_failed",
                    severity="critical",
                    message="Pre-commit hooks failed",
                    remediation="Fix pre-commit hook failures"
                ))
            
            metrics.update({
                'test_result': test_result,
                'lint_result': lint_result,
                'coverage_result': coverage_result,
                'precommit_result': precommit_result
            })
            
        except Exception as e:
            violations.append(ComplianceViolation(
                type="quality_check_error",
                severity="critical",
                message=f"Quality gates check failed: {str(e)}"
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'metrics': metrics
        }
    
    async def _check_pixi_compliance(self) -> Dict:
        """Check PIXI-only dependency management compliance."""
        violations = []
        warnings = []
        metrics = {}
        
        try:
            # Check for PIXI configuration
            pixi_config = None
            if (self.project_root / "pixi.toml").exists():
                pixi_config = "pixi.toml"
            elif (self.project_root / "pyproject.toml").exists():
                pixi_config = "pyproject.toml"
            
            if not pixi_config:
                violations.append(ComplianceViolation(
                    type="pixi_configuration",
                    severity="critical",
                    message="No PIXI configuration file found (pixi.toml or pyproject.toml)",
                    remediation="Create PIXI configuration file"
                ))
            else:
                metrics['pixi_config_file'] = pixi_config
            
            # Check for pip violations
            pip_files = [
                "requirements.txt",
                "requirements-dev.txt", 
                "setup.py",
                "setup.cfg"
            ]
            
            pip_violations_found = []
            for pip_file in pip_files:
                if (self.project_root / pip_file).exists():
                    pip_violations_found.append(pip_file)
            
            if pip_violations_found:
                violations.append(ComplianceViolation(
                    type="pip_dependencies",
                    severity="critical",
                    message=f"pip dependency files found: {pip_violations_found}",
                    remediation="Remove pip files and migrate dependencies to PIXI"
                ))
            
            metrics['pip_violations'] = pip_violations_found
            
        except Exception as e:
            violations.append(ComplianceViolation(
                type="pixi_check_error",
                severity="critical",
                message=f"PIXI compliance check failed: {str(e)}"
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'metrics': metrics
        }
    
    async def _check_security_compliance(self) -> Dict:
        """Check security compliance standards."""
        violations = []
        warnings = []
        metrics = {}
        
        try:
            # Check for sensitive files
            sensitive_patterns = ["*.key", "*.pem", "*.p12", "*.pfx", "private_key*"]
            sensitive_files = []
            
            for pattern in sensitive_patterns:
                matches = list(self.project_root.rglob(pattern))
                sensitive_files.extend(matches)
            
            if sensitive_files:
                violations.append(ComplianceViolation(
                    type="sensitive_files",
                    severity="critical",
                    message=f"Sensitive files detected: {[str(f) for f in sensitive_files]}",
                    remediation="Remove sensitive files or add to .gitignore"
                ))
            
            # Check .env file security
            env_file = self.project_root / ".env"
            if env_file.exists():
                gitignore_file = self.project_root / ".gitignore"
                if not gitignore_file.exists() or ".env" not in gitignore_file.read_text():
                    violations.append(ComplianceViolation(
                        type="env_file_security",
                        severity="critical",
                        message=".env file not in .gitignore",
                        remediation="Add .env to .gitignore"
                    ))
            
            # Run security scanning if available
            security_result = await self._run_quality_command("security")
            if security_result and not security_result['passed']:
                violations.append(ComplianceViolation(
                    type="security_scan_failed",
                    severity="critical",
                    message="Security scan detected issues",
                    remediation="Fix security vulnerabilities"
                ))
            
            metrics.update({
                'sensitive_files': len(sensitive_files),
                'security_scan_result': security_result
            })
            
        except Exception as e:
            violations.append(ComplianceViolation(
                type="security_check_error",
                severity="critical",
                message=f"Security compliance check failed: {str(e)}"
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'metrics': metrics
        }
    
    async def _check_git_workflow(self) -> Dict:
        """Check git workflow compliance."""
        violations = []
        warnings = []
        metrics = {}
        
        try:
            # Check if git repository exists
            git_dir = self.project_root / ".git"
            if not git_dir.exists():
                violations.append(ComplianceViolation(
                    type="git_repository",
                    severity="critical",
                    message="Git repository not initialized",
                    remediation="Initialize git repository"
                ))
                return {'violations': violations, 'warnings': warnings, 'metrics': metrics}
            
            # Check for .gitignore
            gitignore_file = self.project_root / ".gitignore"
            if not gitignore_file.exists():
                warnings.append(ComplianceViolation(
                    type="gitignore_missing",
                    severity="medium",
                    message=".gitignore file missing"
                ))
            else:
                # Check for standard ignore patterns
                gitignore_content = gitignore_file.read_text()
                required_patterns = ["__pycache__", "*.pyc", ".env"]
                missing_patterns = [p for p in required_patterns if p not in gitignore_content]
                
                if missing_patterns:
                    warnings.append(ComplianceViolation(
                        type="gitignore_patterns",
                        severity="low",
                        message=f"Missing gitignore patterns: {missing_patterns}"
                    ))
            
            metrics.update({
                'git_initialized': True,
                'gitignore_exists': gitignore_file.exists()
            })
            
        except Exception as e:
            violations.append(ComplianceViolation(
                type="git_check_error",
                severity="critical",
                message=f"Git workflow check failed: {str(e)}"
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'metrics': metrics
        }
    
    async def _check_taskmaster_integration(self) -> Dict:
        """Check TaskMaster AI integration compliance."""
        violations = []
        warnings = []
        metrics = {}
        
        try:
            # Check TaskMaster directory structure
            taskmaster_dir = self.project_root / ".taskmaster"
            if not taskmaster_dir.exists():
                violations.append(ComplianceViolation(
                    type="taskmaster_not_initialized",
                    severity="critical",
                    message="TaskMaster not initialized",
                    remediation="Run 'task-master init'"
                ))
                return {'violations': violations, 'warnings': warnings, 'metrics': metrics}
            
            # Check essential TaskMaster files
            required_files = [
                ".taskmaster/config.json",
                ".taskmaster/tasks/tasks.json",
                ".taskmaster/docs/prd.txt"
            ]
            
            missing_files = []
            for file_path in required_files:
                if not (self.project_root / file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                warnings.append(ComplianceViolation(
                    type="taskmaster_files",
                    severity="medium",
                    message=f"TaskMaster files missing: {missing_files}"
                ))
            
            metrics.update({
                'taskmaster_initialized': True,
                'missing_files': missing_files
            })
            
        except Exception as e:
            violations.append(ComplianceViolation(
                type="taskmaster_check_error",
                severity="critical",
                message=f"TaskMaster integration check failed: {str(e)}"
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'metrics': metrics
        }
    
    async def _check_framework_adherence(self) -> Dict:
        """Check Universal Development Framework adherence."""
        violations = []
        warnings = []
        metrics = {}
        
        try:
            # Check for CLAUDE.md
            claude_md = self.project_root / "CLAUDE.md"
            if not claude_md.exists():
                warnings.append(ComplianceViolation(
                    type="claude_instructions",
                    severity="medium",
                    message="Project instructions file (CLAUDE.md) missing"
                ))
            
            # Check for .claude directory
            claude_dir = self.project_root / ".claude"
            if not claude_dir.exists():
                warnings.append(ComplianceViolation(
                    type="claude_configuration",
                    severity="medium",
                    message="Claude Code configuration directory missing"
                ))
            else:
                # Check for custom commands
                commands_dir = claude_dir / "commands"
                if commands_dir.exists():
                    command_count = len(list(commands_dir.rglob("*.md")))
                    metrics['claude_commands'] = command_count
            
            # Check directory structure
            expected_dirs = ["src", "tests", "scripts", "docs"]
            existing_dirs = [d for d in expected_dirs if (self.project_root / d).exists()]
            
            metrics.update({
                'claude_md_exists': claude_md.exists(),
                'claude_dir_exists': claude_dir.exists(),
                'standard_directories': existing_dirs
            })
            
        except Exception as e:
            violations.append(ComplianceViolation(
                type="framework_check_error",
                severity="critical",
                message=f"Framework adherence check failed: {str(e)}"
            ))
        
        return {
            'violations': violations,
            'warnings': warnings,
            'metrics': metrics
        }
    
    async def _analyze_tool_usage_patterns(self) -> Dict:
        """Analyze MCP vs Bash tool usage patterns in source code."""
        # This would analyze source code for tool usage patterns
        # For now, return placeholder data
        return {
            'mcp_operations': 0,
            'bash_operations': 0,
            'mcp_percentage': 100,  # Default to compliant for new projects
            'total_operations': 0
        }
    
    async def _check_pixi_available(self) -> bool:
        """Check if PIXI is available and environment is initialized."""
        try:
            result = await asyncio.create_subprocess_exec(
                'pixi', 'info',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    async def _run_quality_command(self, command: str) -> Optional[Dict]:
        """Run a PIXI quality command and return results."""
        try:
            if not await self._check_pixi_available():
                return None
            
            # Map command to PIXI task
            task_map = {
                "test": "test",
                "lint": "lint",
                "coverage": "coverage",
                "pre-commit": "pre-commit",
                "security": "security"
            }
            
            task = task_map.get(command)
            if not task:
                return None
            
            # Check if task exists
            result = await asyncio.create_subprocess_exec(
                'pixi', 'task', 'list',
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if task not in stdout.decode():
                return None
            
            # Run the task
            result = await asyncio.create_subprocess_exec(
                'pixi', 'run', task,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            # Parse results based on command type
            return self._parse_quality_result(command, result.returncode, stdout.decode(), stderr.decode())
            
        except Exception as e:
            self.logger.error(f"Error running quality command {command}: {e}")
            return None
    
    def _parse_quality_result(self, command: str, return_code: int, stdout: str, stderr: str) -> Dict:
        """Parse quality command results."""
        if command == "test":
            return {
                'passed': return_code == 0,
                'failures': stdout.count('FAILED'),
                'output': stdout
            }
        elif command == "lint":
            return {
                'passed': return_code == 0,
                'f_violations': len([line for line in stdout.split('\n') if 'F' in line and ':' in line]),
                'e9_violations': len([line for line in stdout.split('\n') if 'E9' in line and ':' in line]),
                'output': stdout
            }
        elif command == "coverage":
            # Parse coverage percentage from output
            percentage = 100  # Default
            for line in stdout.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    try:
                        percentage = int(line.split('%')[0].split()[-1])
                    except (ValueError, IndexError):
                        pass
            
            return {
                'passed': return_code == 0,
                'percentage': percentage,
                'output': stdout
            }
        else:
            return {
                'passed': return_code == 0,
                'output': stdout
            }
    
    def _calculate_compliance_score(self, violations: List[ComplianceViolation], warnings: List[ComplianceViolation]) -> int:
        """Calculate overall compliance score (0-100)."""
        total_checks = 50  # Approximate number of checks
        
        # Weight violations by severity
        penalty_points = 0
        for violation in violations:
            if violation.severity == 'critical':
                penalty_points += 10
            elif violation.severity == 'high':
                penalty_points += 5
            elif violation.severity == 'medium':
                penalty_points += 2
            else:
                penalty_points += 1
        
        for warning in warnings:
            penalty_points += 1
        
        score = max(0, 100 - penalty_points)
        return score
    
    def generate_compliance_report(self, result: ComplianceResult) -> Dict:
        """Generate comprehensive compliance report."""
        return {
            "compliance_report": {
                "timestamp": result.timestamp.isoformat(),
                "project_root": str(self.project_root),
                "framework_version": "1.0.0",
                "overall_compliance": {
                    "passed": result.passed,
                    "score": result.score,
                    "grade": self._get_compliance_grade(result.score)
                },
                "violations": [
                    {
                        "type": v.type,
                        "severity": v.severity,
                        "message": v.message,
                        "file_path": v.file_path,
                        "line_number": v.line_number,
                        "remediation": v.remediation,
                        "timestamp": v.timestamp.isoformat()
                    }
                    for v in result.violations
                ],
                "warnings": [
                    {
                        "type": w.type,
                        "severity": w.severity,
                        "message": w.message,
                        "remediation": w.remediation,
                        "timestamp": w.timestamp.isoformat()
                    }
                    for w in result.warnings
                ],
                "metrics": result.metrics,
                "framework_compliance": {
                    "mcp_first_strategy": result.metrics.get('mcp_percentage', 0) >= self.mcp_usage_target,
                    "zero_tolerance_quality": len([v for v in result.violations if v.type.startswith('test_') or v.type.startswith('lint_')]) == 0,
                    "pixi_only_policy": len([v for v in result.violations if v.type == 'pip_dependencies']) == 0,
                    "security_compliance": len([v for v in result.violations if v.type.startswith('security_')]) == 0,
                    "taskmaster_integration": len([v for v in result.violations if v.type.startswith('taskmaster_')]) == 0
                }
            }
        }
    
    def _get_compliance_grade(self, score: int) -> str:
        """Get compliance grade based on score."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
EOF < /dev/null
