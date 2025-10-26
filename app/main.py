from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import uuid

from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.triggers.calendarinterval import CalendarIntervalTrigger
from apscheduler import Scheduler, task

from pydantic import BaseModel

from datetime import datetime, timedelta
from time import sleep

from .services.receipt_printer_service import print_chore

# scheduler
datastore = SQLAlchemyDataStore('sqlite:///jobs.sqlite')
scheduler = Scheduler(datastore)
scheduler.start_in_background()

# model for creating chores
class Chore(BaseModel):
  description: str | None = None
  start: datetime = datetime.now()
  interval: int | None = 7

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@task(misfire_grace_time=100000)
def print_job(description):
  print_chore(description)
  sleep(5)

@app.get("/chore/{id}")
async def get_chore(id: str):
  chore = scheduler.get_job(id)
  if chore == None:
    raise HTTPException(status_code=404, detail="Chore not found")
  return {
    "id": chore.id,
    "description": chore.name,
    "next_run": chore.next_run_time
  }

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chores/", response_class=HTMLResponse)
async def get_chores(request: Request):
  chorelist = []
  for schedule in scheduler.get_schedules():
    chorelist.append({
      "id": schedule.id,
      "description": schedule.args[0],
      "interval": schedule.trigger.days,
      "next_run": schedule.next_fire_time
    })
  chorelist.sort(key=lambda item: item['next_run'])
  return templates.TemplateResponse("chores/index.html", {"request": request, "chorelist": chorelist})
  
@app.get("/chores/new", response_class=HTMLResponse)
async def new_chore(request: Request):
  chore = Chore()
  return templates.TemplateResponse("chores/new.html", {"request": request, "chore": chore})

@app.post("/chores/")
async def create_chore(request: Request, description: str = Form(...), start: datetime = Form(...), interval: int = Form(...)):
  schedule_id = uuid.uuid1()
  trigger = CalendarIntervalTrigger(
    start_date=start,
    days=interval,
    timezone="America/New_York"
  )

  scheduler.add_schedule(
    print_job,
    trigger,
    id=str(schedule_id),
    args=[description],
  )

  return RedirectResponse(url="/chores", status_code=303)

@app.get("/chore/{id}/edit", response_class=HTMLResponse)
async def edit_chore(request: Request, id: str):
  schedule = scheduler.get_schedule(id)
  chore = Chore(
    description=schedule.args[0],
    start=schedule.trigger.start_date,
    interval=schedule.trigger.days
  )
  return templates.TemplateResponse("chores/edit.html", {"request": request, "chore": chore, "id": id})

@app.post("/chore/{id}")
async def update_chore(request: Request, id: str, description: str = Form(...), start: datetime = Form(...), interval: int = Form(...)):
  scheduler.remove_schedule(id)
  trigger = CalendarIntervalTrigger(
    start_date=start,
    days=interval,
    timezone="America/New_York"
  )

  scheduler.add_schedule(
    print_job,
    trigger,
    id=id,
    args=[description],
  )
  return RedirectResponse(url="/chores", status_code=303)

@app.post("/chore/{id}/run_chore")
async def run_chore(request: Request, id: str):
  schedule = scheduler.get_schedule(id)

  current_dt = datetime.now()
  run_dt = schedule.next_fire_time
  new_dt = (current_dt + timedelta(days=schedule.trigger.days)).replace(
    hour=run_dt.hour,
    minute=run_dt.minute,
    second=0,
    microsecond=0
  )

  # trigger now
  scheduler.run_job(id)

  # reset next chore time to later date 
  trigger = CalendarIntervalTrigger(
    start_date=new_dt,
    days=schedule.trigger.days,
    timezone="America/New_York"
  )
  scheduler.remove_schedule(id)
  scheduler.add_schedule(
    print_job,
    trigger,
    id=id,
    args=schedule.args,
  )

  return RedirectResponse(url="/chores", status_code=303)


@app.get("/chores/print", response_class=HTMLResponse)
async def get_print(request: Request):
  return templates.TemplateResponse("chores/print.html", {"request": request})

@app.post("/chores/print")
async def print(request: Request, description: str = Form(...)):
  print_job(description)
  return RedirectResponse(url="/chores/print", status_code=303)

@app.delete("/chore/{id}")
@app.post("/chore/{id}/delete")
async def delete_chore(id: str):
  chore = scheduler.get_schedule(id)
  if chore == None:
    raise HTTPException(status_code=404, detail="Chore not found")
  scheduler.remove_schedule(id)
  return RedirectResponse(url="/chores", status_code=303)