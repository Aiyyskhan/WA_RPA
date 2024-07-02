import os
import json
import random as r
from functools import wraps
import asyncio
from asyncio.exceptions import TimeoutError as AsyncioTimeoutError, CancelledError as AsyncioCancelledError
from playwright.async_api import async_playwright, expect, Page, Locator
from playwright._impl._api_types import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from fastapi import WebSocket


URL = "https://web.whatsapp.com"

URL_CONNECT_TIMEOUT = 120*1000
QR_SEARCH_TIMEOUT = 120*1000
CHAT_SEARCH_TIMEOUT = 120*1000
NO_CONTACT_SEARCH_TIMEOUT = 3*1000
MESSAGE_FIELD_SEARCH_TIMEOUT = 60*1000
WAITING_SEND_MESSAGE_TIMEOUT = 60*1000

PW_DIR = os.path.join(os.getcwd(), './tmp/playwright')
QR_DIR = os.path.join(os.getcwd(), './tmp/qr')

WS: WebSocket = None

status_array = []

def event_capture(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        log = {"name":func.__name__}
        try:
            res = await func(*args, **kwargs)
            log["status"] = "success"
            return res
        except PlaywrightError as err:
            log["status"] = "PlaywrightError"
        except PlaywrightTimeoutError as err:
            log["status"] = "PlaywrightTimeoutError"
        except AsyncioTimeoutError as err:
            log["status"] = "AsyncioTimeoutError"
        except AsyncioCancelledError as err:
            log["status"] = "cancelled"
        finally:
            status_array.append(log)
            await WS.send_text(f"{log}")
    return wrapper

@event_capture
async def url_connect(url: str, page: Page, timeout: int) -> None:
    await page.goto(url, timeout=timeout) #, wait_until="domcontentloaded")

@event_capture
async def qr_search(page: Page, timeout: int) -> Locator | None:
    """
    Функция поиска QR.
    """
    el = page.get_by_test_id("qrcode")
    await el.wait_for(timeout=timeout)
    for t in asyncio.all_tasks():
        if t.get_name() == 'chatSearchTask':
            t.cancel()
    return el

@event_capture
async def chat_search(page: Page, timeout: int) -> Locator | None:
    """
    Функция поиска поля ввода номера чата.
    """
    el = page.get_by_test_id("chat-list-search")
    await el.wait_for(timeout=timeout)
    for t in asyncio.all_tasks():
        if t.get_name() == 'qrSearchTask':
            t.cancel()
    return el

@event_capture
async def no_contact_search(page: Page, timeout: int) -> bool | None:
    """
    Функция определения отсутствия контакта.
    """
    el = page.get_by_test_id("search-no-chats-or-contacts")
    await el.wait_for(timeout=timeout)
    return True

@event_capture
async def message_field_search(page: Page, timeout: int) -> Locator | None:
    """
    Функция поиска поля ввода сообщения.
    """
    el = page.get_by_test_id("conversation-compose-box-input")
    await el.wait_for(timeout=timeout)
    return el

@event_capture
async def waiting_send_message(page: Page, timeout: int) -> None:
    """
    Функция ожидания отправки сообщения.
    """
    el = page.get_by_test_id("msg-time")
    await expect(el).to_have_count(0, timeout=timeout)

@event_capture
async def send_message_request(phone: str, text: str, page: Page) -> None:
    """
    Функция отправки сообщения по номеру через GET-запрос.
    """
    await url_connect(f"{URL}/send?phone={phone}&text={text}", page, URL_CONNECT_TIMEOUT)

async def enter_text(text: str, typing: bool, page: Page, el: Locator) -> None:
    """
    Функция печати и отправки текста.
    """
    await page.wait_for_timeout(r.randint(1000, 3000))
    await el.click()
    await page.wait_for_timeout(r.randint(1000, 2000))
    await el.press("Control+A")
    await page.wait_for_timeout(r.randint(1000, 2000))
    await el.press("Delete")
    await page.wait_for_timeout(r.randint(1000, 3000))
    if typing:
        await el.type(text, delay=200)
    else:
        await el.fill(text)
    await page.wait_for_timeout(r.randint(1000, 3000))
    await el.press("Enter")

async def send_message(phone: str, text: str, page: Page, el: Locator) -> None:
    """
    Функция отправки сообщения по номеру.
    """
    log = {"name":"send_message", "phone": phone, "text": text}
    await enter_text(phone, True, page, el)
    contact_is_missing = await no_contact_search(page, NO_CONTACT_SEARCH_TIMEOUT)
    if contact_is_missing:
        await send_message_request(phone, text, page)
        el = await message_field_search(page, MESSAGE_FIELD_SEARCH_TIMEOUT)
        await el.press("Enter")
        await waiting_send_message(page, WAITING_SEND_MESSAGE_TIMEOUT)
    else:
        el = await message_field_search(page, MESSAGE_FIELD_SEARCH_TIMEOUT)
        await enter_text(text, False, page, el)
        await waiting_send_message(page, WAITING_SEND_MESSAGE_TIMEOUT)
    log["status"] = "success"
    status_array.append(log)
    await WS.send_text(f"{log}")

async def send_multiple_messages(cont_mess_arr: list, page: Page, el: Locator) -> None:
    """
    Функция отправки множества сообщений.
    """
    for item in cont_mess_arr:
        await send_message(item["contact"], item["message"], page, el)
        await page.wait_for_timeout(r.randint(1000, 2000))
        el = await chat_search(page, CHAT_SEARCH_TIMEOUT)

async def send_qr_code() -> None:
    with open(f"{QR_DIR}/qr.png", "rb") as image:
        qr_img = bytearray(image.read())
        await WS.send_bytes(qr_img)

async def main() -> None:
    """
    Функция запуска RPA.
    """
    status_array.clear()

    data = await WS.receive_text()
    await WS.send_text(data)
    arr = json.loads(data)
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            PW_DIR, 
            channel="chrome",
            headless=False, 
            slow_mo=50,
            viewport={"width":1000, "height":500}
            )
        page = await context.new_page()
        
        await url_connect(URL, page, URL_CONNECT_TIMEOUT)

        qr_search_task = asyncio.create_task(qr_search(page, QR_SEARCH_TIMEOUT), name="qrSearchTask")
        chat_search_task = asyncio.create_task(chat_search(page, CHAT_SEARCH_TIMEOUT), name="chatSearchTask")
        
        ret = await asyncio.gather(qr_search_task, chat_search_task)

        if ret[0] != None:
            await ret[0].screenshot(path=f"{QR_DIR}/qr.png")
            await send_qr_code()
            el = await chat_search(page, CHAT_SEARCH_TIMEOUT)
            await send_multiple_messages(arr, page, el)
        elif ret[1] != None:
            await send_multiple_messages(arr, page, ret[1])
        else:
            print("Ой, что-то пошло не так! :(")
        
        await context.close()
    await WS.close()

# def run(arr) -> None:
#     asyncio.run(main(arr))

# тестовый массив с номерами и сообщениями
# test_arr = [
#     {
#     "contact": "7**********",
#     "message": "Добрый день! 😊✨\n\nЭто _проверка_ *RPA*",
#     "userId": 1234
#     },
#     {
#     "contact": "7**********",
#     "message": "Добрый день! 😊✨\n\nЭто _проверка_ *RPA*",
#     "userId": 1234
#     },
#     {
#     "contact": "7**********",
#     "message": "Добрый день! 😊✨\n\nЭто _проверка_ *RPA*",
#     "userId": 1234
#     },
# ]