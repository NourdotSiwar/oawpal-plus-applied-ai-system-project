from pawpal_system import Owner, Pet, Task, Scheduler
import streamlit as st

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")


def tasks_to_table_rows(tasks, pets):
    """Convert Task objects into table-friendly rows for Streamlit."""
    rows = []
    for task in tasks:
        pet_name = "Unassigned"
        if task.assigned_pet_id in pets:
            pet_name = pets[task.assigned_pet_id].name
        rows.append(
            {
                "ID": task.task_id,
                "Task": task.description,
                "Pet": pet_name,
                "Date": task.date or "N/A",
                "Time": task.time,
                "Frequency": task.frequency,
                "Status": task.status,
            }
        )
    return rows

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")

# Check if 'owner' already exists in session_state
if 'owner' not in st.session_state:
    # Create and store the Owner instance if it doesn't exist
    st.session_state['owner'] = Owner(owner_id=1, name="Alex", contact_info="alex@email.com")

# Now you can safely use st.session_state['owner'] throughout your app
owner = st.session_state['owner']

# Owner name input (for demo, not used to recreate owner object)
owner_name = st.text_input("Owner name", value=st.session_state['owner'].name if 'owner' in st.session_state else "Jordan")

# --- Add Pet Form ---
st.markdown("### Add a Pet")
if 'pets' not in st.session_state:
    st.session_state['pets'] = {}

with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="")
    age = st.number_input("Age", min_value=0, max_value=50, value=1)
    medical_info = st.text_input("Medical info", value="")
    submitted = st.form_submit_button("Add Pet")
    if submitted:
        # Generate a new pet_id
        pet_id = max(st.session_state['pets'].keys(), default=100, ) + 1 if st.session_state['pets'] else 101
        new_pet = Pet(
            pet_id=pet_id,
            name=pet_name,
            species=species,
            breed=breed,
            age=age,
            medical_info=medical_info,
            owner_id=st.session_state['owner'].owner_id
        )
        st.session_state['pets'][pet_id] = new_pet
        st.session_state['owner'].add_pet(pet_id)
        st.success(f"Added pet: {pet_name}")

# Display pets
if st.session_state['owner'].pet_ids:
    st.markdown("### Your Pets")
    pet_table = []
    for pid in st.session_state['owner'].pet_ids:
        pet = st.session_state['pets'].get(pid)
        if pet:
            pet_table.append({
                "Name": pet.name,
                "Species": pet.species,
                "Breed": pet.breed,
                "Age": pet.age,
                "Medical Info": pet.medical_info
            })
    st.table(pet_table)
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "next_task_id" not in st.session_state:
    st.session_state.next_task_id = 1

# Backward-compatible migration in case older dict tasks are still in session state.
if st.session_state.tasks and isinstance(st.session_state.tasks[0], dict):
    migrated = []
    for item in st.session_state.tasks:
        migrated.append(
            Task(
                task_id=st.session_state.next_task_id,
                description=item.get("title", "Untitled task"),
                time=item.get("time", "09:00"),
                frequency=item.get("frequency", "Daily"),
                date=item.get("date"),
                status=item.get("status", "incomplete"),
                assigned_pet_id=item.get("assigned_pet_id"),
            )
        )
        st.session_state.next_task_id += 1
    st.session_state.tasks = migrated

pet_options = {"Unassigned": None}
for pid in st.session_state["owner"].pet_ids:
    pet = st.session_state["pets"].get(pid)
    if pet:
        pet_options[f"{pet.name} (ID {pid})"] = pid

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    task_time = st.time_input("Task time")
with col3:
    frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Once"], index=0)

col4, col5, col6 = st.columns(3)
with col4:
    task_date = st.date_input("Task date")
with col5:
    task_status = st.selectbox("Task status", ["incomplete", "complete", "deleted"], index=0)
with col6:
    selected_pet_label = st.selectbox("Assign to pet", list(pet_options.keys()), index=0)

if st.button("Add task"):
    st.session_state.tasks.append(
        Task(
            task_id=st.session_state.next_task_id,
            description=task_title,
            time=task_time.strftime("%H:%M"),
            frequency=frequency,
            date=task_date.isoformat(),
            status=task_status,
            assigned_pet_id=pet_options[selected_pet_label],
        )
    )
    st.session_state.next_task_id += 1
    st.success(f"Added task: {task_title}")

if st.session_state.tasks:
    st.write("Current tasks:")
    scheduler_for_filters = Scheduler(st.session_state.tasks)

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.selectbox("Filter by status", ["all", "incomplete", "complete", "deleted"], index=0)
    with filter_col2:
        pet_filter_names = ["all"] + [
            st.session_state["pets"][pid].name
            for pid in st.session_state["owner"].pet_ids
            if pid in st.session_state["pets"]
        ]
        pet_filter = st.selectbox("Filter by pet", pet_filter_names, index=0)

    filtered_tasks = scheduler_for_filters.tasks
    if status_filter != "all":
        filtered_tasks = Scheduler(filtered_tasks).filter_by_status(status_filter)
    if pet_filter != "all":
        filtered_tasks = Scheduler(filtered_tasks).filter_by_pet_name(st.session_state["pets"], pet_filter)

    st.table(tasks_to_table_rows(filtered_tasks, st.session_state["pets"]))
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("No tasks available. Add at least one task to generate a schedule.")
    else:
        scheduler = Scheduler(st.session_state.tasks)
        sorted_tasks = scheduler.sort_by_time()
        conflicts = scheduler.detect_conflicts()

        st.success("Schedule generated and sorted by time.")
        st.table(tasks_to_table_rows(sorted_tasks, st.session_state["pets"]))

        if conflicts:
            st.warning(f"{len(conflicts)} potential scheduling conflict(s) detected.")
            for conflict in conflicts:
                st.write(f"- {conflict}")
            st.info(
                "Helpful next step: adjust one of the conflicting tasks so feeding, medication, or walks do not overlap."
            )
        else:
            st.success("No conflicts detected. Your pet care timeline looks clear.")