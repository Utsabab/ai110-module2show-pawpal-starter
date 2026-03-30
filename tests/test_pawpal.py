import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pawpal_system import Pet, Task, Owner, Scheduler, ScheduledTask


def make_task(name="Walk", preferred_time="morning", frequency="daily",
              priority=2, duration_minutes=30, start_time=None):
    """Helper to create a Task with required fields filled in."""
    return Task(
        name=name,
        task_type="walk",
        pet_name="Luna",
        duration_minutes=duration_minutes,
        priority=priority,
        preferred_time=preferred_time,
        frequency=frequency,
        start_time=start_time,
    )


def make_pet():
    """Helper to create a basic Pet."""
    return Pet(name="Luna", age=3, pet_type="Golden Retriever", gender="female")


def make_scheduler(available_hours=8, date_str="2026-03-30"):
    """Helper to create a Scheduler with one pet (Luna) already attached."""
    owner = Owner(name="Alex", age=30, gender="female", available_hours_per_day=available_hours)
    pet = Pet(name="Luna", age=3, pet_type="Golden Retriever", gender="female")
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner, date=date_str)
    return scheduler, owner, pet


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


# ---------------------------------------------------------------------------
# Test 3: prioritize_tasks() orders tasks by slot (morning → afternoon → evening)
# ---------------------------------------------------------------------------
def test_prioritize_tasks_sorts_slots():
    scheduler, _, _ = make_scheduler()
    evening = make_task(name="Evening Walk", preferred_time="evening")
    morning = make_task(name="Morning Feed", preferred_time="morning")
    afternoon = make_task(name="Afternoon Groom", preferred_time="afternoon")

    result = scheduler.prioritize_tasks([evening, morning, afternoon])

    slots = [t.preferred_time for t in result]
    assert slots == ["morning", "afternoon", "evening"], (
        "Tasks should be sorted morning → afternoon → evening regardless of input order."
    )


# ---------------------------------------------------------------------------
# Test 4: sort_by_time() places untimed tasks before timed tasks in the same slot
# ---------------------------------------------------------------------------
def test_sort_by_time_untimed_before_timed():
    scheduler, _, _ = make_scheduler()
    timed = make_task(name="Timed Walk", preferred_time="morning", start_time="08:30")
    untimed = make_task(name="Untimed Feed", preferred_time="morning", start_time=None)

    result = scheduler.sort_by_time([timed, untimed])

    assert result[0].name == "Untimed Feed", "Untimed task should sort before timed task in the same slot."
    assert result[1].name == "Timed Walk"


# ---------------------------------------------------------------------------
# Test 5: detect_conflicts() flags two tasks with the exact same start_time
# ---------------------------------------------------------------------------
def test_exact_same_start_time_conflict():
    scheduler, _, _ = make_scheduler()
    task_a = make_task(name="Task A", start_time="08:00", duration_minutes=30)
    task_b = make_task(name="Task B", start_time="08:00", duration_minutes=30)
    scheduler.daily_plan = [
        ScheduledTask(task=task_a, pet_name="Luna", reason="test"),
        ScheduledTask(task=task_b, pet_name="Luna", reason="test"),
    ]

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1, "One conflict warning expected for two tasks at the same start time."
    assert "CONFLICT" in warnings[0], "Warning should be labelled CONFLICT."
    assert "Task A" in warnings[0] and "Task B" in warnings[0]


# ---------------------------------------------------------------------------
# Test 6: detect_conflicts() does NOT flag tasks that are back-to-back (no overlap)
# ---------------------------------------------------------------------------
def test_back_to_back_no_conflict():
    scheduler, _, _ = make_scheduler()
    task_a = make_task(name="Task A", start_time="08:00", duration_minutes=30)  # ends 08:30
    task_b = make_task(name="Task B", start_time="08:30", duration_minutes=30)  # starts 08:30
    scheduler.daily_plan = [
        ScheduledTask(task=task_a, pet_name="Luna", reason="test"),
        ScheduledTask(task=task_b, pet_name="Luna", reason="test"),
    ]

    warnings = scheduler.detect_conflicts()

    assert warnings == [], "Back-to-back tasks that share only a boundary should not conflict."


