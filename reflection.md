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
2. **Pet**: Pet class has details on pet's name, gender, age, pet type, medical conditions, insurance and all the tasks associated with the pet and can perform operations such as add & remove task, display all tasks, insurance details and medical needs of the pet.
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

Scheduler takes into consideration the preference of an Owner such as time to avoid scheduling task and preventing duplicate tasks to be scheduled, and provides options in the app to let owner choose how to visualize the list of tasks for the day based on priority or the sorted time value.

- How did you decide which constraints mattered most?

Owner's preference matters the most as the Owner takes care of the pet and the schedule should be based on the owner's preferences and availability of time. The app also provides the functionality to let Owner generate plan based on just the priority or the sorted start time of the tasks which gives owner flexibility to decide what kind of plan they require.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

One trade off the scheduler makes is that while consideting Owner's available time, it accepts task in sorted order based on time and the moment Owner's available time is exhausted, it never looks backs to check which were the higher priority and which were the lower priority tasks. In a given available time, it is more important to pack in higher priority tasks with less time such as vet pills and feeding than lower priority earlier appearing tasks such as walking.  

- Why is that tradeoff reasonable for this scenario?

This tradeoff is made by Scheduler in this scenario as the linear task picking algorithm currently implemented runs in O(nlogn). If the optimal solution is implemented based on priority, it is a 0/1 knapsack problem which is NP-hard problem and requires dynamic programming. greedy approach is simpler to debug and explain to the owner.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

AI was used to brainstrom design during the initial phase of the project and help create skeleton for the classes involved in the app. AI also immensely helped make the app core logic coherent. Debugging, refactoring and creating test cases were the most important tasks performed while collaborating with AI.

- What kinds of prompts or questions were most helpful?

Prompts with #file:file_name and #codebase was helpful as it knew exactly where to look at in the filesystem. Prompts providing further context and more details came up with better results.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

One AI suggestion code implementation had task deletion method incorrectly implemented. If two tasks are of the same name, while deleting one task with that name, it ended up deleting all the task with the same name.

- How did you evaluate or verify what the AI suggested?

I evaluated the functionality by testing in UI and ended up refactoring the code to make the task deletion method identify task uniquely.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

The testcases tested marking tasks complete, adding tasks and counting tasks for each pet, prioritizing task method, sort by time, detecting conflicts, creating new instance of recurring task, filter by pet, complete task of non existent pet, and owner's availability.

- Why were these tests important?

These are the core logic of the app which helps create plan for owner based on owner's preference, priorities to make a reliable daily plan for pet care.

**b. Confidence**

- How confident are you that your scheduler works correctly?

Scheduler works correctly based on all the assumptions we made throughour this readme. The core logic and function of scheduler works reliably.

- What edge cases would you test next if you had more time?

Some edge cases to test are 

I would probe generate_plan function more as it contains the core logic of the scheduler. Scenarios such as Owner with 0 available hours, avoid_time functionality that avoids a certain time of the day from the plan, filtering tasks with no start times, etc.
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Implementing the core logic and refactoring to integrated time conflicts is fundamental part of creating a robust plan. Adding that feature makes this plan genetaring app worth it.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would redesing to add additional features like utilizing AI to recommend tasks for pets such as when was the last grooming done, or when was the last doctor's visit.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

AI can help get a clear picture of what the app is capable of doing and help focus on designing the flow of the app before diving into the core implementation which can make development a lot smoother.
