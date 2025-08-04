#!/usr/bin/env python3
"""
Скрипт для проверки готовности к деплою
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def check_git_status() -> Tuple[bool, List[str]]:
    """Проверяет статус git репозитория"""
    issues = []
    
    try:
        # Проверяем, что мы в git репозитории
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("❌ Не найден git репозиторий")
            return False, issues
        
        # Проверяем незакоммиченные изменения
        result = subprocess.run(['git', 'diff-index', '--quiet', 'HEAD', '--'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            issues.append("⚠️  Есть незакоммиченные изменения")
        
        # Проверяем, что мы на правильной ветке
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch != 'main' and branch != 'master':
                issues.append(f"⚠️  Текущая ветка: {branch} (рекомендуется main/master)")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        issues.append(f"❌ Ошибка проверки git: {e}")
        return False, issues


def check_required_files() -> Tuple[bool, List[str]]:
    """Проверяет наличие необходимых файлов"""
    issues = []
    required_files = [
        'requirements.txt',
        'docker-compose.yml',
        'Dockerfile',
        'app/bot.py',
        'app/config.py',
        'scripts/run_migrations.sh',
        'manage.py',
        'env.example'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            issues.append(f"❌ Отсутствует файл: {file_path}")
    
    return len(issues) == 0, issues


def check_environment_variables() -> Tuple[bool, List[str]]:
    """Проверяет переменные окружения"""
    issues = []
    required_vars = [
        'TELEGRAM_TOKEN',
        'DB_NAME',
        'DB_USER', 
        'DB_PASS'
    ]
    
    # Проверяем .env файл
    env_file = Path('.env')
    if env_file.exists():
        env_content = env_file.read_text()
        for var in required_vars:
            if f'{var}=' not in env_content:
                issues.append(f"⚠️  В .env отсутствует: {var}")
    else:
        issues.append("⚠️  Файл .env не найден (будет создан из env.example)")
    
    return len(issues) == 0, issues


def check_docker_files() -> Tuple[bool, List[str]]:
    """Проверяет Docker файлы"""
    issues = []
    
    # Проверяем Dockerfile
    dockerfile = Path('Dockerfile')
    if dockerfile.exists():
        content = dockerfile.read_text()
        if 'python:3.11' not in content:
            issues.append("⚠️  Dockerfile использует нестандартную версию Python")
    else:
        issues.append("❌ Отсутствует Dockerfile")
    
    # Проверяем docker-compose.yml
    compose_file = Path('docker-compose.yml')
    if compose_file.exists():
        content = compose_file.read_text()
        if 'version:' not in content:
            issues.append("⚠️  docker-compose.yml может быть некорректным")
    else:
        issues.append("❌ Отсутствует docker-compose.yml")
    
    return len(issues) == 0, issues


def check_requirements() -> Tuple[bool, List[str]]:
    """Проверяет requirements.txt"""
    issues = []
    
    requirements_file = Path('requirements.txt')
    if not requirements_file.exists():
        issues.append("❌ Отсутствует requirements.txt")
        return False, issues
    
    content = requirements_file.read_text()
    required_packages = [
        'aiogram',
        'sqlalchemy',
        'asyncpg',
        'redis',
        'pydantic'
    ]
    
    for package in required_packages:
        if package not in content:
            issues.append(f"⚠️  В requirements.txt отсутствует: {package}")
    
    return len(issues) == 0, issues


def check_scripts() -> Tuple[bool, List[str]]:
    """Проверяет скрипты"""
    issues = []
    
    scripts_dir = Path('scripts')
    if not scripts_dir.exists():
        issues.append("❌ Отсутствует директория scripts/")
        return False, issues
    
    required_scripts = [
        'run_migrations.sh',
        'deploy.sh'
    ]
    
    for script in required_scripts:
        script_path = scripts_dir / script
        if not script_path.exists():
            issues.append(f"❌ Отсутствует скрипт: scripts/{script}")
        elif not os.access(script_path, os.X_OK):
            issues.append(f"⚠️  Скрипт не исполняемый: scripts/{script}")
    
    return len(issues) == 0, issues


def main():
    """Основная функция проверки"""
    print("🔍 Проверка готовности к деплою...\n")
    
    checks = [
        ("Git статус", check_git_status),
        ("Необходимые файлы", check_required_files),
        ("Переменные окружения", check_environment_variables),
        ("Docker файлы", check_docker_files),
        ("Requirements", check_requirements),
        ("Скрипты", check_scripts),
    ]
    
    all_passed = True
    all_issues = []
    
    for check_name, check_func in checks:
        print(f"📋 {check_name}...")
        passed, issues = check_func()
        
        if passed:
            print("✅ OK")
        else:
            print("❌ Проблемы найдены:")
            for issue in issues:
                print(f"   {issue}")
            all_passed = False
        
        all_issues.extend(issues)
        print()
    
    # Итоговый результат
    print("=" * 50)
    if all_passed:
        print("🎉 Все проверки пройдены! Готов к деплою.")
        print("\n🚀 Для деплоя выполните:")
        print("   export SERVER_HOST=89.169.38.246")
        print("   export SERVER_USER=root")
        print("   ./scripts/deploy.sh")
    else:
        print("⚠️  Найдены проблемы, которые нужно исправить перед деплоем:")
        for issue in all_issues:
            print(f"   {issue}")
        print("\n🔧 Исправьте проблемы и запустите проверку снова.")
        sys.exit(1)


if __name__ == "__main__":
    main() 