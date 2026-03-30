import streamlit as st
from datetime import date
from pawpal_system import Pet, Owner, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state init ──────────────────────────────────────────────────────
if "owners" not in st.session_state:
    default_owner = Owner(name="Jordan", age=0, gender="", available_hours_per_day=8)
    st.session_state.owners = [default_owner]
    st.session_state.schedulers = {
        default_owner.name: Scheduler(owner=default_owner, date=str(date.today()))
    }

# ── Owner selector ──────────────────────────────────────────────────────────
st.subheader("Owners")
owner_names = [o.name for o in st.session_state.owners]
selected_owner_name = st.selectbox("Select active owner", owner_names)
owner = next(o for o in st.session_state.owners if o.name == selected_owner_name)
scheduler = st.session_state.schedulers[selected_owner_name]

with st.expander("Add a new owner"):
    col1, col2 = st.columns(2)
    with col1:
        new_owner_name = st.text_input("New owner name")
    with col2:
        new_owner_hours = st.number_input("Available hours/day", min_value=1, max_value=24, value=8)
    if st.button("Add owner"):
        if not new_owner_name:
            st.error("Please enter a name.")
        elif new_owner_name in owner_names:
            st.error(f"An owner named '{new_owner_name}' already exists.")
        else:
            new_owner = Owner(name=new_owner_name, age=0, gender="", available_hours_per_day=new_owner_hours)
            st.session_state.owners.append(new_owner)
            st.session_state.schedulers[new_owner_name] = Scheduler(owner=new_owner, date=str(date.today()))
            st.success(f"Owner '{new_owner_name}' added.")
            st.rerun()

st.divider()

# ── Owner Preferences ───────────────────────────────────────────────────────
st.subheader(f"Preferences — {owner.name}")

with st.expander("Scheduling preferences"):
    avoid_options = st.multiselect(
        "Avoid time slots (tasks in these slots will be excluded from the plan)",
        options=["morning", "afternoon", "evening", "anytime"],
        default=owner.preferences.get("avoid_time", []),
        key="pref_avoid_time",
    )
    no_concurrent = st.checkbox(
        "No concurrent pets (block tasks that overlap with another pet's scheduled task)",
        value=owner.preferences.get("no_concurrent_pets", False),
        key="pref_no_concurrent",
    )
    if st.button("Save preferences"):
        owner.set_preference("avoid_time", avoid_options)
        owner.set_preference("no_concurrent_pets", no_concurrent)
        st.success(
            f"Preferences saved. "
            f"Avoided slots: {avoid_options or 'none'}. "
            f"No concurrent pets: {no_concurrent}."
        )

st.divider()

# ── Add a Pet ───────────────────────────────────────────────────────────────
st.subheader(f"Pets — {owner.name}")
col1, col2, col3, col4 = st.columns(4)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    pet_age = st.number_input("Age", min_value=0, max_value=30, value=2)
with col3:
    pet_breed = st.text_input("Pet type", value="Shiba Inu")
with col4:
    pet_gender = st.selectbox("Gender", ["male", "female"])

if st.button("Add pet"):
    pet = Pet(name=pet_name, age=pet_age, pet_type=pet_breed, gender=pet_gender)
    owner.add_pet(pet)
    st.success(f"Added {pet_name} to {owner.name}'s pets.")

current_pets = owner.get_pets()
if current_pets:
    st.write("Current pets:", [p.name for p in current_pets])
    pet_to_remove = st.selectbox("Remove a pet", [p.name for p in current_pets], key="remove_pet_select")
    if st.button("Remove pet"):
        owner.remove_pet(pet_to_remove)
        st.success(f"Removed {pet_to_remove}.")
        st.rerun()
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Add a Task ──────────────────────────────────────────────────────────────
st.subheader(f"Tasks — {owner.name}")

if not current_pets:
    st.warning("Add a pet first before scheduling tasks.")