# ---------------------------------------------------------------------------
# Test 7: complete_task() sets due_date to tomorrow for a daily task
# ---------------------------------------------------------------------------
def test_daily_recurrence_due_date():
    scheduler, _, pet = make_scheduler(date_str="2026-03-30")
    pet.add_task(make_task(name="Walk", frequency="daily"))

    next_task = scheduler.complete_task("Luna", "Walk")

    assert next_task is not None, "Daily task should produce a follow-up task."
    assert next_task.due_date == "2026-03-31", "Daily recurrence should be due the next day."
    assert next_task.is_completed is False, "Next occurrence should start as incomplete."


# ---------------------------------------------------------------------------
# Test 8: complete_task() sets due_date to 7 days ahead for a weekly task
# ---------------------------------------------------------------------------
def test_weekly_recurrence_due_date():
    scheduler, _, pet = make_scheduler(date_str="2026-03-30")
    pet.add_task(make_task(name="Groom", frequency="weekly"))

    next_task = scheduler.complete_task("Luna", "Groom")

    assert next_task is not None, "Weekly task should produce a follow-up task."
    assert next_task.due_date == "2026-04-06", "Weekly recurrence should be due 7 days later."
    assert next_task.is_completed is False, "Next occurrence should start as incomplete."


# ---------------------------------------------------------------------------
# Test 9: complete_task() returns None and adds no new task for an as-needed task
# ---------------------------------------------------------------------------
def test_as_needed_no_recurrence():
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(name="Vet Visit", frequency="as-needed"))
    task_count_before = len(pet.get_tasks())

    result = scheduler.complete_task("Luna", "Vet Visit")

    assert result is None, "as-needed task should return None (no follow-up)."
    assert len(pet.get_tasks()) == task_count_before, "No new task should be added for as-needed frequency."


# ---------------------------------------------------------------------------
# Test 10: filter_by_pet() returns an empty list for a pet with no scheduled tasks
# ---------------------------------------------------------------------------
def test_pet_with_no_tasks():
    scheduler, owner, _ = make_scheduler()
    ghost = Pet(name="Ghost", age=1, pet_type="Husky", gender="male")
    owner.add_pet(ghost)

    scheduler.generate_plan()
    result = scheduler.filter_by_pet("Ghost")

    assert result == [], "A pet with no tasks should return an empty list from filter_by_pet()."


# ---------------------------------------------------------------------------
# Test 11: complete_task() raises ValueError when the pet name does not exist
# ---------------------------------------------------------------------------
def test_complete_task_unknown_pet():
    scheduler, _, _ = make_scheduler()

    with pytest.raises(ValueError):
        scheduler.complete_task("NoSuchPet", "Walk")


# ---------------------------------------------------------------------------
# Test 12: detect_conflicts() slot overload — exactly at budget is fine,
#           one minute over triggers a warning
# ---------------------------------------------------------------------------
def test_slot_budget_boundary():
    scheduler, _, _ = make_scheduler()

    # Morning budget is 240 min — fill it exactly (8 × 30 min untimed tasks)
    at_limit = [
        ScheduledTask(
            task=make_task(name=f"Task{i}", duration_minutes=30, start_time=None),
            pet_name="Luna",
            reason="test",
        )
        for i in range(8)  # 8 × 30 = 240 min
    ]
    scheduler.daily_plan = at_limit
    assert scheduler.detect_conflicts() == [], "Exactly at the morning budget should produce no overload warning."

    # Add one more minute to push over the limit
    over_limit = at_limit + [
        ScheduledTask(
            task=make_task(name="OneMore", duration_minutes=1, start_time=None),
            pet_name="Luna",
            reason="test",
        )
    ]
    scheduler.daily_plan = over_limit
    warnings = scheduler.detect_conflicts()
    assert any("OVERLOAD" in w for w in warnings), "Exceeding the morning budget should produce an OVERLOAD warning."