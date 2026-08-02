from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    title: str
    done: bool = False

tasks = {}
next_id = 1

@app.get("/")
def read_root():
    return {"message": "Welcome to my Cloud-Native API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/tasks")
def create_task(task: Task):
    global next_id
    tasks[next_id] = task
    task_with_id = {"id": next_id, **task.dict()}
    next_id += 1
    return task_with_id

@app.get("/tasks")
def list_tasks():
    return [{"id": tid, **t.dict()} for tid, t in tasks.items()]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": task_id, **tasks[task_id].dict()}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks[task_id] = task
    return {"id": task_id, **task.dict()}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"message": f"Task {task_id} deleted"}