else:
    selected_pet_name = st.selectbox("Assign to pet", [p.name for p in current_pets])

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task name", value="Morning walk")
        task_type = st.selectbox("Task type", ["walk", "feed", "groom", "med", "enrichment"])
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        preferred_time = st.selectbox("Preferred time", ["morning", "afternoon", "evening", "anytime"])
    with col3:
        priority_label = st.selectbox("Priority", ["high (1)", "medium (3)", "low (5)"])
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

    # Improvement 1: start_time input so sort_by_time() can order within a slot
    start_time_input = st.text_input(
        "Start time (optional, HH:MM)",
        value="",
        placeholder="e.g. 08:30",
    )

    priority_map = {"high (1)": 1, "medium (3)": 3, "low (5)": 5}

    if st.button("Add task"):
        selected_pet = next(p for p in current_pets if p.name == selected_pet_name)
        task = Task(
            name=task_title,
            task_type=task_type,
            pet_name=selected_pet_name,
            duration_minutes=int(duration),
            priority=priority_map[priority_label],
            preferred_time=preferred_time,
            frequency=frequency,
            start_time=start_time_input.strip() or None,
        )
        scheduler.add_task(selected_pet, task)
        st.success(f"Task '{task_title}' added for {selected_pet_name}.")

    all_tasks = [t for p in current_pets for t in p.get_tasks()]
    if all_tasks:
        # Improvement 2: sort_by_time() applied to the raw task list display
        sort_mode = st.radio(
            "Task list order",
            ["Priority (slot → priority)", "Clock time (slot → HH:MM → priority)"],
            horizontal=True,
        )
        if sort_mode == "Clock time (slot → HH:MM → priority)":
            display_tasks = scheduler.sort_by_time(all_tasks)
        else:
            display_tasks = scheduler.prioritize_tasks(all_tasks)

        st.write("Current tasks:")
        st.table([t.get_details() for t in display_tasks])

        st.write("**Remove a task:**")
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            pets_with_tasks = [p for p in current_pets if p.get_tasks()]
            delete_pet_name = st.selectbox(
                "Pet", [p.name for p in pets_with_tasks], key="delete_pet"
            )
        with col2:
            delete_pet = next(p for p in pets_with_tasks if p.name == delete_pet_name)
            task_list = delete_pet.get_tasks()
            name_count = {}
            for t in task_list:
                name_count[t.name] = name_count.get(t.name, 0) + 1
            name_seen = {}
            task_labels = []
            for t in task_list:
                if name_count[t.name] > 1:
                    name_seen[t.name] = name_seen.get(t.name, 0) + 1
                    task_labels.append(f"{t.name} #{name_seen[t.name]}")
                else:
                    task_labels.append(t.name)
            delete_task_idx = st.selectbox(
                "Task", range(len(task_labels)),
                format_func=lambda i: task_labels[i], key="delete_task"
            )
        with col3:
            st.write("")  # vertical alignment spacer
            if st.button("Delete", key="delete_task_btn"):
                deleted_label = task_labels[delete_task_idx]
                delete_pet.remove_task_at(delete_task_idx)
                st.success(f"Deleted '{deleted_label}' from {delete_pet_name}.")
                st.rerun()
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ── Generate Schedule ───────────────────────────────────────────────────────
st.subheader(f"Build Schedule — {owner.name}")

generate_sort = st.radio(
    "Schedule tasks by",
    ["Priority (slot → importance)", "Clock time (slot → HH:MM → importance)"],
    horizontal=True,
    key="generate_sort_mode",
    help=(
        "Priority: higher-importance tasks claim the budget first, regardless of clock time. "
        "Clock time: earlier start_time tasks are evaluated first — useful when a specific "
        "appointment time must be honoured over abstract priority."
    ),
)
generate_sort_mode = "clock" if "Clock" in generate_sort else "priority"

