from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import engine, Base
from routes_auth import router as auth_router
from routes_dice import router as dice_router

app = FastAPI(title='Odd Table')

# Create tables
Base.metadata.create_all(bind=engine)

# Templates
templates = Jinja2Templates(directory='templates')

# Static files
app.mount('/static', StaticFiles(directory='static'), name='static')

# Routers
app.include_router(auth_router)
app.include_router(dice_router)


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
