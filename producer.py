import asyncio
import logging
import orjson
from aio_pika import connect, ExchangeType, Message
from core.wrappers import try_exc_async

from tasks.all_tasks import PERIODIC_TASKS
import configparser
import sys
config = configparser.ConfigParser()
config.read(sys.argv[1], "utf-8")

logger = logging.getLogger(__name__)

periodic_tasks = PERIODIC_TASKS

setts = config['RABBIT']
RABBIT_URL = f"amqp://{setts['USERNAME']}:{setts['PASSWORD']}@{setts['HOST']}:{setts['PORT']}/"


class WorkerProducer:
    def __init__(self, loop):
        self.loop = loop
        self.rabbit_url = RABBIT_URL
        self.periodic_tasks = []

    @try_exc_async
    async def run(self):
        for task in periodic_tasks:
            self.periodic_tasks.append(self.loop.create_task(self._publishing_task(task)))

    @try_exc_async
    async def _publishing_task(self, task):
        await asyncio.sleep(task.get('delay', 0))

        while True:
            connection = await connect(url=self.rabbit_url, loop=self.loop)
            channel = await connection.channel()

            exchange = await channel.declare_exchange(task['exchange'], type=ExchangeType.DIRECT, durable=True)
            queue = await channel.declare_queue(task['queue'], durable=True)
            await queue.bind(exchange, routing_key=task['routing_key'])

            message = Message(orjson.dumps(task.get('payload', {})))
            await exchange.publish(message, routing_key=task['routing_key'])

            logger.info(f'Published message to queue {task["queue"]}')

            await connection.close()

            await asyncio.sleep(task['interval'])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    worker = WorkerProducer(loop)

    loop.run_until_complete(worker.run())

    try:
        loop.run_forever()
    finally:
        loop.close()
