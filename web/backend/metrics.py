"""
Metrics collection for code statistics and AI coding effectiveness.
"""
import subprocess
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import re

# Repository root directory. When running inside the metrics collector job we
# override this via the METRICS_REPO_PATH environment variable (points to the
# freshly cloned working tree).
REPO_ROOT = Path(
    os.getenv(
        "METRICS_REPO_PATH",
        Path(__file__).parent.parent.parent,
    )
)


def get_git_commits(days: int = 30) -> List[Dict[str, Any]]:
    """Get commit statistics from git log."""
    try:
        # Get commits from the last N days
        cmd = [
            'git', 'log',
            f'--since={days} days ago',
            '--pretty=format:{"commit":"%H","author":"%an","email":"%ae","date":"%ai","message":"%s","files_changed":"%stat"}',
            '--numstat'
        ]
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        # Parse git log output
        commits = []
        current_commit = None
        lines = result.stdout.split('\n')
        
        for line in lines:
            if line.startswith('{"commit"'):
                try:
                    commit_data = json.loads(line)
                    current_commit = {
                        'hash': commit_data.get('commit', '')[:7],
                        'author': commit_data.get('author', ''),
                        'email': commit_data.get('email', ''),
                        'date': commit_data.get('date', ''),
                        'message': commit_data.get('message', ''),
                        'files_changed': 0,
                        'insertions': 0,
                        'deletions': 0
                    }
                    commits.append(current_commit)
                except json.JSONDecodeError:
                    continue
            elif current_commit and line and not line.startswith('{'):
                # Parse numstat line: additions deletions filename
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        additions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                        current_commit['insertions'] += additions
                        current_commit['deletions'] += deletions
                        current_commit['files_changed'] += 1
                    except ValueError:
                        continue
        
        return commits
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"Error getting git commits: {e}")
        return []


