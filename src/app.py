import asyncio
import os
import re
import vulcan_authorizer
from croniter import croniter
from aiocron import crontab, Cron
from vulcan_client import VulcanClient
from telegram import Telegram
from deepl import Deepl
from dotenv import load_dotenv
import datetime

load_dotenv()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

MESSAGES_SCHEDULE = os.getenv('MESSAGES_SCHEDULE')
GRADES_SCHEDULE = os.getenv('GRADES_SCHEDULE')
NEW_HOMEWORK_SCHEDULE = os.getenv('NEW_HOMEWORK_SCHEDULE')
NEXT_HOMEWORK_SCHEDULE = os.getenv('NEXT_HOMEWORK_SCHEDULE')
DEEPL_KEY = os.getenv('DEEPL_KEY')
DEEPL_LANG = os.getenv('DEEPL_LANG')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_CHAT_ID = os.getenv('ALLOWED_CHAT_ID')

vulcan: VulcanClient = None
telegram: Telegram = None


def start_if_cron_valid(cron: Cron):
    function_name = re.findall(r'<function\s+(\w+)', str(cron))[0]
    try:
        croniter(cron.spec)
        cron.start()
        print(f"{function_name} has been scheduled: {cron.spec}")
    except ValueError:
        print(f"{function_name} has not been scheduled: {cron.spec}")


@crontab(MESSAGES_SCHEDULE, start=False)
async def check_messages():
    # print(f"{datetime.datetime.now().time()}: check_messages")
    messages = await vulcan.get_new_messages()
    for message in messages:
        await telegram.send_mail(message)


@crontab(NEW_HOMEWORK_SCHEDULE, start=False)
async def check_homework_new():
    # print(f"{datetime.datetime.now().time()}: check_homework_new")
    homeworks = await vulcan.get_new_homework()
    for homework in homeworks:
        await telegram.send_homework(homework)


@crontab(NEXT_HOMEWORK_SCHEDULE, start=False)
async def check_homework_next():
    # print(f"{datetime.datetime.now().time()}: check_homework_next")
    homeworks = await vulcan.get_today_homework()
    for homework in homeworks:
        await telegram.send_homework(homework, remind=True)


@crontab(GRADES_SCHEDULE, start=False)
async def check_grades():
    # print(f"{datetime.datetime.now().time()}: check_grades")
    grades = await vulcan.get_new_grades()
    for grade in grades:
        await telegram.send_grade(grade)


async def init():
    global vulcan
    global telegram

    creds = await vulcan_authorizer.authenticate()
    if creds is None:
        return
    print("Authorized")

    vulcan = VulcanClient(creds)
    student = await vulcan.get_student()
    print(student)

    deepl = Deepl(DEEPL_KEY, DEEPL_LANG) if DEEPL_KEY is not None and DEEPL_KEY != '' else None
    telegram = Telegram(BOT_TOKEN, ALLOWED_CHAT_ID, deepl)


if __name__ == '__main__':
    loop.run_until_complete(init())

    if vulcan is None:
        print("Not authenticated. Exec the following command in order to authenticate \
(replace \'token\', \'symbol\', \'pin\', \'device_name\' with your values):")
        print('\
docker-compose exec vulcan-bot python -c "\
import vulcan_authorizer; import asyncio; \
asyncio.get_event_loop().run_until_complete(\
vulcan_authorizer.authenticate(\'token\', \'symbol\', \'pin\', \'device_name\')\
)" && docker-compose restart vulcan-bot')
        loop.run_forever()

    start_if_cron_valid(check_messages)
    start_if_cron_valid(check_grades)
    start_if_cron_valid(check_homework_new)
    start_if_cron_valid(check_homework_next)

    print("App started. Waiting for vulcan updates now.")

    loop.run_forever()
