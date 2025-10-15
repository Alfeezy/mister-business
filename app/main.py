from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import uuid

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from pydantic import BaseModel

from datetime import datetime

# scheduler
jobstores = {
  'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

# model for creating chores
class Chore(BaseModel):
  description: str | None
  start: datetime = datetime.now()
  interval: int = 7

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def print_job(description):
  print(description)

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chores/", response_class=HTMLResponse)
async def get_chores(request: Request):
  chorelist = []
  for chore in scheduler.get_jobs():
    chorelist.append({
      "id": chore.id,
      "description": chore.name,
      "next_run": chore.next_run_time
    })
  return templates.TemplateResponse("chores/index.html", {"request": request, "chorelist": chorelist})
  
@app.get("/chores/new", response_class=HTMLResponse)
async def new_chore(request: Request):
  chore = Chore(
    description=None,
  )
  return templates.TemplateResponse("chores/new.html", {"request": request, "chore": chore})

@app.post("/chores/")
async def create_chore(chore: Chore):
  chore_id = uuid.uuid1()
  scheduler.add_job(
    print_job,
    'interval',
    id=str(chore_id),
    name=chore.description,
    args=[chore.description],
    start_date=chore.start,
    days=chore.interval
  )
  return chore_id

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
@app.post("/chore/{id}/delete")
async def delete_chore(id: str):
  chore = scheduler.get_job(id)
  if chore == None:
    raise HTTPException(status_code=404, detail=f"Chore not found")
  scheduler.remove_job(id)
  return {"message": "Chore successfully deleted."}