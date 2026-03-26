# PawPal+ Project Reflection

## 1. System Design

- User actions:
1. Edit/Add tasks
2. See daily generated plan
3. User enters pet + owner information

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?


Initial Design:
*Owner Class*
Attributes: owner_id, name, contact_info, pets (Pet List)
Methods: add_pet(), remove_pet(), get_pets(), update_info()

*Pet Class*
Attributes: pet_id, name, species, breed, age, medical_info, owner (Owner), tasks (list of Task)
Methods: add_task(), remove_task(), get_tasks(), update_info()

*Task Class*
Attributes: task_id, description, category, due_date, status, assigned_pet (Pet)
Methods: mark_complete(), edit_task(), delete_task()

*TaskManager  Class*
Attributes: tasks (list of Task)
Methods: add_task(), edit_task(), delete_task(), get_tasks(), assign_task_to_pet()

*DailyPlanGenerator Class*
Attributes: tasks (list of Task), constraints (e.g., pet schedule, owner availability), plan
Methods: generate_plan(), explain_reasoning(), update_constraints(), get_plan()

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

CoPilot mentioned that there is a circular reference of Owner -> Pet -> Owner. So, I wanted to remove a cause for a potential infinite loop. Thus, I decided to use IDs so that Pet and Task use only IDs for references, and remove the direct object references, which would make serialization and data management easier.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

- The scheduler primarily considers the time each task is scheduled for, ensuring tasks are ordered and checked for conflicts based on their time and date.
- Time was chosen as the most important constraint because, for pet care, making sure tasks do not overlap and are performed at the correct times is critical for the pets' well-being and the owner's routine. Other constraints like priority or preferences could be added in the future.
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

- One tradeoff the scheduler makes is that it only checks for exact time matches (tasks scheduled at the same hour and minute) when detecting conflicts, rather than considering overlapping durations or tasks that might partially overlap.
- This tradeoff is reasonable because most pet care tasks in this context are short and occur at specific times (like feeding or walking), so exact time conflicts are the most likely and relevant issue. This approach keeps the conflict detection logic simple and efficient, which is appropriate for a lightweight scheduling app.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Copilot Chat to help with brainstorming and designing initial UML as I was confused at first on what PawPawl+ does. Then, I used it to help with coding the implementation, debugging any issues I found, and refactoring unreadable code.

I think the prompts/questions that were most helpful actually came from the project instructions on the project site on CodePath A110 page. I copy pasted them but made sure to identify the correct files.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment where I did not accept an AI suggestion as-is was when I asked for ideas to refactor one of my algorithmic methods. I found that the code it suggested would have been either the same or redundant for what I currently had.

I evaluated/verified what the AI suggested through running test cases while also running the UI and noticing any failing tests or any weird bugs that showed on the site.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested the core scheduling behaviors that directly affect correctness and daily usability:

- Task completion state changes from incomplete to complete.
- Pet task assignment logic (adding task IDs to a pet).
- Chronological sorting of tasks by time.
- Daily recurrence behavior (marking a daily task complete creates the next-day task).
- Conflict detection for tasks with the same date and time.
- Empty-scheduler behavior (no crashes, returns empty outputs).
- Non-conflict behavior for tasks at the same time on different dates.

These tests were important because they cover both happy paths and key edge conditions in my scheduler. Together, they verify that tasks are ordered correctly, recurring care is preserved, and owners receive meaningful conflict warnings without false positives.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am highly confident that my scheduler works correctly for the implemented scope (about 4/5 confidence). My tests validate the most critical behaviors, and all current tests pass.

If I had more time, I would add tests for these edge cases:

- Invalid or malformed time strings (for example, non-HH:MM input).
- Multiple conflicts in the same time slot (more than two tasks colliding).
- Weekly recurrence across month/year boundaries.
- Behavior when a task has no date but recurrence is enabled.
- Filtering and conflict detection with deleted tasks.
- Stability of sort order when multiple tasks share the same time.
- UI-level integration tests to confirm warnings and tables render as expected from scheduler outputs.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am satisfied that I was able to take a project from a paragraph to an UML to backend code to linking it to frontend code!

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would redesign the website for sure. There is a lot of scrolling, so instead I would divide the website into pages. I would add a navigation bar and link those pages.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
One important thing I learned was that it is important to understand that AI can fabricate requirements not mentioned before. While these suggestions may be helpful, it can contradict what the client wants so it is important and critical to double and triple check what the AI spits out.
