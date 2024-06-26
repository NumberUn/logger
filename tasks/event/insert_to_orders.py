import logging
from logging.config import dictConfig
from core.wrappers import try_exc_async


dictConfig({'version': 1, 'disable_existing_loggers': False, 'formatters': {
                'simple': {'format': '[%(asctime)s][%(threadName)s] %(funcName)s: %(message)s'}},
            'handlers': {'console': {'class': 'logging.StreamHandler', 'level': 'DEBUG', 'formatter': 'simple',
                'stream': 'ext://sys.stdout'}},
            'loggers': {'': {'handlers': ['console'], 'level': 'INFO', 'propagate': False}}})
logger = logging.getLogger(__name__)


class InsertToOrders:
    """
    Class for insert to orders table
    """

    def __init__(self, app):
        self.app = app
        self.worker_name = 'INSERT_TO_ORDERS'

    @try_exc_async
    async def run(self, payload: dict) -> None:
        """
        Get cursor and start insert func
        :param payload: dict with NOT NULL values (
                            id,
                            datetime,
                            ts,
                            context,
                            parent_id,
                            exchange_order_id,
                            type,
                            status,
                            exchange,
                            side,
                            symbol,
                            expect_price,
                            expect_amount_coin,
                            expect_amount_usd,
                            expect_fee,
                            factual_price,
                            factual_amount_coin,
                            factual_amount_usd,
                            factual_fee,
                            order_place_time,
                            env
        :return: None
        """

        logger.info(f"Start: {self.worker_name}")
        # logger.info(f"INSERT TO ORDERS GOT PAYLOAD:\n{payload}")
        async with self.app['db'].acquire() as cursor:
            # if not payload['exchange_order_id'] == 'default':
            #     if not await self.__select(payload, cursor):
            await self.__insert(payload, cursor)
        logger.info(f"Finish: {self.worker_name}")

    @staticmethod
    @try_exc_async
    async def __select(data: dict, cursor):
        sql = f"""
        select 
            *
        from 
            orders
        where 
            exchange_order_id = '{data['exchange_order_id']}'
        """

        return await cursor.fetch(sql)

    @staticmethod
    @try_exc_async
    async def __insert(data: dict, cursor) -> None:
        """
        Insert data to orders table
        :param data: dict with NOT NULL keys
        :param cursor: asyncpg cursor
        :return: None
        """
        sql = f"""
            insert into orders(
                id,
                datetime,
                ts,
                context,
                parent_id,
                exchange_order_id,
                type,
                status,
                exchange,
                side,
                symbol,
                expect_price,
                expect_amount_coin,
                expect_amount_usd,
                expect_fee,
                factual_price,
                factual_amount_coin,
                factual_amount_usd,
                factual_fee,
                order_place_time,
                env,
                oneway_ping_orderbook,
                oneway_ping_order,
                inner_ping
                )
            values(
                '{data['id']}',
                '{data['datetime']}',
                {data['ts']},
                '{data['context']}',
                '{data['parent_id']}',
                '{data['exchange_order_id']}',
                '{data['type']}',
                '{data['status']}',
                '{data['exchange_name']}',
                '{data['side']}',
                '{data['symbol']}',
                {data['expect_price']},
                {data['expect_amount_coin']},
                {data['expect_amount_usd']},
                {data['expect_fee']},
                {data['factual_price']},
                {data['factual_amount_coin']},
                {data['factual_amount_usd']},
                {data['factual_fee']},
                {data['order_place_time']},
                '{data['env']}',
                {data['oneway_ping_orderbook']},
                {data['oneway_ping_order']},
                {data['inner_ping']}
                )         
            """
        await cursor.execute(sql)

