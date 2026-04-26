from dotenv import load_dotenv
load_dotenv()

from datetime import date as date_today, datetime
from pawpal_system import Owner, Pet, Task, Scheduler
from ai_assistant import suggest_tasks, answer_question, generate_weekly_schedule
import streamlit as st

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")


def _fmt_date(date_str: str) -> str:
    if not date_str or date_str == "N/A":
        return "N/A"
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    except ValueError:
        return date_str


def _fmt_day_label(day_str: str) -> str:
    """Convert 'Wednesday 2026-04-22' to 'Wednesday, April 22, 2026'."""
    parts = day_str.split(" ", 1)
    if len(parts) == 2:
        return f"{parts[0]}, {_fmt_date(parts[1])}"
    return day_str


def tasks_to_table_rows(tasks, pets):
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
                "Date": _fmt_date(task.date),
                "Time": task.time,
                "Frequency": task.frequency,
                "Status": task.status,
            }
        )
    return rows


with st.expander("About PawPal+", expanded=False):
    st.markdown(
        """
**PawPal+** is an AI-powered pet care planning assistant. It helps pet owners manage daily
care tasks and uses a RAG-based AI assistant to suggest personalised tasks, answer pet care
questions, and generate full weekly schedules — all grounded in a curated pet care knowledge base.
"""
    )

st.divider()

# ── Owner ────────────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(owner_id=1, name="Alex", contact_info="alex@email.com")

owner = st.session_state["owner"]
owner_name = st.text_input("Owner name", value=owner.name)

# ── Pets ─────────────────────────────────────────────────────────────────────
st.markdown("### Add a Pet")
if "pets" not in st.session_state:
    st.session_state["pets"] = {}

with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="")
    age = st.number_input("Age", min_value=0, max_value=50, value=1)
    medical_info = st.text_input("Medical info", value="")
    submitted = st.form_submit_button("Add Pet")
    if submitted:
        pet_id = (max(st.session_state["pets"].keys()) + 1) if st.session_state["pets"] else 101
        new_pet = Pet(
            pet_id=pet_id,
            name=pet_name,
            species=species,
            breed=breed,
            age=age,
            medical_info=medical_info,
            owner_id=owner.owner_id,
        )
        st.session_state["pets"][pet_id] = new_pet
        owner.add_pet(pet_id)
        st.success(f"Added pet: {pet_name}")

if owner.pet_ids:
    st.markdown("### Your Pets")
    st.table(
        [
            {
                "Name": p.name,
                "Species": p.species,
                "Breed": p.breed,
                "Age": p.age,
                "Medical Info": p.medical_info,
            }
            for pid in owner.pet_ids
            if (p := st.session_state["pets"].get(pid))
        ]
    )
else:
    st.info("No pets yet. Add one above.")

# ── Tasks ─────────────────────────────────────────────────────────────────────
st.markdown("### Tasks")

if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "next_task_id" not in st.session_state:
    st.session_state.next_task_id = 1

# Backward-compatible migration for older dict-format tasks
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
for pid in owner.pet_ids:
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
            for pid in owner.pet_ids
            if pid in st.session_state["pets"]
        ]
        pet_filter = st.selectbox("Filter by pet", pet_filter_names, index=0)

    filtered_tasks = scheduler_for_filters.tasks
    if status_filter != "all":
        filtered_tasks = Scheduler(filtered_tasks).filter_by_status(status_filter)
    if pet_filter != "all":
        filtered_tasks = Scheduler(filtered_tasks).filter_by_pet_name(
            st.session_state["pets"], pet_filter
        )

    st.table(tasks_to_table_rows(filtered_tasks, st.session_state["pets"]))
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Build Schedule ────────────────────────────────────────────────────────────
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("No tasks available. Add at least one task first.")
        st.session_state["last_schedule"] = None
    else:
        scheduler = Scheduler(st.session_state.tasks)
        st.session_state["last_schedule"] = {
            "tasks": scheduler.sort_by_time(),
            "conflicts": scheduler.detect_conflicts(),
        }

if st.session_state.get("last_schedule"):
    sched = st.session_state["last_schedule"]
    st.success("Schedule generated and sorted by time.")
    st.table(tasks_to_table_rows(sched["tasks"], st.session_state["pets"]))
    if sched["conflicts"]:
        st.warning(f"{len(sched['conflicts'])} potential scheduling conflict(s) detected.")
        for conflict in sched["conflicts"]:
            st.write(f"- {conflict}")
    else:
        st.success("No conflicts detected. Your pet care timeline looks clear.")

st.divider()

# ── AI Assistant ──────────────────────────────────────────────────────────────
st.subheader("🤖 AI Assistant (RAG-Powered)")
st.caption(
    "Powered by Llama 3.1 (OpenRouter) + a curated pet care knowledge base."
    "The AI retrieves relevant facts before generating any response."
)

