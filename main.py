from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

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
  id: str
  description: str
  start: datetime = datetime.now()
  interval: int = 7

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="src/templates")

def print_job(description):
  print(description)

@app.get("/", response_class=HTMLResponse)
async def get_chores(request: Request):
  chorelist = []
  for chore in scheduler.get_jobs():
    chorelist.append({
      "id": chore.id,
      "description": chore.name,
      "next_run": chore.next_run_time
    })
  return templates.TemplateResponse("index.html", {"request": request, "chorelist": chorelist})
  
@app.post("/chores/")
async def create_chore(chore: Chore):
  scheduler.add_job(print_job, 'interval', id=chore.id, name=chore.description, args=[chore.description], start_date=chore.start, days=chore.interval)
  return chore.id

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