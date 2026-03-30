from dataclasses import dataclass, field
from typing import Optional, Any


# ---------------------------------------------------------------------------
# Task — plain data container.
# pet_name records which pet this task belongs to so the association is
# preserved once tasks are flattened into daily_plan.
# Priority 1 = highest, 5 = lowest.
# ---------------------------------------------------------------------------
@dataclass
class Task:
    name: str
    task_type: str                        # walk | feed | groom | med | enrichment
    pet_name: str                         # which pet this task belongs to
    duration_minutes: int
    priority: int                         # 1 (highest) – 5 (lowest)
    preferred_time: str = "anytime"       # morning | afternoon | evening | anytime
    frequency: str = "daily"             # daily | weekly | as-needed
    is_completed: bool = False

    def set_priority(self, level: int) -> None:
        """Update task priority (1–5)."""
        pass

    def set_duration(self, minutes: int) -> None:
        """Update how long this task takes."""
        pass

    def mark_complete(self) -> None:
        """Mark the task as done for today."""
        pass

    def mark_incomplete(self) -> None:
        """Reset the task to not-done."""
        pass

    def get_details(self) -> dict:
        """Return a dictionary summary of the task's attributes."""
        pass


# ---------------------------------------------------------------------------
# ScheduledTask — pairs a Task with its pet and scheduling reason so
# display_plan() and explain_reasoning() always have full context without
# needing to re-run generate_plan().
# ---------------------------------------------------------------------------
@dataclass
class ScheduledTask:
    task: Task
    pet_name: str
    reason: str                           # human-readable explanation for this slot


# ---------------------------------------------------------------------------
# Pet — a dataclass for the core attributes; behaviour methods added below.
# ---------------------------------------------------------------------------
@dataclass
class Pet:
    name: str
    age: int
    breed: str
    gender: str
    medical_conditions: list[str] = field(default_factory=list)
    insurance: Optional[str] = None       # insurance provider name, or None if uninsured
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a new task to this pet."""
        pass

    def remove_task(self, task_name: str) -> None:
        """Remove a task by name from this pet."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        pass

    def get_medical_needs(self) -> list[str]:
        """Return the pet's list of medical conditions."""
        pass

    def get_insurance_details(self) -> dict:
        """Return insurance info for this pet.

        Returns a dict with keys:
          - 'insured' (bool): whether the pet has coverage
          - 'provider' (str | None): insurance provider name, or None if uninsured
        """
        pass


# ---------------------------------------------------------------------------
# Owner — regular class (holds pets and preferences, has richer behaviour).
# ---------------------------------------------------------------------------
class Owner:
    def __init__(
        self,
        name: str,
        age: int,
        gender: str,
        available_hours_per_day: int = 2,
        preferences: Optional[dict] = None,
    ) -> None:
        self.name = name
        self.age = age
        self.gender = gender
        self.available_hours_per_day = available_hours_per_day
        self.preferences: dict = preferences or {}
        self.pets: list[Pet] = []

    def set_preference(self, key: str, value: Any) -> None:
        """Set or update an owner preference (e.g. preferred_walk_time='morning')."""
        pass

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        pass

    def remove_pet(self, pet_name: str) -> None:
        """Unregister a pet by name."""
        pass

    def get_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        pass

    def get_available_time(self) -> int:
        """Return total available minutes per day (hours × 60)."""
        pass


# ---------------------------------------------------------------------------
# Scheduler — orchestrates plan generation; not a dataclass because it
# contains significant logic and mutable state built up across calls.
# ---------------------------------------------------------------------------
class Scheduler:
    def __init__(self, owner: Owner, date: str) -> None:
        self.owner = owner
        self.date = date                              # ISO format: "YYYY-MM-DD"
        self.daily_plan: list[ScheduledTask] = []    # reason stored per entry via ScheduledTask

    def add_task(self, pet: Pet, task: Task) -> None:
        """Write a task to the pet (single source of truth).
        generate_plan() pulls from owner → pets → tasks, so tasks must live
        on the pet — do not write directly to daily_plan here.
        """
        pass

    def edit_task(self, pet_name: str, task_name: str, updates: dict) -> None:
        """Update attributes of a task identified by both pet name and task name.
        Using both avoids ambiguity when multiple pets share a task name
        (e.g. two pets both have a 'Feed' task).
        """
        pass

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks first by preferred_time bucket
        (morning → afternoon → evening → anytime), then by priority (1 = highest)
        within each bucket. Returns the ordered list.
        """
        pass

    def check_constraints(self, current_total: int, candidate: Task) -> bool:
        """Return True if adding candidate keeps the plan within the owner's
        available time budget. Called incrementally inside generate_plan() so
        low-priority tasks are dropped when the budget is exhausted rather
        than forcing a full rebuild.
        """
        pass

    def generate_plan(self) -> list[ScheduledTask]:
        """Build daily_plan from owner → pets → tasks.
        1. Collect all tasks across all pets.
        2. Call prioritize_tasks() to order by time slot then priority.
        3. Add tasks one-by-one, calling check_constraints() before each;
           skip tasks that would exceed the time budget.
        4. Wrap each accepted task in a ScheduledTask with a reason string.
        Returns the completed daily_plan.
        """
        pass

    def display_plan(self) -> None:
        """Print the daily plan in a human-readable format, drawing reason
        strings from each ScheduledTask entry.
        """
        pass

    def explain_reasoning(self) -> str:
        """Return a single string summarising why the plan was ordered and
        filtered the way it was, derived from ScheduledTask.reason entries.
        """
        pass
