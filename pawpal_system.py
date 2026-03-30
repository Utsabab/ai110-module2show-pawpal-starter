from dataclasses import dataclass, field, replace
from datetime import date, timedelta
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
    start_time: Optional[str] = None     # "HH:MM" clock time within the slot, e.g. "08:30"
    due_date: Optional[str] = None       # ISO "YYYY-MM-DD"; set automatically on recurrence
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
            "start_time": self.start_time,
            "due_date": self.due_date,
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
    pet_type: str
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

# Realistic minute budget per slot — used by detect_conflicts() for untimed tasks.
_SLOT_BUDGET_MINUTES = {"morning": 240, "afternoon": 240, "evening": 180, "anytime": 60}


def _to_minutes(hhmm: str) -> int:
    """Convert 'HH:MM' to total minutes since midnight (e.g. '08:30' → 510)."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _to_hhmm(minutes: int) -> str:
    """Convert total minutes since midnight back to 'HH:MM' (e.g. 510 → '08:30')."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


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

    def complete_task(self, pet_name: str, task_name: str) -> Optional[Task]:
        """Mark a task complete and, for recurring tasks, register the next occurrence.

        - Finds the task on the named pet and calls mark_complete().
        - If frequency is 'daily'  → next occurrence due_date = scheduler.date + 1 day.
        - If frequency is 'weekly' → next occurrence due_date = scheduler.date + 7 days.
        - 'as-needed' tasks are marked done with no follow-up created.

        The next occurrence is a fresh Task (is_completed=False, new due_date) added
        to the same pet via add_task(), ready to be picked up by the next
        generate_plan() call.

        Returns the newly created Task if one was made, otherwise None.
        """
        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            raise ValueError(f"No pet named '{pet_name}' found.")

        task = next((t for t in pet.tasks if t.name == task_name), None)
        if task is None:
            raise ValueError(f"No task named '{task_name}' found for pet '{pet_name}'.")

        task.mark_complete()

        if task.frequency not in ("daily", "weekly"):
            return None

        days_ahead = 1 if task.frequency == "daily" else 7
        next_due = (date.fromisoformat(self.date) + timedelta(days=days_ahead)).isoformat()

        next_task = replace(task, is_completed=False, due_date=next_due)
        self.add_task(pet, next_task)
        return next_task

    def prioritize_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks first by preferred_time bucket
        (morning → afternoon → evening → anytime), then by priority (1 = highest)
        within each bucket. Returns the ordered list.
        """
        return sorted(
            tasks,
            key=lambda t: (_TIME_SLOT_ORDER.get(t.preferred_time, 3), t.priority),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by exact clock time within their time slot.

        Sort key (three levels):
          1. Slot bucket  — morning(0) → afternoon(1) → evening(2) → anytime(3)
          2. start_time   — "HH:MM" string; tasks without a start_time ("") sort
                            before timed tasks so they appear at the top of each slot.
          3. priority     — 1 (highest) within ties at the same slot + time.

        Use this instead of prioritize_tasks() when tasks carry explicit start_time
        values and you need precise intra-slot ordering (e.g. "08:00 Hip Med" before
        "08:30 Morning Walk" even though both are priority 1 in the morning slot).
        """
        return sorted(
            tasks,
            key=lambda t: (
                _TIME_SLOT_ORDER.get(t.preferred_time, 3),
                t.start_time or "",   # "" < any "HH:MM", so untimed tasks sort first
                t.priority,
            ),
        )

    def filter_by_pet(self, pet_name: str) -> list[ScheduledTask]:
        """Return only the scheduled entries that belong to the named pet.

        Comparison is case-insensitive so 'luna' and 'Luna' both match.
        Returns an empty list if the pet has no tasks in the current plan
        or if generate_plan() has not been run yet.
        """
        target = pet_name.strip().lower()
        return [e for e in self.daily_plan if e.pet_name.lower() == target]

    def filter_by_status(self, completed: bool) -> list[ScheduledTask]:
        """Return scheduled entries whose completion status matches the flag.

        Pass completed=True  → tasks already marked done.
        Pass completed=False → tasks still pending.
        """
        return [e for e in self.daily_plan if e.task.is_completed == completed]

    def detect_conflicts(self) -> list[str]:
        """Scan daily_plan for scheduling conflicts and return warning strings.

        Two detection strategies are applied independently:

        1. Timed overlap (tasks that carry a start_time):
           Converts each task's start_time to minutes since midnight and computes
           its end = start + duration_minutes.  Every pair of timed tasks is checked
           with the standard interval-overlap test:
               a.start < b.end  AND  b.start < a.end
           A warning is emitted for every overlapping pair, regardless of whether
           the tasks belong to the same pet or different pets.

        2. Slot overload (tasks without a start_time):
           Groups untimed tasks by preferred_time slot and sums their durations.
           If the total for a slot exceeds _SLOT_BUDGET_MINUTES for that slot a
           warning is emitted.  This is a lightweight heuristic — it cannot detect
           precise overlaps without clock times, but it flags obviously overloaded
           slots before the owner's day begins.

        Returns an empty list when no conflicts are found.  Warnings are plain
        strings so callers can print, log, or surface them in a UI without the
        method itself crashing the program.
        """
        warnings: list[str] = []

        timed   = [e for e in self.daily_plan if e.task.start_time]
        untimed = [e for e in self.daily_plan if not e.task.start_time]

        # ── Strategy 1: exact overlap between timed tasks ───────────────────
        for i, a in enumerate(timed):
            a_start = _to_minutes(a.task.start_time)
            a_end   = a_start + a.task.duration_minutes
            for b in timed[i + 1:]:
                b_start = _to_minutes(b.task.start_time)
                b_end   = b_start + b.task.duration_minutes
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"CONFLICT: '{a.task.name}' ({a.pet_name}, "
                        f"{a.task.start_time}–{_to_hhmm(a_end)}) overlaps with "
                        f"'{b.task.name}' ({b.pet_name}, "
                        f"{b.task.start_time}–{_to_hhmm(b_end)})."
                    )

        # ── Strategy 2: slot overload for untimed tasks ──────────────────────
        from collections import defaultdict
        slot_totals: dict[str, int] = defaultdict(int)
        for e in untimed:
            slot_totals[e.task.preferred_time] += e.task.duration_minutes
        for slot, total in slot_totals.items():
            budget = _SLOT_BUDGET_MINUTES.get(slot, 120)
            if total > budget:
                warnings.append(
                    f"OVERLOAD: {slot.capitalize()} slot has {total} min of untimed "
                    f"tasks but only {budget} min are realistic for that slot."
                )

        return warnings

    def check_constraints(self, current_total: int, candidate: Task) -> bool:
        """Return True if adding candidate keeps the plan within the owner's
        available time budget. Called incrementally inside generate_plan() so
        low-priority tasks are dropped when the budget is exhausted rather
        than forcing a full rebuild.
        """
        return current_total + candidate.duration_minutes <= self.owner.get_available_time()

    def generate_plan(self, sort_mode: str = "priority") -> list[ScheduledTask]:
        """Build daily_plan from owner → pets → tasks, honouring owner preferences.

        Parameters
        ----------
        sort_mode : str
            Controls the order in which tasks compete for the time budget:
            "priority" (default) — slot bucket first, then priority number
                                   (1 = highest).  Use when importance should
                                   determine what gets a slot.
            "clock"             — slot bucket first, then start_time ("HH:MM"),
                                   then priority.  Use when the real-world clock
                                   order matters more than abstract importance,
                                   e.g. a vet appointment at 09:00 must go first
                                   regardless of its priority number.
            The chosen mode is recorded in every ScheduledTask.reason string so
            the plan is self-documenting.

        Steps:
        1. Read owner preferences (avoid_time, no_concurrent_pets).
        2. Collect all tasks across all pets; drop any in an avoided slot.
        3. Sort by the chosen sort_mode.
        4. Add tasks one-by-one:
             a. check_constraints() — skip if time budget exceeded.
             b. cross-pet overlap check — skip if no_concurrent_pets blocks it.
             c. Accept: wrap in ScheduledTask with a reason string that records
                the sort mode and which preferences were active.
        Returns the completed daily_plan.
        """
        if sort_mode not in ("priority", "clock"):
            raise ValueError(f"sort_mode must be 'priority' or 'clock', got '{sort_mode}'.")

        # ── Read preferences ────────────────────────────────────────────────
        avoid = self.owner.preferences.get("avoid_time", [])
        if isinstance(avoid, str):
            avoid = [avoid]
        no_concurrent = self.owner.preferences.get("no_concurrent_pets", False)

        # ── Collect and pre-filter tasks ────────────────────────────────────
        all_tasks: list[Task] = []
        for pet in self.owner.pets:
            all_tasks.extend(pet.get_tasks())

        if avoid:
            all_tasks = [t for t in all_tasks if t.preferred_time not in avoid]

        ordered = (
            self.sort_by_time(all_tasks)
            if sort_mode == "clock"
            else self.prioritize_tasks(all_tasks)
        )

        # ── Build the plan ──────────────────────────────────────────────────
        self.daily_plan = []
        total_minutes = 0

        for task in ordered:
            if not self.check_constraints(total_minutes, task):
                continue

            # Preference: no_concurrent_pets — block cross-pet time overlaps.
            # Only applies when the candidate has an explicit start_time; untimed
            # tasks cannot be precisely compared so they pass through unchecked.
            if no_concurrent and task.start_time:
                t_start = _to_minutes(task.start_time)
                t_end   = t_start + task.duration_minutes
                blocked_by: Optional[str] = None
                for entry in self.daily_plan:
                    if entry.pet_name == task.pet_name:
                        continue                          # same pet — not a concern
                    if not entry.task.start_time:
                        continue                          # untimed — skip
                    e_start = _to_minutes(entry.task.start_time)
                    e_end   = e_start + entry.task.duration_minutes
                    if t_start < e_end and e_start < t_end:
                        blocked_by = entry.task.name
                        break
                if blocked_by:
                    continue                              # drop conflicting task

            # ── Build reason string ─────────────────────────────────────────
            notes: list[str] = [
                f"sorted by {sort_mode}",
            ]
            if avoid:
                notes.append(f"avoided slots: {', '.join(avoid)}")
            if no_concurrent:
                notes.append("no concurrent pets enforced")

            reason = (
                f"Scheduled in the {task.preferred_time} slot "
                f"(priority {task.priority}, {task.duration_minutes} min). "
                f"Time used: {total_minutes + task.duration_minutes}/"
                f"{self.owner.get_available_time()} min. "
                f"[{'; '.join(notes)}]"
            )
            self.daily_plan.append(ScheduledTask(task=task, pet_name=task.pet_name, reason=reason))
            total_minutes += task.duration_minutes

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