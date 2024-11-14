import datetime
import time
import certifi
import ssl
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from gspread_formatting import *
from fuzzywuzzy import fuzz

ssl_context = ssl.create_default_context(cafile=certifi.where())
token = '7882a1f47882a1f47882a1f41a7b9cc7f4778827882a1f41e6b688dd789f59313170b67'
version = '5.199'
domain = 'mdk_nn'

class Parser:
    def get_posts(self):
        raise NotImplementedError("Этот метод должен быть реализован в подклассе")

class VKParser(Parser):


    def __init__(self, token, domain, version):
        self.token = token
        self.domain = domain
        self.version = version

    async def get_posts(self):
        all_posts = []
        offset = 0

        # Время начала и конца предыдущего дня (последние 24 часа)
        current_time = int(time.time())  # Текущее время в формате Unix
        one_day_ago = current_time - 86400  # 24 часа назад
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:

            while True:
                try:
                    async with session.get(
                            "https://api.vk.com/method/wall.get",
                            params={
                                'access_token': self.token,
                                'v': self.version,
                                'domain': self.domain,
                                'count': 100,  # Получаем 100 постов за раз для оптимизации
                                'offset': offset
                            }
                    ) as response:
                        data = await response.json()

                        # Добавляем проверку, что 'response' и 'items' действительно существуют и являются списком
                        if 'response' not in data or 'items' not in data['response']:
                            print("Нет данных в ответе от ВКонтакте")
                            break

                        data_items = data['response']['items']

                        # Если данных больше нет, выходим из цикла
                        if not data_items:
                            break

                        for post in data_items:
                            post_date = post['date']

                            # Игнорируем закрепленные посты
                            if post.get('is_pinned', 0) == 1:
                                continue

                            post_date_readable = datetime.utcfromtimestamp(post_date).strftime('%Y-%m-%d %H:%M:%S')

                            # Если пост за последние 24 часа
                            if one_day_ago <= post['date'] <= current_time:
                                all_posts.append({
                                    "text": post.get("text", ""),
                                    "link": f"https://vk.com/{self.domain}?w=wall{post['from_id']}_{post['id']}",
                                    "date": post_date_readable
                                })
                            else:
                                all_posts_sorted = sorted(all_posts, key=lambda x: x['date'])
                                return all_posts_sorted

                        offset += 100

                        # Задержка для предотвращения ограничения API VK
                        await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"Произошла ошибка: {e}")
                    break

        all_posts_sorted = sorted(all_posts, key=lambda x: x['date'])
        return all_posts_sorted


# TGParser - класс для работы с Telegram API и парсинга сообщений из канала
class TGParser(Parser):

    def __init__(self, ID, HASH, phone_number):
        # Инициализация клиента TelegramClient с сессией 'parser_tg'
        self.client = TelegramClient('parser_tg', ID, HASH,  system_version="4.16.30-vxCUSTOM")

        self.phone_number = phone_number  # Сохранение номера телефона для авторизации

    # Асинхронная функция для получения постов
    async def get_posts(self):
        # Запуск клиента Telegram
        await self.client.start()  # Необходимо использовать self.client, а не client

        # Проверка, авторизован ли пользователь в Telegram
        if not await self.client.is_user_authorized():  # Используем self.client
            # Если пользователь не авторизован, отправляем ему код на телефон
            await self.client.send_code_request(self.phone_number)
            try:
                # Пользователю нужно ввести код, который он получил на свой номер телефона
                await self.client.sign_in(self.phone_number, input('Enter the code: '))
            except SessionPasswordNeededError:
                # Если у пользователя включена двухфакторная аутентификация (2FA), потребуется пароль
                await self.client.sign_in(password=input('Password: '))

        # Получение информации о текущем пользователе
        me = await self.client.get_me()

        channel_url = '@MDK_NN'

        # Получаем объект канала на основе URL
        my_channel = await self.client.get_entity(channel_url)
        all_messages = []
        offset_id = 0  # Начальное значение смещения для итерации по сообщениям

        # Время начала и конца предыдущего дня (последние 24 часа)
        current_time = int(time.time())  # Текущее время в формате Unix
        one_day_ago = current_time - 86400  # 24 часа назад

        while True:
            try:
                # Получение истории сообщений из канала
                history = await self.client(GetHistoryRequest(
                    peer=my_channel,
                    offset_id=offset_id,
                    offset_date= None,  # Сообщения с даты за предыдущие 24 часа
                    add_offset=0,
                    limit=100,  # Получаем 100 сообщений за раз
                    max_id=0,
                    min_id=0,
                    hash=0
                ))

                # Если сообщений нет, выходим из цикла
                if not history.messages:
                    break

                for message in history.messages:
                    message_timestamp = int(message.date.timestamp())  # Преобразуем дату в Unix-время

                    # Если сообщение за последние 24 часа
                    if one_day_ago <= message_timestamp <= current_time:
                        message_date_readable = message.date.strftime('%Y-%m-%d %H:%M:%S')
                        if "#реклама" in message.message or message.message == '':
                            continue
                        else:
                            all_messages.append({
                                "text": message.message,
                                "date": message_date_readable,
                                "id": message.id,
                                "link": f"https://t.me/{my_channel.username}/{message.id}"
                            })
                    else:
                        print("Найдены все посты")
                        all_messages_sorted = sorted(all_messages, key=lambda x: x['date'])

                        return all_messages_sorted

                # Обновляем offset_id для следующей итерации
                offset_id = history.messages[-1].id

                # Задержка для предотвращения ограничения API Telegram
                await asyncio.sleep(0.3)

            except Exception as e:
                print(f"Произошла ошибка: {e}")
                break

        all_messages_sorted = sorted(all_messages, key=lambda x: x['date'])
        return all_messages_sorted


