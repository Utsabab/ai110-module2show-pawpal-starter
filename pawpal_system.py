from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Task — a dataclass because it is a plain data container with no behaviour
# that depends on other classes.  Priority 1 = highest, 5 = lowest.
# ---------------------------------------------------------------------------
@dataclass
class Task:
    name: str
    task_type: str                        # walk | feed | groom | med | enrichment
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

    def set_preference(self, key: str, value) -> None:
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
        self.date = date                  # ISO format: "YYYY-MM-DD"
        self.daily_plan: list[Task] = []
        self._reasoning: list[str] = []  # internal log used by explain_reasoning()

    def add_task(self, pet: Pet, task: Task) -> None:
        """Add a task to a specific pet and register it with the scheduler."""
        pass

    def edit_task(self, task_name: str, updates: dict) -> None:
        """Update attributes of an existing task by name."""
        pass

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority and preferred_time; return the ordered list."""
        pass

    def check_constraints(self) -> bool:
        """Return True if the current daily_plan fits within the owner's available time."""
        pass

    def generate_plan(self) -> list[Task]:
        """
        Build and store daily_plan from all pet tasks.
        Considers priority, preferred_time, and owner's available_hours_per_day.
        Populates self._reasoning with explanations for each scheduling decision.
        """
        pass

    def display_plan(self) -> None:
        """Print the daily plan in a human-readable format."""
        pass

    def explain_reasoning(self) -> str:
        """Return a string explaining why the plan was ordered the way it was."""
        pass