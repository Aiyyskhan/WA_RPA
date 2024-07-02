from fastapi import FastAPI, Request, WebSocket, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import src.warpa as warpa


app = FastAPI()

app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# тестовый массив с номерами и сообщениями
test_arr = [
    {
    "contact": "7**********",
    "message": "Добрый день! 😊✨\n\nЭто _проверка_ *RPA*\nrand_num: 777",
    "userId": 1234
    },
    # {
    # "contact": "7**********",
    # "message": f"Добрый день! 😊✨\n\nЭто _проверка_ *RPA*\nrand_num: {random.randint(0,1000)}",
    # "userId": 1234
    # },
    # {
    # "contact": "7**********",
    # "message": f"Добрый день! 😊✨\n\nЭто _проверка_ *RPA*\nrand_num: {random.randint(0,1000)}",
    # "userId": 1234
    # },
    # {
    # "contact": "7**********",
    # "message": f"Добрый день! 😊✨\n\nЭто _проверка_ *RPA*\nrand_num: {random.randint(0,1000)}",
    # "userId": 1234
    # },
]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
   return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/api/warpa_start")
async def rpa_run(ws: WebSocket):
    await ws.accept()
    await ws.send_text(
        """[{ "contact": "7**********", "message": "Добрый день! 😊✨\n\nЭто _проверка_ *RPA*\nrand_num: 777", "userId": 1234 }, 
        { "contact": "7**********", "message": "Добрый день! 😊✨\n\nЭто _проверка_ *RPA*\nrand_num: 777", "userId": 1234 }]
        """
    )
    warpa.WS = ws
    # while True:
    await warpa.main()

@app.get("/api/warpa_status")
def rpa_status():
    return {
        "status": status.HTTP_200_OK,
        "func": warpa.status_array
    }

# poetry run uvicorn src.main:app --reload