class OKParser:
    def __init__(self, url):
        self.url = url

    async def get_today_posts(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers) as response:
                print("Status Code:", response.status)
                if response.status != 200:
                    print("Failed to retrieve the page.")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                todays_posts = []
                posts = soup.find_all('div', class_='feed-w')

                for post in posts:
                    date_div = post.find('div', class_='feed-info-date feed-info-subtitle_i')
                    post_date = date_div.find('time').text if date_div and date_div.find('time') else "Дата не найдена"


                    if ":" in post_date and "вчера" not in post_date:
                        link_tag = post.find('a', class_='media-text_heading-lnk-v2')
                        link = 'https://ok.ru' + link_tag.get('href') if link_tag else "Ссылка не найдена"
                        text_div = post.find('div', class_='media-text_cnt_tx')
                        text = text_div.get_text(strip=True) if text_div else "Текст не найден"
                        todays_posts.append({
                            "text": text[:-3],
                            "link": link
                        })

                return todays_posts


class GoogleSheetsWriter:
    def __init__(self, credentials_json, spreadsheet_name):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        self.client = gspread.authorize(creds)
        self.spreadsheet_name = spreadsheet_name

    async def write_data(self, data):
        sheet = self.client.open(self.spreadsheet_name)
        today_date = datetime.now().strftime('%Y-%m-%d')

        try:
            worksheet = sheet.worksheet(today_date)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=today_date, rows="100", cols="4")

        if worksheet.cell(1, 1).value != "Текст поста":
            worksheet.append_row(["Текст поста", "Ссылка ТГ", "Ссылка ВК", "Ссылка ОК"])

        rows_to_append = []
        for post in data:
            rows_to_append.append([post["text"], post.get("tg_link", ""), post.get("vk_link", ""), post.get("ok_link", "")])

        for row in rows_to_append:
            worksheet.append_row(row)
        self.apply_formatting(worksheet)

    def apply_formatting(self, worksheet):
        # Enable text wrapping in the entire worksheet
        format_cell_range(worksheet, 'A:D', CellFormat(
            wrapStrategy='WRAP'
        ))

        # Auto-resize columns to fit content
        set_column_widths(worksheet, [('A', 300), ('B', 200), ('C', 200), ('D', 200)])


def is_similar(text1, text2, threshold=75):

    similarity = fuzz.partial_ratio(text1, text2)
    return similarity > threshold


def shorten_ok_link(link):
    return link.split('?')[0]


async def main():

    vk_parser = VKParser("7882a1f47882a1f47882a1f41a7b9cc7f4778827882a1f41e6b688dd789f59313170b67", 'mdk_nn', '5.199')

    # Получаем посты за последние 24 часа
    vk_posts = await vk_parser.get_posts()


    # Пример использования GoogleSheetsWriter
    sheets_writer = GoogleSheetsWriter('credentials.json', 'MDK NN Data')
    unique_posts = []


    tg_parser = TGParser('23706087', '96b3c3744ed446a5192186c40f517564', '+79087235739')
    tg_posts = await tg_parser.get_posts()

    ok_parser = OKParser('https://ok.ru/group/61322896802030')
    ok_posts = await ok_parser.get_today_posts()



    for vk_post in vk_posts:
        is_duplicate = False
        for tg_post in tg_posts:
            if is_similar(vk_post['text'], tg_post['text']):
                # Если посты похожи, объединяем информацию
                unique_posts.append({
                    "text": vk_post['text'],  # или tg_post['text']
                    "vk_link": vk_post['link'],
                    "tg_link": tg_post['link']
                })
                is_duplicate = True
                break

        # Если не найдено похожего поста в ТГ, добавляем ВК пост как уникальный
        if not is_duplicate:
            unique_posts.append({
                "text": vk_post['text'],
                "vk_link": vk_post['link']
            })

        # Добавляем уникальные посты из Телеграма, которых нет в ВК
    for tg_post in tg_posts:
        is_duplicate = False
        for vk_post in vk_posts:
            if is_similar(vk_post['text'], tg_post['text']):
                is_duplicate = True
                break

        if not is_duplicate:
            unique_posts.append({
                "text": tg_post['text'],
                "tg_link": tg_post['link']
            })


    for ok_post in ok_posts:
        is_duplicate = False
        for unique_post in unique_posts:
            # Проверка на совпадение с существующим постом
            if is_similar(ok_post['text'], unique_post['text']):
                is_duplicate = True
                unique_post["ok_link"] = shorten_ok_link(ok_post['link'])  # Сокращаем ссылку и добавляем её
                break

        # Если пост из ОК уникальный, добавляем его как новый пост
        if not is_duplicate:
            unique_posts.append({
                "text": ok_post['text'],
                "ok_link": shorten_ok_link(ok_post['link'])  # Сокращаем ссылку
            })



    await sheets_writer.write_data(unique_posts)


if __name__ == "__main__":
    asyncio.run(main())