import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task


def make_task(name="Walk", preferred_time="morning", frequency="daily"):
    """Helper to create a Task with required fields filled in."""
    return Task(
        name=name,
        task_type="walk",
        pet_name="Luna",
        duration_minutes=30,
        priority=2,
        preferred_time=preferred_time,
        frequency=frequency,
    )


def make_pet():
    """Helper to create a basic Pet."""
    return Pet(name="Luna", age=3, breed="Golden Retriever", gender="female")


# ---------------------------------------------------------------------------
# Test 1: mark_complete() changes is_completed from False to True
# ---------------------------------------------------------------------------
def test_mark_complete_changes_status():
    task = make_task()
    assert task.is_completed is False, "Task should start as incomplete."
    task.mark_complete()
    assert task.is_completed is True, "Task should be complete after mark_complete()."


# ---------------------------------------------------------------------------
# Test 2: add_task() increases the pet's task count by 1
# ---------------------------------------------------------------------------
def test_add_task_increases_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0, "Pet should start with no tasks."
    pet.add_task(make_task(name="Walk"))
    assert len(pet.get_tasks()) == 1, "Pet should have 1 task after add_task()."
    pet.add_task(make_task(name="Feed"))
    assert len(pet.get_tasks()) == 2, "Pet should have 2 tasks after second add_task()."