# ── 1. Suggest tasks ──────────────────────────────────────────────────────────
st.markdown("#### Suggest Care Tasks for a Pet")

if owner.pet_ids:
    ai_pet_map = {
        st.session_state["pets"][pid].name: pid
        for pid in owner.pet_ids
        if pid in st.session_state["pets"]
    }
    selected_for_suggest = st.selectbox(
        "Select pet for task suggestions", list(ai_pet_map.keys()), key="ai_suggest_pet"
    )

    if st.button("Suggest tasks with AI"):
        pet = st.session_state["pets"][ai_pet_map[selected_for_suggest]]
        with st.spinner("Retrieving care facts and generating suggestions…"):
            result = suggest_tasks(pet)

        if result.get("tasks"):
            confidence = result.get("confidence", 0)
            st.success(f"Suggestions ready — confidence: {confidence:.0%}")
            st.info(f"**Reasoning:** {result.get('reasoning', '')}")

            if "pending_suggestions" not in st.session_state:
                st.session_state["pending_suggestions"] = []
            st.session_state["pending_suggestions"] = [
                (t, ai_pet_map[selected_for_suggest]) for t in result["tasks"]
            ]
        else:
            st.error(f"Could not generate suggestions. {result.get('reasoning', '')}")

    if st.session_state.get("pending_suggestions"):
        st.markdown("**Click a task to add it:**")
        for i, (task_data, pid) in enumerate(st.session_state["pending_suggestions"]):
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.write(
                    f"• **{task_data['description']}** — {task_data['time']} ({task_data.get('frequency', 'Daily')})"
                )
            with col_b:
                already_added = any(
                    t.description == task_data["description"]
                    for t in st.session_state.tasks
                )
                if already_added:
                    st.caption("✓ Added")
                elif st.button("Add", key=f"add_sug_{i}"):
                    st.session_state.tasks.append(
                        Task(
                            task_id=st.session_state.next_task_id,
                            description=task_data["description"],
                            time=task_data["time"],
                            frequency=task_data.get("frequency", "Daily"),
                            date=date_today.today().isoformat(),
                            status="incomplete",
                            assigned_pet_id=pid,
                        )
                    )
                    st.session_state.next_task_id += 1
                    st.rerun()
else:
    st.info("Add a pet first to get AI task suggestions.")

st.markdown("---")

# ── 2. Pet care Q&A ───────────────────────────────────────────────────────────
st.markdown("#### Ask a Pet Care Question")

question = st.text_input(
    "Your question",
    placeholder="How often should I bathe a Golden Retriever?",
    key="qa_question",
)

qa_pet_names = ["No specific pet"] + [
    st.session_state["pets"][pid].name
    for pid in owner.pet_ids
    if pid in st.session_state["pets"]
]
qa_pet_choice = st.selectbox("Context pet (optional)", qa_pet_names, key="qa_pet")

if st.button("Ask AI") and question.strip():
    pet_for_qa = None
    if qa_pet_choice != "No specific pet":
        pet_for_qa = next(
            (
                st.session_state["pets"][pid]
                for pid in owner.pet_ids
                if st.session_state["pets"].get(pid)
                and st.session_state["pets"][pid].name == qa_pet_choice
            ),
            None,
        )

    with st.spinner("Looking up answer in knowledge base…"):
        result = answer_question(question, pet_for_qa)

    st.info(result.get("answer", "No answer generated."))
    sources = ", ".join(result.get("sources_used", ["General knowledge"]))
    st.caption(f"Confidence: {result.get('confidence', 0):.0%} | Sources: {sources}")

st.markdown("---")

# ── 3. Weekly schedule ────────────────────────────────────────────────────────
st.markdown("#### Generate AI Weekly Schedule")
st.caption("The AI will create a personalised 7-day care plan for all your pets and explain its reasoning.")

if st.button("Generate AI Weekly Schedule"):
    pets_list = [
        st.session_state["pets"][pid]
        for pid in owner.pet_ids
        if pid in st.session_state["pets"]
    ]
    if not pets_list:
        st.warning("Add at least one pet first.")
    else:
        with st.spinner("Building your personalised weekly schedule…"):
            result = generate_weekly_schedule(pets_list)

        if result.get("schedule"):
            confidence = result.get("confidence", 0)
            st.success(f"Weekly schedule ready — confidence: {confidence:.0%}")
            st.info(f"**Reasoning:** {result.get('reasoning', '')}")

            for day_data in result["schedule"]:
                with st.expander(_fmt_day_label(day_data.get("day", "Day"))):
                    for t in day_data.get("tasks", []):
                        st.write(
                            f"• **[{t.get('pet_name', '?')}]** {t['description']} — {t['time']}"
                        )
        else:
            st.error(f"Could not generate schedule. {result.get('reasoning', '')}")
