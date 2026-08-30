"""Tests for dynamic IMPLEMENTATION_PLAN.md generation and bidirectional markdown parsing."""
import os
import pytest
from core.planner.planner import Planner, PlanStep, ExecutionPlan
from core.goal_engine.engine import StructuredTask


def test_14_section_plan_markdown_generation():
    steps = [
        PlanStep(
            id="s1",
            step_index=0,
            objective="Scaffold project workspace directory",
            agent="FileSystemAgent",
            tool="filesystem",
            input_data={"operation": "create_folder", "path": "K:\\TestApp"},
            expected_result="Directory created",
            verification_condition="os.path.isdir('K:\\TestApp')"
        ),
        PlanStep(
            id="s2",
            step_index=1,
            objective="Synthesize main.py entry point",
            agent="CodingAgent",
            tool="filesystem",
            input_data={"operation": "create_file", "path": "K:\\TestApp\\main.py", "content": "print('hello')"},
            expected_result="File created",
            verification_condition="os.path.isfile('K:\\TestApp\\main.py')"
        )
    ]

    task = StructuredTask(
        goal="Create an automated PDF invoice generator",
        intent="code_generation",
        requirements=["Generate PDF invoices", "Include customer address"],
        dependencies=["Python 3.12", "ReportLab"]
    )

    plan_md = Planner.generate_implementation_plan_markdown(
        goal="Create an automated PDF invoice generator",
        target_dir="K:\\TestApp",
        steps=steps,
        structured_task=task,
        files_to_create=["main.py", "invoices.py"],
        dependencies=["ReportLab", "Python 3.12"],
        commands=["python main.py"]
    )

    # Verify key sections
    assert "# Implementation Plan" in plan_md
    assert "## Goal" in plan_md
    assert "## Current State" in plan_md
    assert "## Requirements" in plan_md
    assert "## Assumptions" in plan_md
    assert "## Architecture" in plan_md
    assert "## Files To Create" in plan_md
    assert "## Files To Modify" in plan_md
    assert "## Dependencies" in plan_md
    assert "## Commands" in plan_md
    assert "## Execution Steps" in plan_md
    assert "## Risks" in plan_md
    assert "## Permission Requirements" in plan_md
    assert "## Testing Strategy" in plan_md
    assert "## Verification Strategy" in plan_md
    assert "## Rollback Strategy" in plan_md

    # Check content
    assert "PDF invoice generator" in plan_md
    assert "ReportLab" in plan_md


def test_bidirectional_markdown_parsing():
    sample_markdown = """# Implementation Plan

## Goal
Build a weather CLI in Python

## Current State
Workspace: K:\\WeatherCLI

## Execution Steps
1. **[FILESYSTEM]** Create project root directory at K:\\WeatherCLI
2. **[FILESYSTEM]** Synthesize weather_cli.py with open-meteo integration
3. **[POWERSHELL]** Run python weather_cli.py --city London

## Risks
None
"""
    parsed_plan = Planner.parse_plan_from_markdown(
        markdown_content=sample_markdown,
        task_id="task-test-123",
        target_dir="K:\\WeatherCLI"
    )

    assert parsed_plan.task_id == "task-test-123"
    assert parsed_plan.goal == "Build a weather CLI in Python"
    assert len(parsed_plan.steps) == 3
    assert parsed_plan.steps[0].tool == "filesystem"
    assert parsed_plan.steps[1].tool == "filesystem"
    assert parsed_plan.steps[2].tool == "powershell"
    assert "weather_cli.py" in parsed_plan.steps[1].objective
