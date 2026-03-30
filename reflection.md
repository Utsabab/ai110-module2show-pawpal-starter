# PawPal+ Project Reflection

## 1. System Design

Three core actions for users:
- Add/Edit/Delete tasks
- Track each task planned for the day
- Set Owner's preference such as availability, priority, etc..

**a. Initial design**

- Briefly describe your initial UML design.

The UML has four major classes namely, Owner, Pet, Task and Scheduler. Owner class has details on Owner and Pet class has details on pets. Task class has attributes and methods for each task. Scheduler is the core logic implementation class which generates daily plan for owner based on the owner's preferences and pets. An owner can have 0 to many pets. A pet can have 0 to many tasks associated. A scheduler can have only one owner. A scheduler can have 0 to many tasks.

- What classes did you include, and what responsibilities did you assign to each?

There are four major classes in the UML design which are described below:

1. **Owner:** Owner class has details on owner's name, age, gender, available hours, and preferences and has methods such as set_preferences, add & remove pet, get available times for owner.
2. **Pet**: Pet class has details on pet's name, gender, age, breed, medical conditions, insurance and all the tasks associated with the pet and can perform operations such as add & remove task, display all tasks, insurance details and medical needs of the pet.
3. **Task**: Task class has task name, task type, time duration, priority value, preferred time, is completed marker, and frequency as attributse and has methods such as set priority, set duration, mark complete, mark incomplete, and get details.
4. **Scheduler**: Scheduler class schedules tasks for owners where a scheduler can have only 1 owner and 0 to many tasks. The attributes are owner, date, daily plan and reasoning for daily plan. The methods associated are add task, edit task, prioritize task, check owner constraint, generate plan, display plan and explain reasoning method to display the reasoning for the plan generated.

**b. Design changes**

- Did your design change during implementation?

Yes

- If yes, describe at least one change and why you made it.

Missing relationships:

1. Task has no reference back to its Pet.

   Fix: Add a pet_name: str attribute to task, populated when Scheduler.add_task(pet, task) is called.

2. Scheduler collects tasks from pets with no clear trigger generate_plan() is supposed to pull tasks from all owner.pets but Scheduler.add_task() also exists independently. These two paths can diverge, tasks added via add_task() may not be in pet.tasks, and tasks in pet.tasks may not be in daily_plan.

   Fix: Make generate_plan() the authoritative source. It should always pull from owner → pets → tasks. add_task() should write to the pet, not directly to daily_plan.

3. _reasoning is a plain list[str] sitting inside Scheduler.  If you ever want to re-display the plan or export it, you'd need to re-run generate_plan(). The plan and its reasoning are not stored together.

   Fix: A lightweight @dataclass pairing a Task with its reasoning string would make display_plan() and explain_reasoning() much cleaner.

4. check_constraints() is called after plan generation, not during.

   Fix: generate_plan() should call check_constraints() incrementally as tasks are added, stopping or dropping low-priority tasks when the time budget is exhausted.

5. prioritize_tasks() only takes a flat list and has no time-slot awareness.

   Fix: Sort by preferred_time first as a time-slot bucket, then by priority within each bucket.

6. edit_task() matches by name therefore is fragile if two pets share a task name.

   Fix: Change the signature to edit_task(pet_name: str, task_name: str, updates: dict) so the lookup is unambiguous.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
