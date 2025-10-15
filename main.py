from fastapi import FastAPI, HTTPException
from datetime import datetime
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel

# scheduler
jobstores = {
  'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

# model for creating chores
class Chore(BaseModel):
  id: str
  description: str
  start: datetime = datetime.now()
  interval: int = 7

app = FastAPI()

def print_job(description):
  print(description)

@app.post("/chores/")
async def create_chore(chore: Chore):
  scheduler.add_job(print_job, 'interval', id=chore.id, name=chore.description, args=[chore.description], start_date=chore.start, days=chore.interval)
  return chore.id

@app.get("/chores/")
async def get_chores():
  chorelist = []
  for chore in scheduler.get_jobs():
    chorelist.append({
      "id": chore.id,
      "description": chore.name,
      "next_run": chore.next_run_time
    })
  return chorelist

@app.get("/chore/{id}")
async def get_chore(id: str):
  chore = scheduler.get_job(id)
  if chore == None:
    raise HTTPException(status_code=404, detail=f"Chore not found")
  return {
    "id": chore.id,
    "description": chore.name,
    "next_run": chore.next_run_time
  }

@app.delete("/chore/{id}")
async def get_chore(id: str):
  chore = scheduler.get_job(id)
  if chore == None:
    raise HTTPException(status_code=404, detail=f"Chore not found")
  scheduler.remove_job(id)
  return {"message": "Chore successfully deleted."}