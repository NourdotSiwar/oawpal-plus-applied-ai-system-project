import pytest
from pawpal_system import Task, Pet

def test_task_completion():
    task = Task(task_id=1, description="Feed", time="08:00", frequency="Daily")
    assert task.status == "incomplete"
    task.mark_complete()
    assert task.status == "complete"

def test_pet_add_task():
    pet = Pet(pet_id=1, name="Buddy", species="Dog", breed="Lab", age=3, medical_info="None")
    initial_count = len(pet.task_ids)
    pet.add_task(101)
    assert len(pet.task_ids) == initial_count + 1
    assert 101 in pet.task_ids
