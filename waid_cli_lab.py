#!/usr/bin/env python3

"""
@file waid_cli_lab.py
@brief WAID Operations & Command Registry.
Modular interactive launcher with context guards (PC Host, Docker, ARM).
"""

import os
import sys
import ast
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Preliminary environment check
WAID_SOURCE = os.environ.get("WAID_SOURCE")
if not WAID_SOURCE:
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")


def is_in_docker() -> bool:
    """
    Verifies if execution is inside a Docker container.
    @return: True if running inside a Docker container, False otherwise.
    """
    if os.environ.get("IN_DOCKER") == "1":
        return True
    if Path("/.dockerenv").exists():
        return True
    cgroup = Path("/proc/1/cgroup")
    if cgroup.exists():
        try:
            return any(t in cgroup.read_text() for t in ["docker", "containerd", "kubepods"])
        except Exception:
            pass
    return False


def is_arm_host() -> bool:
    """
    Verifies if the execution hardware/host is ARM.
    @return: True if architecture is ARM or aarch64, False otherwise.
    """
    try:
        res = subprocess.run(["uname", "-m"], capture_output=True, text=True)
        arch = res.stdout.strip().lower()
        return "arm" in arch or "aarch64" in arch
    except Exception:
        return False
    

def extract_docstring_from_script(cmd_str: str) -> Optional[str]:
    """
    Extracts the header description or docstring from Python and Bash scripts preserving multiline layout.
    @param cmd_str: Bash command string.
    @return: Formatted content of the description or None if not found.
    """
    expanded = os.path.expandvars(cmd_str)
    
    # Search for a script file (.py or .sh) in the command
    match = re.search(r'(\S+\.(py|sh))', expanded)
    if not match:
        return None

    script_path = Path(match.group(1))

    # If it is a relative path without root, try with WAID_SOURCE
    if not script_path.exists() and WAID_SOURCE:
        script_path = Path(WAID_SOURCE) / script_path.name

    if not script_path.exists():
        return None

    try:
        source_code = script_path.read_text(encoding="utf-8")
        
        if script_path.suffix == '.py':
            parsed = ast.parse(source_code)
            doc = ast.get_docstring(parsed)
            return doc.strip() if doc else None
            
        elif script_path.suffix == '.sh':
            lines = source_code.splitlines()
            comment_block = []
            capturing = False
            
            for line in lines:
                line_str = line.strip()
                # Ignore initial shebang
                if line_str.startswith("#!"):
                    continue
                
                # If we find a comment line
                if line_str.startswith("#"):
                    # Clean only the initial hash and related spaces
                    cleaned = re.sub(r'^#+\s*', '', line_str)
                    # Exclude lines consisting only of separator characters (e.g. ========)
                    if cleaned and not set(cleaned) <= {'='}:
                        comment_block.append(cleaned)
                    capturing = True
                elif capturing and line_str == "":
                    # Break at the first empty line after the header
                    break
                elif capturing and not line_str.startswith("#"):
                    # Break if code is encountered
                    break
                    
            # Use \n instead of space to preserve line alignment
            return "\n".join(comment_block) if comment_block else None
            
    except Exception:
        None
        

def confirm_critical_operation(item: Dict[str, Any]) -> bool:
    """
    Requests confirmation for critical operations by extracting the script description.
    @param item: Selected command dictionary.
    @return: True if the user confirms with 'Y' or 'y', False otherwise.
    """
    cmd_str = item["cmd"]
    doc = extract_docstring_from_script(cmd_str)

    print("\n" + "!" * 50)
    print(" [ATTENZIONE] Critical Operation Requested!")
    print(f" Target: {item['desc']}")
    print(f"\nRequired command: \n {cmd_str}")
    
    if doc:
        print("\n--- Script Documentation ---")
        print(doc)
        print("----------------------------")
    else:
        print("\nNo docstring extracted from the script.")
        
    print("!" * 50)

    choice = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
    return choice == "y"


# ==============================================================================
# COMMAND REGISTRY
# - "critical": True to request confirmation and display the docstring
# ==============================================================================

