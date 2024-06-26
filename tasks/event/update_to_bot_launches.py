import logging
from logging.config import dictConfig
from core.wrappers import try_exc_async


dictConfig({'version': 1, 'disable_existing_loggers': False, 'formatters': {
                'simple': {'format': '[%(asctime)s][%(threadName)s] %(funcName)s: %(message)s'}},
            'handlers': {'console': {'class': 'logging.StreamHandler', 'level': 'DEBUG', 'formatter': 'simple',
                'stream': 'ext://sys.stdout'}},
            'loggers': {'': {'handlers': ['console'], 'level': 'INFO', 'propagate': False}}})
logger = logging.getLogger(__name__)


class UpdateBotLaunches:
    """
    Class for update to bot_launches table
    """

    def __init__(self, app):
        self.app = app
        self.worker_name = 'UPDATE_BOT_LAUNCHES'

    @try_exc_async
    async def run(self, payload: dict) -> None:
        logger.info(f"Start: {self.worker_name}")
        async with self.app['db'].acquire() as cursor:
            await self.__update(payload, cursor)
        logger.info(f"Finish: {self.worker_name}")

    @staticmethod
    @try_exc_async
    async def __update(payload, cursor) -> None:
        to_update = ""

        for k, v in payload.items():
            if k != 'launch_id':
                if isinstance(v, int):
                    v = v
                elif isinstance(v, float):
                    v = v
                else:
                    v = "'" + str(v) + "'"

                to_update += f"{k} = {v},\n"

        sql = f"""
           update 
               bot_launches
           set 
               {to_update[:-2]}
           where 
               id = '{payload['launch_id']}'
           """

        await cursor.execute(sql)




