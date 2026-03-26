# Logic layer for PawPal system
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Task:
    task_id: int
    description: str
    time: str
    frequency: str
    status: str = "incomplete"
    assigned_pet_id: Optional[int] = None

    def mark_complete(self):
        """Mark the task as complete."""
        self.status = "complete"

    def edit_task(self, **kwargs):
        """Edit task attributes."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def delete_task(self):
        """Delete the task (mark as deleted)."""
        self.status = "deleted"


@dataclass
class Pet:
    pet_id: int
    name: str
    species: str
    breed: str
    age: int
    medical_info: str
    owner_id: Optional[int] = None  # Reference by owner_id only
    task_ids: List[int] = field(default_factory=list)  # List of task IDs only

    def add_task(self, task_id: int):
        """Add a task to the pet."""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)

    def edit_task(self, task_id: int, tasks: Dict[int, Task], **kwargs):
        """Edit a task for the pet."""
        if task_id in self.task_ids and task_id in tasks:
            tasks[task_id].edit_task(**kwargs)

    def delete_task(self, task_id: int):
        """Delete a task from the pet."""
        if task_id in self.task_ids:
            self.task_ids.remove(task_id)

    def get_tasks(self, tasks: Dict[int, Task]):
        """Get all tasks for the pet."""
        return [tasks[tid] for tid in self.task_ids if tid in tasks]

    def update_info(self, **kwargs):
        """Update pet information."""
        for key, value in kwargs.items():
            setattr(self, key, value)

class Owner:
    def __init__(self, owner_id: int, name: str, contact_info: str):
        self.owner_id = owner_id
        self.name = name
        self.contact_info = contact_info
        self.pet_ids: List[int] = []  # List of pet IDs only

    def add_pet(self, pet_id: int):
        """Add a pet to the owner."""
        if pet_id not in self.pet_ids:
            self.pet_ids.append(pet_id)

    def remove_pet(self, pet_id: int):
        """Remove a pet from the owner."""
        if pet_id in self.pet_ids:
            self.pet_ids.remove(pet_id)

    def get_pets(self, pets: Dict[int, Pet]):
        """Get all pets for the owner."""
        return [pets[pid] for pid in self.pet_ids if pid in pets]

    def get_all_tasks(self, pets: Dict[int, Pet], tasks: Dict[int, Task]):
        """Get all tasks for all pets owned by the owner."""
        all_tasks = []
        for pet in self.get_pets(pets):
            all_tasks.extend(pet.get_tasks(tasks))
        return all_tasks

    def update_info(self, **kwargs):
        """Update owner information."""
        for key, value in kwargs.items():
            setattr(self, key, value)


class Scheduler:
    def __init__(self, tasks: List[Task], constraints=None):
        self.tasks = tasks
        self.constraints = constraints
        self.plan = None

    def generate_plan(self):
        """Generate a plan for tasks."""
        self.plan = sorted(self.tasks.values(), key=lambda t: t.time)
        return self.plan

    def explain_reasoning(self):
        """Explain the reasoning behind the plan."""
        return "Tasks are scheduled based on their time attribute."

    def update_constraints(self, constraints):
        """Update scheduling constraints."""
        self.constraints = constraints

    def get_plan(self):
        """Get the current plan."""
        return self.plan

    def get_owner_tasks(self, owner: Owner, pets: Dict[int, Pet]):
        """Retrieve all tasks for all pets owned by the owner."""
        return owner.get_all_tasks(pets, self.tasks)