COMMAND_SECTIONS: List[Dict[str, Any]] = [
    {
        "title": "1. PC HOST ONLY (Blocked if inside Docker)",
        "context_rule": "pc_only",
        "commands": [
            {
                "desc": "Run main lab pipeline (waid_orchestrate_lab.py) from PC host",
                "cmd": "./waid_orchestrate_lab.py",
                "critical": False
            },
            {
                "desc": "Run ML Retrain locally on PC",
                "cmd": "python3 $WAID_SOURCE/waid_05_1_train_model.py",
                "critical": True
            },
            {
                "desc": "Full Local Setup (WAID_SETUP_MODE=1)",
                "cmd": "WAID_SETUP_MODE=1 python3 $WAID_SOURCE/waid_orchestrate_lab.py",
                "critical": True
            },
            {
                "desc": "Reset DB & Local Feature Store",
                "cmd": "WAID_SETUP_MODE=2 python3 $WAID_SOURCE/waid_orchestrate_lab.py",
                "critical": True
            },
            {
                "desc": "Show latest available log",
                "cmd": "WAID_SETUP_MODE=2 python3 $WAID_SOURCE/waid_orchestrate_lab.py",
                "critical": False
            },
            {
                "desc": "Update source code on arm container",
                "cmd": "$WAID_SOURCE/src/utils/draft_sync_source_on_arm.sh",
                "critical": True
            },
            {
                "desc": "Synchronize draft and public waid repositories",
                "cmd": "$WAID_SOURCE/src/utils/draft_sync_public_repo.sh",
                "critical": True
            },
            {
                "desc": "Make lint review for current commit",
                "cmd": (
                    "{ git diff --name-only --diff-filter=d; "
                    "git ls-files --others --exclude-standard; } "
                    r"| grep -E '\.(py|md)$' "
                    "| xargs -I {} src/utils/draft_lint_review.py {}"
                ),
                "critical": False
            },
            {
                "desc": "Make pytest only for unit tests",
                "cmd": ( ". $WAID_SOURCE/.venv/bin/activate ; "
                         #"pip install --upgrade setuptools ; "
                         #"pip install --no-build-isolation -e . ; " 
                         "pytest --cache-clear tests/unit/*"
                ),
                "critical": False
            },
            
            {   "desc": "DBT: execute just dbt compile|run|test over main mock db",
                "cmd": ( 
                         "WAID_SIM_MODE=True WAID_DATA_DIR=$WAID_SOURCE/mock/data "
                         "WAID_DB_MOCK_FILE=$WAID_SOURCE/mock/data/waid_mock.db "
                         "$WAID_SOURCE/.venv-dbt/bin/dbt test "
                         "--profiles-dir $WAID_SOURCE/config "
                         "--project-dir $WAID_SOURCE/dbt "
                         "--target dev ; "
                    ),
                "critical": False
            },
            
            {   "desc": "DBT: execute just full dbt setup and run over main mock db",
                "cmd": ( "waid_02_1_dbt_sync.py ; "
                         "WAID_SIM_MODE=True WAID_DATA_DIR=$WAID_SOURCE/mock/data "
                         "WAID_DB_MOCK_FILE=$WAID_SOURCE/mock/data/waid_mock.db "
                         "$WAID_SOURCE/.venv-dbt/bin/dbt run "
                         "--profiles-dir $WAID_SOURCE/config "
                         "--project-dir $WAID_SOURCE/dbt "
                         "--target dev ; "
                    ),
                "critical": False
            },
            
            {   "desc": "DBT: command to check table existing",
                "cmd": ( "waid_02_1_dbt_sync.py ; "
                         
                         "WAID_SIM_MODE=True WAID_DATA_DIR=$WAID_SOURCE/mock/data "
                         "WAID_DB_MOCK_FILE=$WAID_SOURCE/mock/data/waid_mock.db "
                         "$WAID_SOURCE/.venv-dbt/bin/dbt run "
                         "--profiles-dir $WAID_SOURCE/config "
                         "--project-dir $WAID_SOURCE/dbt "
                         "--target dev ; "
                         
                         "WAID_SIM_MODE=True "
                         "WAID_DATA_DIR=$WAID_SOURCE/mock/data "
                         "WAID_DB_MOCK_FILE=$WAID_SOURCE/mock/data/waid_mock.db "
                         "$WAID_SOURCE/.venv-dbt/bin/dbt run "
                         "--select ecowitt_records "
                         "--profiles-dir  $WAID_SOURCE/config "
                         "--project-dir $WAID_SOURCE/dbt "
                         "--target dev" 
                    ),
                "critical": False
            },
            
            {
                "desc": "SQLITE: show all table on main mock database",
                "cmd": "sqlite3 /home/alex/lab/waid-draft/mock/data/waid_mock.db \".tables\"",
                "critical": False
            },
            {
                "desc": "SQLITE: show SQL about a table...",
                "cmd": "sqlite3 $WAID_SOURCE/mock/data/waid_mock.db \"SELECT sql FROM sqlite_master "
                       "WHERE type='view' AND name='stg_matches';\"",
                "critical": False
            },
            {
                "desc": "SQLITE: RESET main mock database",
                "cmd": "rm -rf mock/data/waid_mock.db mock/data/waid_dbt_models.md ; "
                       "waid_init_main_db.py",
                "critical": True
            },
            {
                "desc": "SQLITE: DROP a specified table",
                "cmd": "sqlite3 $WAID_SOURCE/mock/data/waid_mock.db "
                       "\"DROP TABLE IF EXISTS inference_quality;\"",
                "critical": True
            },
            
                        
            
            
        ]
    },
    {
        "title": "2. DOCKER PC / HOST TARGETS",
        "context_rule": "docker_pc",
        "commands": [
            {
                "desc": "Exec ML Retrain inside waid_host container",
                "cmd": (
                    "docker exec -e WAID_SETUP_MODE=3 -it waid_host "
                    "python3 ./waid_orchestrate_lab.py --start-from waid_05_1_train_model"
                ),
                "critical": False
            },
            {
                "desc": "Check waid_host container logs",
                "cmd": "docker logs --tail 50 -f waid_host",
                "critical": False
            }
        ]
    },
    {
        "title": "3. DOCKER ARM SETUP & EXEC (ARM Reserved)",
        "context_rule": "docker_arm",
        "commands": [
            {
                "desc": "Batch Rebuild All Historical Tensors (11 Features)",
                "cmd": (
                    "nohup docker exec -e WAID_SETUP_MODE=3 waid_arm "
                    "bash src/utils/draft_execute_all_periods.sh waid_05_1_ml_tensors.py > waid_batch.log 2>&1 &"
                ),
                "critical": True
            },
            {
                "desc": "Full Setup and Retrain from scratch on ARM (WAID_SETUP_MODE=1)",
                "cmd": "docker exec -e WAID_SETUP_MODE=1 -it waid_arm python3 ./waid_orchestrate_lab.py",
                "critical": True
            },
            {
                "desc": "Exec ML Retrain inside waid_arm container (WAID_SETUP_MODE=3)",
                "cmd": (
                    "docker exec -e WAID_SETUP_MODE=3 -it waid_arm "
                    "python3 ./waid_orchestrate_lab.py --start-from waid_05_2_ml_train.py"
                ),
                "critical": False
            },
            {
                "desc": "Build local ARM Docker image",
                "cmd": "docker build -t waid-arm:latest -f $WAID_SOURCE/Dockerfile.arm $WAID_SOURCE",
                "critical": True
            },
            {
                "desc": "Show current log from waid_arm container",
                "cmd": "log_filename = f\"waid_pipeline_{datetime.now().strftime('%Y%m%d')}.log\"; tail -f log_filename",
                "critical": False
            },
        ]
    }
]


