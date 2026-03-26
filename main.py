from pawpal_system import Task, Pet, Owner, Scheduler

# Global registries for testing
pets = {}
tasks = {}

# Create an Owner
owner = Owner(owner_id=1, name="Alex", contact_info="alex@email.com")

# Create two Pets
pet1 = Pet(pet_id=101, name="Buddy", species="Dog", breed="Labrador", age=5, medical_info="Healthy", owner_id=owner.owner_id)
pet2 = Pet(pet_id=102, name="Mittens", species="Cat", breed="Siamese", age=3, medical_info="Allergic to fish", owner_id=owner.owner_id)

# Register pets
tpets = {pet1.pet_id: pet1, pet2.pet_id: pet2}
for pet in tpets.values():
    pets[pet.pet_id] = pet
    owner.add_pet(pet.pet_id)

# Create three Tasks with different times
task1 = Task(task_id=201, description="Morning Walk", time="08:00", frequency="Daily", assigned_pet_id=pet1.pet_id)
task2 = Task(task_id=202, description="Feed Breakfast", time="09:00", frequency="Daily", assigned_pet_id=pet2.pet_id)
task3 = Task(task_id=203, description="Vet Appointment", time="15:00", frequency="Once", assigned_pet_id=pet1.pet_id)

# Register tasks
tasks[task1.task_id] = task1
tasks[task2.task_id] = task2
tasks[task3.task_id] = task3

# Assign tasks to pets
pet1.add_task(task1.task_id)
pet1.add_task(task3.task_id)
pet2.add_task(task2.task_id)

# Create Scheduler
scheduler = Scheduler(tasks)

# Get all tasks for the owner
owner_tasks = scheduler.get_owner_tasks(owner, pets)

# Sort tasks by time for today's schedule
today_schedule = sorted(owner_tasks, key=lambda t: t.time)

# Print Today's Schedule
print("Today's Schedule:")
for task in today_schedule:
    pet_name = pets[task.assigned_pet_id].name if task.assigned_pet_id in pets else "Unknown Pet"
    print(f"{task.time} - {task.description} for {pet_name} (Frequency: {task.frequency})")
