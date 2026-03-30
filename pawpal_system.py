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
    preferred_time: str                   # morning | afternoon | evening | anytime
    frequency: str                        # daily | weekly | as-needed
    is_completed: bool = False

    def set_priority(self, level: int) -> None:
        """Update task priority (1–5)."""
        if not 1 <= level <= 5:
            raise ValueError(f"Priority must be between 1 and 5, got {level}.")
        self.priority = level

    def set_duration(self, minutes: int) -> None:
        """Update how long this task takes."""
        if minutes <= 0:
            raise ValueError(f"Duration must be a positive number of minutes, got {minutes}.")
        self.duration_minutes = minutes

    def mark_complete(self) -> None:
        """Mark the task as done for today."""
        self.is_completed = True

    def mark_incomplete(self) -> None:
        """Reset the task to not-done."""
        self.is_completed = False

    def get_details(self) -> dict:
        """Return a dictionary summary of the task's attributes."""
        return {
            "name": self.name,
            "task_type": self.task_type,
            "pet_name": self.pet_name,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "preferred_time": self.preferred_time,
            "frequency": self.frequency,
            "is_completed": self.is_completed,
        }


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
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove a task by name from this pet."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def get_medical_needs(self) -> list[str]:
        """Return the pet's list of medical conditions."""
        return self.medical_conditions

    def get_insurance_details(self) -> dict:
        """Return insurance info for this pet.

        Returns a dict with keys:
          - 'insured' (bool): whether the pet has coverage
          - 'provider' (str | None): insurance provider name, or None if uninsured
        """
        return {
            "insured": self.insurance is not None,
            "provider": self.insurance,
        }


# ---------------------------------------------------------------------------
# Owner — regular class (holds pets and preferences, has richer behaviour).
# ---------------------------------------------------------------------------
class Owner:
    def __init__(
        self,
        name: str,
        age: int,
        gender: str,
        available_hours_per_day: int,
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
        self.preferences[key] = value

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Unregister a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        return self.pets

    def get_available_time(self) -> int:
        """Return total available minutes per day (hours × 60)."""
        return self.available_hours_per_day * 60


# ---------------------------------------------------------------------------
# Scheduler — orchestrates plan generation; not a dataclass because it
# contains significant logic and mutable state built up across calls.
# ---------------------------------------------------------------------------

# Time-slot ordering used by prioritize_tasks: earlier in the day = lower index.
_TIME_SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "anytime": 3}


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
        task.pet_name = pet.name
        pet.add_task(task)

    def edit_task(self, pet_name: str, task_name: str, updates: dict) -> None:
        """Update attributes of a task identified by both pet name and task name.
        Using both avoids ambiguity when multiple pets share a task name
        (e.g. two pets both have a 'Feed' task).
        """
        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            raise ValueError(f"No pet named '{pet_name}' found.")

        task = next((t for t in pet.tasks if t.name == task_name), None)
        if task is None:
            raise ValueError(f"No task named '{task_name}' found for pet '{pet_name}'.")

        for key, value in updates.items():
            if not hasattr(task, key):
                raise ValueError(f"Task has no attribute '{key}'.")
            setattr(task, key, value)

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks first by preferred_time bucket
        (morning → afternoon → evening → anytime), then by priority (1 = highest)
        within each bucket. Returns the ordered list.
        """
        return sorted(
            tasks,
            key=lambda t: (_TIME_SLOT_ORDER.get(t.preferred_time, 3), t.priority),
        )

    def check_constraints(self, current_total: int, candidate: Task) -> bool:
        """Return True if adding candidate keeps the plan within the owner's
        available time budget. Called incrementally inside generate_plan() so
        low-priority tasks are dropped when the budget is exhausted rather
        than forcing a full rebuild.
        """
        return current_total + candidate.duration_minutes <= self.owner.get_available_time()

    def generate_plan(self) -> list[ScheduledTask]:
        """Build daily_plan from owner → pets → tasks.
        1. Collect all tasks across all pets.
        2. Call prioritize_tasks() to order by time slot then priority.
        3. Add tasks one-by-one, calling check_constraints() before each;
           skip tasks that would exceed the time budget.
        4. Wrap each accepted task in a ScheduledTask with a reason string.
        Returns the completed daily_plan.
        """
        all_tasks: list[Task] = []
        for pet in self.owner.pets:
            all_tasks.extend(pet.get_tasks())

        ordered = self.prioritize_tasks(all_tasks)

        self.daily_plan = []
        total_minutes = 0

        for task in ordered:
            if self.check_constraints(total_minutes, task):
                reason = (
                    f"Scheduled in the {task.preferred_time} slot "
                    f"(priority {task.priority}, {task.duration_minutes} min). "
                    f"Time used: {total_minutes + task.duration_minutes}/"
                    f"{self.owner.get_available_time()} min."
                )
                self.daily_plan.append(ScheduledTask(task=task, pet_name=task.pet_name, reason=reason))
                total_minutes += task.duration_minutes
            else:
                # Task skipped — budget exhausted for this slot
                continue

        return self.daily_plan

    def display_plan(self) -> None:
        """Print the daily plan in a human-readable format, drawing reason
        strings from each ScheduledTask entry.
        """
        if not self.daily_plan:
            print("No plan generated yet. Run generate_plan() first.")
            return

        print(f"\n{'='*50}")
        print(f"  PawPal+ Daily Plan — {self.date}")
        print(f"  Owner: {self.owner.name}  |  Budget: {self.owner.get_available_time()} min")
        print(f"{'='*50}")

        for i, entry in enumerate(self.daily_plan, start=1):
            t = entry.task
            status = "Done" if t.is_completed else "Pending"
            print(f"\n{i}. [{t.preferred_time.upper()}] {t.name} — {entry.pet_name}")
            print(f"   Type: {t.task_type}  |  Duration: {t.duration_minutes} min  |  Priority: {t.priority}  |  Status: {status}")
            print(f"   Why: {entry.reason}")

        total = sum(e.task.duration_minutes for e in self.daily_plan)
        print(f"\n{'='*50}")
        print(f"  Total scheduled: {total} min / {self.owner.get_available_time()} min available")
        print(f"{'='*50}\n")

    def explain_reasoning(self) -> str:
        """Return a single string summarising why the plan was ordered and
        filtered the way it was, derived from ScheduledTask.reason entries.
        """
        if not self.daily_plan:
            return "No plan generated yet. Run generate_plan() first."

        lines = [f"Daily plan reasoning for {self.owner.name} on {self.date}:\n"]
        for i, entry in enumerate(self.daily_plan, start=1):
            lines.append(f"  {i}. {entry.task.name} ({entry.pet_name}): {entry.reason}")

        total = sum(e.task.duration_minutes for e in self.daily_plan)
        lines.append(
            f"\nTasks were sorted by time-of-day slot first (morning → afternoon → "
            f"evening → anytime), then by priority (1 = highest) within each slot. "
            f"Tasks were dropped once the {self.owner.get_available_time()}-minute budget "
            f"was reached. Total scheduled: {total} min."
        )
        return "\n".join(lines)