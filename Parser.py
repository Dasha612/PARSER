import datetime
import requests
import time
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.errors import SessionPasswordNeededError
import csv
import asyncio
import aiohttp


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
        async with aiohttp.ClientSession() as session:

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
                        data_items = data.get('response', {}).get('items', [])

                    # Если данных больше нет, выходим из цикла
                    if not data:
                        break

                    for post in data:
                        post_date = post['date']

                        # Игнорируем закрепленные посты
                        if post.get('is_pinned', 0) == 1:
                            continue

                        post_date_readable = datetime.utcfromtimestamp(post_date).strftime('%Y-%m-%d %H:%M:%S')
                        #print(f"Дата поста: {post_date_readable}")

                        # Если пост за последние 24 часа
                        if one_day_ago <= post['date'] <= current_time:
                            all_posts.append({
                                "text": post.get("text", ""),
                                "link": f"https://vk.com/{self.domain}?w=wall{post['from_id']}_{post['id']}",
                                "date": post_date_readable
                            })
                        else:
                            print("Найдены все посты")
                            all_posts_sorted = sorted(all_posts, key=lambda x: x['date'])

                            return all_posts_sorted

                    print(f"Получено {len(all_posts)} постов, offset = {offset}")

                    # Увеличиваем сдвиг для следующего запроса
                    offset += 100

                    # Добавляем задержку, чтобы не вызвать ограничение API VK
                    await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"Произошла ошибка: {e}")
                    break

        # Сортировка постов по дате
        all_posts_sorted = sorted(all_posts, key=lambda x: x['date'])

        return all_posts_sorted

    # def vk_file_writer():


class TGParser(Parser):

    def __init__(self, ID, HASH, phone_number):
        self.client = TelegramClient('parser_tg', ID, HASH)
        self.phone_number = phone_number

    async def get_posts(self):
        posts = []

        return posts






class GoogleSheetsWriter:
    def __init__(self, credentials_json, spreadsheet_name):
        # Настройка доступа через сервисный аккаунт
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        self.client = gspread.authorize(creds)
        self.spreadsheet_name = spreadsheet_name

    async def write_data(self, data):
        # Открываем таблицу
        sheet = self.client.open(self.spreadsheet_name)

        # Получаем текущую дату в нужном формате для названия листа
        today_date = datetime.now().strftime('%Y-%m-%d')

        # Проверяем, существует ли лист с текущей датой
        try:
            worksheet = sheet.worksheet(today_date)
        except gspread.exceptions.WorksheetNotFound:
            # Если листа с такой датой нет, создаем новый
            worksheet = sheet.add_worksheet(title=today_date, rows="100", cols="3")

        # Записываем заголовки, если их еще нет
        if worksheet.cell(1, 1).value != "Текст поста":
            worksheet.append_row(["Текст поста", "Ссылка", "Дата публикации"])

        # Записываем данные
        for post in data:
            worksheet.append_row([post["text"], post["link"], post["date"]])



async def main():
    vk_parser = VKParser("7882a1f47882a1f47882a1f41a7b9cc7f4778827882a1f41e6b688dd789f59313170b67", 'mdk_nn', '5.199')

    # Получаем посты за последние 24 часа
    vk_posts = await vk_parser.get_posts()

    #Выводим количество постов за последние сутки
    print(f"Найдено {len(vk_posts)} постов в вк за последние 24 часа")
    # Пример использования GoogleSheetsWriter
    sheets_writer = GoogleSheetsWriter('credentials.json', 'MDK NN Data')

    data = []
    for i in range(len(vk_posts)):
        data.append({
            "text": vk_posts[i]['text'],
            "link": vk_posts[i]['link'],
            "date": vk_posts[i]['date']
        })

    await sheets_writer.write_data(data)

if __name__ == "__main__":
    asyncio.run(main())