def get_lines_of_code_by_module() -> Dict[str, Dict[str, Any]]:
    """Calculate lines of code by module/directory."""
    metrics = {}
    
    # Define major modules/directories to track
    modules = {
        'backend': 'web/backend',
        'frontend': 'web/frontend/src',
        'agents': ['bq_agent', 'bq_agent_mick', 'asl_agent'],
        'deployment': 'web/deploy',
        'scripts': 'scripts',
        'docs': 'docs',
    }
    
    # File extensions to count
    code_extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.css': 'CSS',
        '.html': 'HTML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.json': 'JSON',
        '.sh': 'Shell',
        '.md': 'Markdown',
    }
    
    def count_lines(file_path: Path) -> Dict[str, int]:
        """Count lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                total = len(lines)
                code = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
                # For some languages, refine comment detection
                if file_path.suffix in ['.py']:
                    code = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
                elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                    code = sum(1 for line in lines if line.strip() and not (line.strip().startswith('//') or line.strip().startswith('/*')))
                else:
                    code = total  # Simple count for other files
                
                return {
                    'total': total,
                    'code': code,
                    'blank': sum(1 for line in lines if not line.strip()),
                    'comments': total - code - sum(1 for line in lines if not line.strip())
                }
        except Exception:
            return {'total': 0, 'code': 0, 'blank': 0, 'comments': 0}
    
    # Count by module
    for module_name, module_path in modules.items():
        module_metrics = {
            'total_files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'by_language': {}
        }
        
        if isinstance(module_path, list):
            # Multiple directories
            for mp in module_path:
                path = REPO_ROOT / mp
                if path.exists():
                    for ext, lang in code_extensions.items():
                        for file_path in path.rglob(f'*{ext}'):
                            if file_path.is_file():
                                lines_data = count_lines(file_path)
                                module_metrics['total_files'] += 1
                                module_metrics['total_lines'] += lines_data['total']
                                module_metrics['code_lines'] += lines_data['code']
                                if lang not in module_metrics['by_language']:
                                    module_metrics['by_language'][lang] = {
                                        'files': 0,
                                        'lines': 0,
                                        'code_lines': 0
                                    }
                                module_metrics['by_language'][lang]['files'] += 1
                                module_metrics['by_language'][lang]['lines'] += lines_data['total']
                                module_metrics['by_language'][lang]['code_lines'] += lines_data['code']
        else:
            # Single directory
            path = REPO_ROOT / module_path
            if path.exists():
                for ext, lang in code_extensions.items():
                    for file_path in path.rglob(f'*{ext}'):
                        if file_path.is_file():
                            lines_data = count_lines(file_path)
                            module_metrics['total_files'] += 1
                            module_metrics['total_lines'] += lines_data['total']
                            module_metrics['code_lines'] += lines_data['code']
                            if lang not in module_metrics['by_language']:
                                module_metrics['by_language'][lang] = {
                                    'files': 0,
                                    'lines': 0,
                                    'code_lines': 0
                                }
                            module_metrics['by_language'][lang]['files'] += 1
                            module_metrics['by_language'][lang]['lines'] += lines_data['total']
                            module_metrics['by_language'][lang]['code_lines'] += lines_data['code']
        
        metrics[module_name] = module_metrics
    
    return metrics


def get_repository_summary() -> Dict[str, Any]:
    """Get overall repository statistics."""
    try:
        # Total commits
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )
        total_commits = int(result.stdout.strip()) if result.returncode == 0 else 0
        
        # Repository age
        result = subprocess.run(
            ['git', 'log', '--reverse', '--pretty=format:%ai', '--date=iso', '|', 'head', '-1'],
            cwd=REPO_ROOT,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        first_commit_date = None
        if result.returncode == 0 and result.stdout.strip():
            first_commit_date = result.stdout.strip().split('\n')[0]
        
        # Active contributors
        result = subprocess.run(
            ['git', 'shortlog', '-sn', '--all'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )
        contributors = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n')[:10]:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        contributors.append({
                            'commits': int(parts[0]),
                            'name': parts[1]
                        })
        
        # Total files
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )
        total_files = len(result.stdout.strip().split('\n')) if result.returncode == 0 and result.stdout.strip() else 0
        
        return {
            'total_commits': total_commits,
            'first_commit_date': first_commit_date,
            'contributors': contributors,
            'total_files': total_files
        }
    except Exception as e:
        print(f"Error getting repository summary: {e}")
        return {
            'total_commits': 0,
            'first_commit_date': None,
            'contributors': [],
            'total_files': 0
        }


def calculate_ai_effectiveness_metrics(commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate metrics related to AI-assisted coding effectiveness."""
    if not commits:
        return {
            'total_commits': 0,
            'avg_files_per_commit': 0,
            'avg_changes_per_commit': 0,
            'productivity_score': 0,
            'commits_per_day': 0
        }
    
    total_files = sum(c.get('files_changed', 0) for c in commits)
    total_insertions = sum(c.get('insertions', 0) for c in commits)
    total_deletions = sum(c.get('deletions', 0) for c in commits)
    total_changes = total_insertions + total_deletions
    
    # Calculate date range
    if commits:
        dates = [datetime.strptime(c.get('date', '').split()[0], '%Y-%m-%d') for c in commits if c.get('date')]
        if dates:
            date_range = (max(dates) - min(dates)).days + 1
            commits_per_day = len(commits) / date_range if date_range > 0 else len(commits)
        else:
            commits_per_day = len(commits)
    else:
        commits_per_day = 0
    
    # Productivity score (normalized metric)
    # Based on commits per day, files changed, and code volume
    productivity_score = min(100, (
        (commits_per_day * 10) +  # Commits per day weight
        (total_files / len(commits) * 2) +  # Files per commit weight
        (total_changes / len(commits) / 10)  # Changes per commit weight
    ) if commits else 0)
    
    return {
        'total_commits': len(commits),
        'avg_files_per_commit': total_files / len(commits) if commits else 0,
        'avg_changes_per_commit': total_changes / len(commits) if commits else 0,
        'total_insertions': total_insertions,
        'total_deletions': total_deletions,
        'net_lines': total_insertions - total_deletions,
        'productivity_score': round(productivity_score, 2),
        'commits_per_day': round(commits_per_day, 2),
        'days_analyzed': len(set(c.get('date', '').split()[0] for c in commits if c.get('date')))
    }


def get_all_metrics(days: int = 30) -> Dict[str, Any]:
    """Get all metrics."""
    commits = get_git_commits(days)
    loc_by_module = get_lines_of_code_by_module()
    repo_summary = get_repository_summary()
    ai_metrics = calculate_ai_effectiveness_metrics(commits)
    
    # Calculate total LOC
    total_loc = {
        'total_files': sum(m.get('total_files', 0) for m in loc_by_module.values()),
        'total_lines': sum(m.get('total_lines', 0) for m in loc_by_module.values()),
        'code_lines': sum(m.get('code_lines', 0) for m in loc_by_module.values())
    }
    
    return {
        'repository_summary': repo_summary,
        'commits': commits,
        'commit_statistics': {
            'total': len(commits),
            'by_author': {},
            'by_date': {}
        },
        'lines_of_code': {
            'summary': total_loc,
            'by_module': loc_by_module
        },
        'ai_effectiveness': ai_metrics,
        'generated_at': datetime.now().isoformat(),
        'analysis_period_days': days
    }