if st.button("Generate schedule"):
    plan = scheduler.generate_plan(sort_mode=generate_sort_mode)
    if plan:
        total_min = sum(e.task.duration_minutes for e in plan)
        budget = scheduler.owner.get_available_time()
        st.success(f"Plan generated — sorted by {generate_sort_mode}.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tasks scheduled", len(plan))
        c2.metric("Minutes used", f"{total_min} / {budget}")
        c3.metric("Budget remaining", f"{budget - total_min} min")
    else:
        st.warning("No tasks fit within the available time budget, or no tasks have been added.")

if scheduler.daily_plan:
    with st.expander("View scheduling reasoning"):
        st.caption(scheduler.explain_reasoning())

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.subheader("Conflict Warnings")
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected.")

    st.divider()

    # Improvement 3: filter_by_pet() and filter_by_status() controls
    st.subheader("Filter Schedule")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox(
            "Filter by pet",
            ["All"] + [p.name for p in current_pets],
            key="plan_pet_filter",
        )
    with col2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Pending", "Done"],
            key="plan_status_filter",
        )

    # Apply pet filter
    if pet_filter == "All":
        filtered_entries = scheduler.daily_plan
    else:
        filtered_entries = scheduler.filter_by_pet(pet_filter)

    # Apply status filter
    if status_filter == "Pending":
        filtered_entries = scheduler.filter_by_status(completed=False)
        if pet_filter != "All":
            filtered_entries = [e for e in filtered_entries if e.pet_name == pet_filter]
    elif status_filter == "Done":
        filtered_entries = scheduler.filter_by_status(completed=True)
        if pet_filter != "All":
            filtered_entries = [e for e in filtered_entries if e.pet_name == pet_filter]

    if filtered_entries:
        _SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "anytime": 3}
        plan_sort = st.radio(
            "Schedule order",
            ["Priority (slot → priority)", "Clock time (slot → HH:MM → priority)"],
            horizontal=True,
            key="plan_sort",
        )
        if plan_sort == "Clock time (slot → HH:MM → priority)":
            filtered_entries = sorted(
                filtered_entries,
                key=lambda e: (
                    _SLOT_ORDER.get(e.task.preferred_time, 3),
                    e.task.start_time or "",
                    e.task.priority,
                ),
            )

        done_count = sum(1 for e in filtered_entries if e.task.is_completed)
        pending_count = len(filtered_entries) - done_count
        sc1, sc2 = st.columns(2)
        sc1.success(f"{done_count} task(s) done")
        sc2.warning(f"{pending_count} task(s) pending")

        rows = []
        for e in filtered_entries:
            t = e.task
            rows.append({
                "Slot": t.preferred_time.capitalize(),
                "Time": t.start_time or "—",
                "Task": t.name,
                "Pet": e.pet_name,
                "Type": t.task_type,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Status": "Done" if t.is_completed else "Pending",
                "Next Due": t.due_date or "—",
            })
        st.table(rows)
    else:
        st.info("No tasks match the selected filters.")

    st.divider()

    # Improvement 4: complete_task() — mark done and auto-schedule next occurrence
    st.subheader("Mark Task Complete")
    pending_entries = scheduler.filter_by_status(completed=False)
    if pending_entries:
        pending_options = [f"{e.task.name} ({e.pet_name})" for e in pending_entries]
        selected_label = st.selectbox("Select a task to complete", pending_options, key="complete_select")
        selected_entry = pending_entries[pending_options.index(selected_label)]

        if st.button("Mark complete"):
            next_task = scheduler.complete_task(
                pet_name=selected_entry.pet_name,
                task_name=selected_entry.task.name,
            )
            if next_task:
                st.success(
                    f"'{selected_entry.task.name}' marked done. "
                    f"Next occurrence ({selected_entry.task.frequency}) scheduled for {next_task.due_date}."
                )
            else:
                st.success(
                    f"'{selected_entry.task.name}' marked done. "
                    f"No follow-up created (frequency: {selected_entry.task.frequency})."
                )
            scheduler.generate_plan()
            st.rerun()
    else:
        st.info("All tasks in today's plan are already completed.")
