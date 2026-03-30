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
# 3. Create Scheduler and add Tasks intentionally OUT OF ORDER
#    (afternoon tasks first, then evening, then morning) to prove that
#    sort_by_time() and prioritize_tasks() reorder them correctly regardless
#    of insertion order.
# ---------------------------------------------------------------------------
today = date.today().isoformat()
scheduler = Scheduler(owner=owner, date=today)

# --- afternoon tasks added first (out of order) ---
scheduler.add_task(luna, Task(
    name="Grooming",
    task_type="groom",
    pet_name="Luna",
    duration_minutes=25,
    priority=4,
    preferred_time="afternoon",
    frequency="weekly",
    start_time="14:00",
))

scheduler.add_task(max, Task(
    name="Enrichment Play",
    task_type="enrichment",
    pet_name="Max",
    duration_minutes=20,
    priority=3,
    preferred_time="afternoon",
    frequency="daily",
    start_time="15:00",
))

# --- evening task added second (still out of order) ---
scheduler.add_task(luna, Task(
    name="Evening Walk",
    task_type="walk",
    pet_name="Luna",
    duration_minutes=20,
    priority=2,
    preferred_time="evening",
    frequency="daily",
    start_time="18:00",
))

# --- morning tasks added last (correct order would be first) ---
scheduler.add_task(max, Task(
    name="Feeding",
    task_type="feed",
    pet_name="Max",
    duration_minutes=10,
    priority=1,
    preferred_time="morning",
    frequency="daily",
    start_time="08:15",
))

scheduler.add_task(luna, Task(
    name="Hip Med",
    task_type="med",
    pet_name="Luna",
    duration_minutes=5,
    priority=1,
    preferred_time="morning",
    frequency="daily",
    start_time="08:00",
))

scheduler.add_task(luna, Task(
    name="Morning Walk",
    task_type="walk",
    pet_name="Luna",
    duration_minutes=30,
    priority=1,
    preferred_time="morning",
    frequency="daily",
    start_time="08:30",
))

# ---------------------------------------------------------------------------
# Conflict tasks — added intentionally to trigger detect_conflicts()
#
# Conflict A (same pet): "Dental Treat" for Luna starts at 08:45 and runs
#   30 min (08:45–09:15).  Morning Walk is 08:30–09:00.  They overlap by 15 min.
#
# Conflict B (cross pet): "Nail Trim" for Max starts at 08:20 and runs
#   20 min (08:20–08:40).  Feeding is 08:15–08:25.  They overlap by 5 min.
# ---------------------------------------------------------------------------
scheduler.add_task(luna, Task(
    name="Dental Treat",
    task_type="groom",
    pet_name="Luna",
    duration_minutes=30,
    priority=2,
    preferred_time="morning",
    frequency="daily",
    start_time="08:45",        # overlaps Morning Walk (08:30–09:00)
))

scheduler.add_task(max, Task(
    name="Nail Trim",
    task_type="groom",
    pet_name="Max",
    duration_minutes=20,
    priority=2,
    preferred_time="morning",
    frequency="as-needed",
    start_time="08:20",        # overlaps Feeding (08:15–08:25)
))

# ---------------------------------------------------------------------------
# 4. Set owner preferences, then generate the plan in both sort modes
# ---------------------------------------------------------------------------
owner.set_preference("avoid_time", "evening")
owner.set_preference("no_concurrent_pets", True)

# ── Mode A: priority (slot → importance number) ──────────────────────────
print("\n" + "="*50)
print("  PLAN A — sort_mode='priority'")
print("="*50)
scheduler.generate_plan(sort_mode="priority")
scheduler.display_plan()

# ── Mode B: clock (slot → HH:MM → importance number) ────────────────────
print("\n" + "="*50)
print("  PLAN B — sort_mode='clock'")
print("="*50)
scheduler.generate_plan(sort_mode="clock")

# ---------------------------------------------------------------------------
# 5. Full plan (clock-sorted version shown from here on)
# ---------------------------------------------------------------------------
scheduler.display_plan()

# ---------------------------------------------------------------------------
# 6. sort_by_time() — reorders by exact clock time across all tasks
# ---------------------------------------------------------------------------
all_tasks = [t for pet in owner.get_pets() for t in pet.get_tasks()]
clock_sorted = scheduler.sort_by_time(all_tasks)

print("--- sort_by_time(): insertion order was afternoon→evening→morning ---")
print("    result should read morning→afternoon→evening by clock time\n")
for t in clock_sorted:
    time_label = t.start_time if t.start_time else "no time"
    print(f"  [{t.preferred_time:<9}] {time_label}  priority={t.priority}  {t.name} ({t.pet_name})")

# ---------------------------------------------------------------------------
# 7. filter_by_pet() — show only one pet's scheduled tasks
# ---------------------------------------------------------------------------
print("\n--- filter_by_pet('Luna') ---")
luna_entries = scheduler.filter_by_pet("Luna")
for e in luna_entries:
    status = "Done" if e.task.is_completed else "Pending"
    print(f"  [{e.task.preferred_time.upper()}] {e.task.name}  |  {status}")

print("\n--- filter_by_pet('Max') ---")
max_entries = scheduler.filter_by_pet("Max")
for e in max_entries:
    status = "Done" if e.task.is_completed else "Pending"
    print(f"  [{e.task.preferred_time.upper()}] {e.task.name}  |  {status}")

# ---------------------------------------------------------------------------
# 8. filter_by_status() — split plan into done vs. still pending
# ---------------------------------------------------------------------------
print("\n--- filter_by_status(completed=True) ---")
done = scheduler.filter_by_status(completed=True)
for e in done:
    print(f"  {e.task.name} ({e.pet_name})")

print("\n--- filter_by_status(completed=False) ---")
pending = scheduler.filter_by_status(completed=False)
for e in pending:
    print(f"  {e.task.name} ({e.pet_name})")

# ---------------------------------------------------------------------------
# 9. complete_task() — mark done and auto-create next occurrence
# ---------------------------------------------------------------------------
print("\n--- complete_task() recurring logic ---")

# Complete a daily task — should spawn a next occurrence due tomorrow
next_hip_med = scheduler.complete_task("Luna", "Hip Med")
print(f"Completed 'Hip Med' (daily). Next occurrence due: {next_hip_med.due_date}")

# Complete a weekly task — should spawn a next occurrence due in 7 days
next_grooming = scheduler.complete_task("Luna", "Grooming")
print(f"Completed 'Grooming' (weekly). Next occurrence due: {next_grooming.due_date}")

# Complete an as-needed task — no follow-up should be created
scheduler.complete_task("Max", "Enrichment Play")
print("Completed 'Enrichment Play' (as-needed). No follow-up created.")

# Confirm new tasks exist on the pet
print("\nLuna's tasks after completions:")
for t in luna.get_tasks():
    due = f"  due {t.due_date}" if t.due_date else ""
    status = "Done" if t.is_completed else "Pending"
    print(f"  {t.name:<20} freq={t.frequency:<10} status={status}{due}")

# ---------------------------------------------------------------------------
# 10. detect_conflicts() — identify overlapping or overloaded tasks
# ---------------------------------------------------------------------------
print("\n--- detect_conflicts() ---")
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")