def validate_context(rule: str, in_docker: bool, on_arm: bool) -> tuple[bool, str]:
    """
    Validates if the command can be executed in the current context.
    @param rule: Section rule ("pc_only", "docker_arm", "docker_pc", "any").
    @param in_docker: Docker context flag.
    @param on_arm: ARM hardware context flag.
    @return: Tuple (Allowed: bool, ErrorMessage: str)
    """
    if rule == "pc_only" and (in_docker or on_arm):
        return False, "[WARN] Invalid option."

    if rule == "docker_arm" and not on_arm:
        return False, "[WARN] Invalid option."

    if rule == "docker_pc" and on_arm:
        return False, "[WARN] Invalid option."

    return True, ""


def execute_shell_command(cmd_str: str) -> None:
    """
    Executes arbitrary Bash command expanding environment variables.
    @param cmd_str: Bash command string to execute.
    """
    expanded_cmd = os.path.expandvars(cmd_str)
    print(f"\n🔶 [EXEC] > {expanded_cmd}\n")
    try:
        subprocess.run(expanded_cmd, shell=True, check=False)
    except Exception as e:
        print(f"[ERROR] Failure during execution: {e}")


def show_interactive_menu(request_number: int) -> None:
    """
    Dynamically generates the menu starting from the data structure.
    @param request_number: Option index requested or -1 for interactive selection.
    """
    in_docker = is_in_docker()
    on_arm = is_arm_host()

    option_map: Dict[str, tuple[Dict[str, Any], str]] = {}
    counter = 1
    for section in COMMAND_SECTIONS:
        for item in section["commands"]:
            key = str(counter)
            warn_tag = " (!)" if item.get("critical") else ""
            option_map[key] = (item, section["context_rule"])
            counter += 1
            
    counter = 1
    if request_number < 0:
        ctx_info = "DOCKER CONTAINER" if in_docker else ("ARM BOARD" if on_arm else "PC HOST")
        print("\n==================================================")
        print("          WAID OPERATIONS REGISTRY               ")
        print(f"   Current Context: [{ctx_info}]")
        print("==================================================")

        for section in COMMAND_SECTIONS:
            print(f"\n--- [ {section['title']} ] ---")
            for item in section["commands"]:
                key = str(counter)
                warn_tag = " (!)" if item.get("critical") else ""
                print(f" {key:>2}) {item['desc']}{warn_tag}")
                counter += 1

        print("\n--- [ SYSTEM ] ---")
        print("  0) Exit")

        choice = input("\nSelect option: ").strip()
    else:
        choice = str(request_number)
    
    if choice == "0":
        sys.exit(0)

    if choice in option_map:
        item, rule = option_map[choice]
        allowed, reason = validate_context(rule, in_docker, on_arm)

        if not allowed:
            print(f"\n[ERROR] Invalid context\n")
        else:
            if item.get("critical", False):
                if not confirm_critical_operation(item):
                    print("\n[INFO] Operation cancelled by user.\n")
                    return
            execute_shell_command(item["cmd"])
    else:
        print("\n[WARN] Invalid option.")


if __name__ == "__main__":
    # Read the argument and convert it to an integer
    try:
        input_request = int(sys.argv[1])
    except (IndexError, ValueError):
        input_request = -1
    
    # Calculate the total number of commands across all sections
    total_commands = sum(len(section["commands"]) for section in COMMAND_SECTIONS)

    if input_request > total_commands:
        print("\nNo valid input.\nPlease select a valid command\n")
        input_request = -1
    
    show_interactive_menu(input_request)