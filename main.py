from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from routes_auth import router as auth_router
from routes_dice import router as dice_router

app = FastAPI(title='Odd Table - Old Dragon Dice Roller')

# Cria as tabelas no banco
Base.metadata.create_all(bind=engine)

# Registra as rotas da API
app.include_router(auth_router)
app.include_router(dice_router)

# Servir arquivos estáticos
static_dir = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=str(static_dir)), name='static')


# Rota principal — renderiza o index.html
@app.get('/')
def index():
    from pathlib import Path
    html = (Path(__file__).parent / 'templates' / 'index.html').read_text(encoding='utf-8')
    from starlette.responses import HTMLResponse
    return HTMLResponse(html)
