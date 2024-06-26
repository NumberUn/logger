import datetime
import logging
import time
from logging.config import dictConfig
from core.wrappers import try_exc_async

dictConfig({'version': 1, 'disable_existing_loggers': False, 'formatters': {
                'simple': {'format': '[%(asctime)s][%(threadName)s] %(funcName)s: %(message)s'}},
            'handlers': {'console': {'class': 'logging.StreamHandler', 'level': 'DEBUG', 'formatter': 'simple',
                'stream': 'ext://sys.stdout'}},
            'loggers': {'': {'handlers': ['console'], 'level': 'INFO', 'propagate': False}}})
logger = logging.getLogger(__name__)



class OrderStatuses:
    SUCCESS = 'Fully Executed'
    UNSUCCESS = 'Not Executed'

class DisbalanceStatuses:
    SUCCESS = 'Success'
    UNSUCCESS = 'Unsuccess'
    PARTIAL_SUCCESS = 'Partial_success'


class CheckAndUpdateDisbalances:
    ROUTING_KEY = 'logger.event.check_balance'
    EXCHANGE_NAME = 'logger.event.'
    QUEUE_NAME = 'logger.event.check_balance'

    def __init__(self, app):
        self.app = app
        self.worker_name = 'CHECK_AND_UPDATE_DISBALANCES'
        self.all_disbalances = []
        self.disbalances_to_update = []

    @try_exc_async
    async def run(self, payload: dict) -> None:
        logger.info(f"Start: {self.worker_name}")

        async with self.app['db'].acquire() as cursor:
            await self.__get_all_processing_arbitrage_possibilities_ids(cursor)
            await self.__get_orders_by_parent_id(cursor)
            await self.__update_arbitrage_possibilities(cursor)

        logger.info(f"Finish: {self.worker_name}")

    @try_exc_async
    async def __get_all_processing_arbitrage_possibilities_ids(self, cursor):
        sql = """
        select 
            id
        from 
           disbalances
        where 
            status = 'Processing' 
        order by
            ts desc
        """

        self.all_disbalances = [x['id'] for x in await cursor.fetch(sql)]

    @try_exc_async
    async def __get_orders_by_parent_id(self, cursor):
        for parent_id in self.all_disbalances:
            sql = f"""
            select 
                status
            from
                orders
            where 
                parent_id = '{parent_id}'
            """

            data = await cursor.fetch(sql)
            in_processing = False
            else_statuses = []

            for row in data:
                if row['status'] == 'Processing':
                    in_processing = True
                elif row['status'] == OrderStatuses.SUCCESS:
                    else_statuses.append(True)
                elif row['status'] == OrderStatuses.UNSUCCESS:
                    else_statuses.append(False)

            if not in_processing and all(else_statuses):
                self.disbalances_to_update.append(
                    {
                        'id': parent_id,
                        'status': DisbalanceStatuses.SUCCESS,
                        'status_datetime': datetime.datetime.utcnow(),
                        'status_ts': time.time()
                    }
                )
            elif not in_processing and any(else_statuses):
                self.disbalances_to_update.append(
                    {
                        'id': parent_id,
                        'status': DisbalanceStatuses.PARTIAL_SUCCESS,
                        'status_datetime': datetime.datetime.utcnow(),
                        'status_ts': time.time()
                    }
                )
            elif not in_processing and not all(else_statuses):
                self.disbalances_to_update.append(
                    {
                        'id': parent_id,
                        'status': DisbalanceStatuses.UNSUCCESS,
                        'status_datetime': datetime.datetime.utcnow(),
                        'status_ts': time.time()
                    }
                )

    @try_exc_async
    async def __update_arbitrage_possibilities(self, cursor):
        for data in self.disbalances_to_update:
            sql = f"""
                    update 
                        disbalances
                    set 
                        status = '{data['status']}',
                        status_datetime = '{data['status_datetime']}',
                        status_ts = {data['status_ts']}
                    where 
                        id = '{data['id']}'
                    """

            await cursor.execute(sql)
