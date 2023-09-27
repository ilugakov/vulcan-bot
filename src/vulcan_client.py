from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import List, Callable, TypeVar, AsyncIterable, Deque, Any, Coroutine
from vulcan import Vulcan, data, Keystore, Account, model
from collections import deque

T = TypeVar("T")


class SyncTime:
    def __init__(self):
        self.datetime = datetime.now() - timedelta(days=1)


class LastSync:
    def __init__(self):
        self.homework = SyncTime()
        self.grades = SyncTime()
        self.messages = SyncTime()


class VulcanClient:
    def __init__(self, credentials: (Keystore, Account)):
        self.keystore = credentials[0]
        self.account = credentials[1]
        self.message_box = None
        self.last_sync = LastSync()
        self.already_seen_items = deque(maxlen=30)

    async def get_client(self) -> Vulcan:
        client = Vulcan(self.keystore, self.account)
        await client.select_student()
        return client

    async def get_student(self) -> model.Student:
        client = await self.get_client()
        student = client.student
        await client.close()
        return student

    async def get_today_homework(self) -> List[data.Homework]:
        client = await self.get_client()
        async with client:
            iterator = await client.data.get_homework(date.today() - timedelta(days=5))
            homework = [hw async for hw in iterator]
            homework = [hw for hw in homework if hw.deadline.date > date.today()]

            if not homework:
                return []

            homework_by_deadline = defaultdict(list)
            for hw in homework:
                homework_by_deadline[hw.deadline.date].append(hw)

            closest_deadline = min(homework_by_deadline.keys())
            homework = homework_by_deadline[closest_deadline]

            return homework

    async def get_new_data(
            self,
            get_data_func: Callable[[Any], Coroutine[Any, Any, AsyncIterable[T]]],
            last_sync: SyncTime,
    ) -> List[T]:
        client = await self.get_client()
        async with client:
            new_last_sync = await client.data.get_time()
            new_last_sync = new_last_sync.date_time
            iterator = await get_data_func(client)

            new_data = [item async for item in iterator]
            new_data = [item for item in new_data if not any(x == item.id for x in self.already_seen_items)]

            for item in new_data:
                self.already_seen_items.append(item.id)

            last_sync.datetime = new_last_sync
            return new_data

    async def get_new_homework(self) -> List[data.Homework]:
        return await self.get_new_data(
            get_data_func=lambda client: client.data.get_homework(
                self.last_sync.homework.datetime - timedelta(minutes=30)),
            last_sync=self.last_sync.homework,
        )

    async def get_new_grades(self) -> List[data.Grade]:
        return await self.get_new_data(
            get_data_func=lambda client: client.data.get_grades(self.last_sync.grades.datetime - timedelta(minutes=30)),
            last_sync=self.last_sync.grades,
        )

    async def get_new_messages(self) -> List[data.Message]:
        if self.message_box is None:
            mb_client = await self.get_client()
            async with mb_client:
                message_boxes = await mb_client.data.get_message_boxes()
                self.message_box = await anext(message_boxes)
                self.message_box = self.message_box.global_key

        return await self.get_new_data(
            get_data_func=lambda client: client.data.get_messages(self.message_box,
                                                                  self.last_sync.messages.datetime - timedelta(
                                                                      minutes=30)),
            last_sync=self.last_sync.messages,
        )
