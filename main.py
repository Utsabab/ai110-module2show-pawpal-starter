from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# 1. Create Owner
# ---------------------------------------------------------------------------
owner = Owner(
    name="Alex",
    age=28,
    gender="female",
    available_hours_per_day=3,
)

# ---------------------------------------------------------------------------
# 2. Create two Pets
# ---------------------------------------------------------------------------
luna = Pet(
    name="Luna",
    age=3,
    breed="Golden Retriever",
    gender="female",
    medical_conditions=["hip dysplasia"],
    insurance="Trupanion",
)

max = Pet(
    name="Max",
    age=5,
    breed="Tabby Cat",
    gender="male",
)

# Register pets with the owner
owner.add_pet(luna)
owner.add_pet(max)

# ---------------------------------------------------------------------------
# 3. Create Scheduler and add Tasks with different times
# ---------------------------------------------------------------------------
today = date.today().isoformat()
scheduler = Scheduler(owner=owner, date=today)

# Luna's tasks
scheduler.add_task(luna, Task(
    name="Morning Walk",
    task_type="walk",
    pet_name="Luna",
    duration_minutes=30,
    priority=1,
    preferred_time="morning",
    frequency="daily",
))

scheduler.add_task(luna, Task(
    name="Hip Med",
    task_type="med",
    pet_name="Luna",
    duration_minutes=5,
    priority=1,
    preferred_time="morning",
    frequency="daily",
))

scheduler.add_task(luna, Task(
    name="Evening Walk",
    task_type="walk",
    pet_name="Luna",
    duration_minutes=20,
    priority=2,
    preferred_time="evening",
    frequency="daily",
))

scheduler.add_task(luna, Task(
    name="Grooming",
    task_type="groom",
    pet_name="Luna",
    duration_minutes=25,
    priority=4,
    preferred_time="afternoon",
    frequency="weekly",
))

# Max's tasks
scheduler.add_task(max, Task(
    name="Feeding",
    task_type="feed",
    pet_name="Max",
    duration_minutes=10,
    priority=1,
    preferred_time="morning",
    frequency="daily",
))

scheduler.add_task(max, Task(
    name="Enrichment Play",
    task_type="enrichment",
    pet_name="Max",
    duration_minutes=20,
    priority=3,
    preferred_time="afternoon",
    frequency="daily",
))

# ---------------------------------------------------------------------------
# 4. Generate and print Today's Schedule
# ---------------------------------------------------------------------------
scheduler.generate_plan()
scheduler.display_plan()
print(scheduler.explain_reasoning())
