# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

### Smarter Scheduling

- Added feature that implements sorting logic based on start time of task and is able to folter results based on pet's name ans task completion status.
- It automates recurring tasks as a daily or weekly task is completed, a new instance is automatically created for next occurence. 
- It detect conflicts between tasks for the same pet or different pets for a Owner and adds Owner's preference to remove such conflicting tasks.
- Utilizes Owner's preference to avoid certain times for scheduling.

### Testing PawPal+

Run python -m pytest

The tests covers both happy paths and edge cases. Tests include tasks based on priorities, tasks sorted by time, tasks with exact same start times, back to back tasks with no conflicts, daily and weekly tasks creating a new instance for the next task, as-needed tasks with no follow up, filter based on pet with no tasks, and complete_task() for non existent pet, and testing owner's time availability with tasks.