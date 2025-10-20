from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import uuid

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from pydantic import BaseModel

from datetime import datetime
from time import sleep
from zoneinfo import ZoneInfo

from .services.receipt_printer_service import print_chore

# scheduler
jobstores = {
  'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(
  jobstores=jobstores,
  timezone='America/New_York'
)
scheduler.start()

# model for creating chores
class Chore(BaseModel):
  description: str | None = None
  start: datetime = datetime.now()
  interval: int | None = 7

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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
  for job in scheduler.get_jobs():
    chorelist.append({
      "id": job.id,
      "description": job.name,
      "interval": job.trigger.interval.days,
      "next_run": job.next_run_time
    })
  chorelist.sort(key=lambda item: item['next_run'])
  return templates.TemplateResponse("chores/index.html", {"request": request, "chorelist": chorelist})
  
@app.get("/chores/new", response_class=HTMLResponse)
async def new_chore(request: Request):
  chore = Chore()
  return templates.TemplateResponse("chores/new.html", {"request": request, "chore": chore})

@app.post("/chores/")
async def create_chore(request: Request, description: str = Form(...), start: datetime = Form(...), interval: int = Form(...)):
  job_id = uuid.uuid1()
  scheduler.add_job(
    print_job,
    'interval',
    id=str(job_id),
    name=description,
    args=[description],
    start_date=start,
    days=interval
  )
  return RedirectResponse(url="/chores", status_code=303)

@app.get("/chore/{id}/edit", response_class=HTMLResponse)
async def edit_chore(request: Request, id: str):
  job = scheduler.get_job(id)
  chore = Chore(
    description=job.name,
    start=job.trigger.start_date,
    interval=job.trigger.interval.days
  )
  return templates.TemplateResponse("chores/edit.html", {"request": request, "chore": chore, "id": id})

@app.post("/chore/{id}")
async def update_chore(request: Request, id: str, description: str = Form(...), start: datetime = Form(...), interval: int = Form(...)):
  job = scheduler.get_job(id)
  job.modify(
    name=description
  )
  job.reschedule(
    'interval',
    start_date=start,
    days=interval
  )
  return RedirectResponse(url="/chores", status_code=303)

@app.post("/chore/{id}/run_chore")
async def run_chore(request: Request, id: str):
  job = scheduler.get_job(id)
  current_dt = datetime.now()
  run_dt = job.next_run_time
  new_dt = current_dt + job.trigger.interval

  # trigger now
  print_chore(job.name)

  # reset next chore time to later date
  job.modify(next_run_time=new_dt.replace(
      hour=run_dt.hour,
      minute=run_dt.minute,
      second=0,
      microsecond=0
    )
  )
  return RedirectResponse(url="/chores", status_code=200)


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
  chore = scheduler.get_job(id)
  if chore == None:
    raise HTTPException(status_code=404, detail="Chore not found")
  scheduler.remove_job(id)
  return RedirectResponse(url="/chores", status_code=303)