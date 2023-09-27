from datetime import datetime
from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from bs4 import BeautifulSoup
from vulcan import data
from deepl import Deepl


def clean_up_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    for paragraph in paragraphs:
        paragraph.replace_with(f"{paragraph.get_text()}\n")
    text = soup.get_text()
    text = text.strip()
    return text


class Telegram:
    def __init__(self, bot_token: str, chat_id: str, deepl: Deepl):
        self.deepl = deepl
        self.bot = Bot(token=bot_token)
        self.ALLOWED_CHAT_ID = chat_id

    async def translate(self, text: str, str_format: str) -> str:
        if not text or not self.deepl:
            return ''
        result = await self.deepl.translate(text)
        result = str_format.format(result)
        return result

    async def send_mail(self, message: data.Message) -> None:
        clean_content = clean_up_html(message.content)
        translated_subject = await self.translate(message.subject, '<b>Translated Subject:</b> {}\n')
        translated_content = await self.translate(clean_content, '\n<b>Translation:</b>\n{}')
        formatted_message = (
            f"<b>✉ Message</b>\n"
            f"<b>Subject:</b> {message.subject}\n"
            f"{translated_subject}"
            f"<b>Sender:</b> {message.sender.name}\n"
            f"<b>Sent Date:</b> {message.sent_date.date} {message.sent_date.time}\n\n"
            f"{clean_content}\n"
            f"{translated_content}"
        )
        await self.bot.send_message(chat_id=self.ALLOWED_CHAT_ID, text=formatted_message, parse_mode=ParseMode.HTML)
        print(f"{datetime.now().time()}: email sent")

    async def send_homework(self, homework: data.Homework, remind: bool = False) -> None:
        clean_content = clean_up_html(homework.content)
        header = "🕒 Deadline approaching" if remind else "📚 New"
        translated_content = await self.translate(clean_content, '\n<b>Translation:</b> {}')
        formatted_message = (
            f"<b>{header} Homework</b>\n"
            f"<b>Subject:</b> {homework.subject.name}\n"
            f"<b>Teacher:</b> {homework.creator.name}\n"
            f"<b>Due date:</b> {homework.deadline.date}\n\n"
            f"{clean_content}\n"
            f"{translated_content}"
        )
        await self.bot.send_message(chat_id=self.ALLOWED_CHAT_ID, text=formatted_message, parse_mode=ParseMode.HTML)
        print(f"{datetime.now().time()}: homework sent")

    async def send_grade(self, grade: data.Grade) -> None:
        formatted_message = (
            f"<b>⭐ Grade</b>\n"
            f"<b>Subject:</b> {grade.column.subject.name} - {grade.column.name}\n"
            f"<b>Category:</b> {grade.column.category.name}\n"
            f"<b>Teacher:</b> {grade.teacher_created.display_name}\n"
            f"{grade.content}"
        )
        await self.bot.send_message(chat_id=self.ALLOWED_CHAT_ID, text=formatted_message, parse_mode=ParseMode.HTML)
        print(f"{datetime.now().time()}: grade sent")
