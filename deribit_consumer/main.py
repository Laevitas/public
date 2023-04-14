import asyncio
import json
import sys
from typing import Dict
from loguru import logger
from datetime import timedelta, datetime
import websockets

client_id = 'HD5Poh0t'
client_secret = 'B4rgiZopaPg83Od0oah037IUPJ96teR8-1svxUmeFB8'
channels = ["ticker.BTC-29DEC23-16000-C.raw", "ticker.BTC-29DEC23-18000-C.raw", "ticker.BTC-29DEC23-20000-C.raw"]

class Main:
    def __init__(
            self,
            client_id: str,
            client_secret: str,
            channels: list

    ) -> None:

        self.loop = asyncio.get_event_loop()

        self.deribit_url: str = self.get_url()
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.ws_client: websockets.WebSocketClientProtocol = None
        self.refresh_token = None
        self.expiration_time = None
        self.channels: list = channels
        self.params = {
            "jsonrpc": "2.0",
            "method": None,
        }
        # Start Primary Coroutine
        self.loop.run_until_complete(
            self.runner()
        )

    def connectws(self, deribit_url):
        logger.info("Establishing connection to Deribit WebSocket {}".format(deribit_url))
        try:
            return websockets.connect(deribit_url)

        except Exception:
            logger.error('Unable to connect to Deribit {}'.format(deribit_url))

    async def runner(self) -> None:

        async with self.connectws(self.deribit_url) as self.ws_client:
            logger.info("Connected successfully, proceeding to authentication ...")
            await self.auth()

            logger.info("Sending a heartbeat request...")
            await self.heartbeat_request()

            self.loop.create_task(
                self.reauthenticate()
            )

            # logger.info('subscribing to receive data for the following channels {}', format(channels))
            await self.subscription(channels=self.channels)
            # logger.info('Start processing incoming messages ...')
            while self.ws_client.open:
                msg = json.loads(await self.ws_client.recv())
                if 'id' in list(msg):
                    if msg['id'] == 9929:
                        if self.refresh_token is None:
                            x = 1
                            logger.info("Authenticated with User {},".format(self.client_id))
                        else:
                            print("Re-authentication proceeded")
                            self.refresh_token = msg['result']['refresh_token']
                            # Refresh Authentication well before the required datetime
                            expires_in = msg['result']['expires_in'] - 300
                            self.expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
                            print(self.expiration_time)

                    elif msg['id'] == 8212:
                        continue

                elif 'method' in list(msg):
                    # Respond to Heartbeat Message
                    if msg['method'] == 'heartbeat':
                        await self.heartbeat_response()
                    if msg['method'] == 'subscription':
                        #TODO: To be persisted
                        data = msg['params']['data']
                        print(data)

    def get_url(self):
        url = 'wss://test.deribit.com/ws/api/v2'
        return url

    async def subscription(
            self,
            channels: list
    ) -> None:
        # Request to subscribe to the provided channels
        add_params: dict = {
            "channels": channels
        }

        self.params["method"] = "public/subscribe"
        self.params["id"] = 42
        self.params["params"] = add_params
        await self.ws_client.send(
            json.dumps(
                self.params
            )
        )

    async def auth(self) -> None:
        add_params: dict = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        print(add_params)
        self.params["id"] = 9929
        self.params["method"] = "public/auth"
        self.params["params"] = add_params
        logger.info(json.dumps(
                self.params
            ))
        # logger.info('Authenticating using provided user {}'.format(self.client_id))
        await self.ws_client.send(
            json.dumps(
                self.params
            )
        )

    async def reauthenticate(self) -> None:
        while True:
            if self.expiration_time is not None:
                if datetime.utcnow() > self.expiration_time:
                    add_params: dict = {
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token
                    }

                    self.params["method"] = "public/auth"
                    self.params["id"] = 9929
                    self.params["params"] = add_params
                    logger.info('Re-authenticating using provided user {}'.format(self.client_id))
                    await self.ws_client.send(
                        json.dumps(
                            self.params
                        )
                    )

            await asyncio.sleep(1)

    async def heartbeat_request(self) -> None:
        """
        Requests DBT's `public/set_heartbeat` to
        establish a heartbeat connection.
        """
        add_params: Dict = {
            "interval": 30
        }

        self.params["method"] = "public/set_heartbeat"
        self.params["id"] = 9098
        self.params["params"] = add_params

        await self.ws_client.send(
            json.dumps(
                self.params
            )
        )

    logger.info("Sending a heartbeat response to public/test endpoint...")

    async def heartbeat_response(self) -> None:
        """
        Sends the required WebSocket response to
        the Deribit API Heartbeat message.
        """

        add_params: Dict = {
        }

        self.params["method"] = "public"
        self.params["id"] = 8212
        self.params["params"] = add_params
        await self.ws_client.send(
            json.dumps(
                self.params
            )
        )



if __name__ == "__main__":
    # Configuration of loguru
    logger.add(sys.stderr, format="{thread.name} | {time} | {level} | {message}", serialize=True, enqueue=True)
    try:

        Main(
            client_id=client_id,
            client_secret=client_secret,
            channels=channels
        )
    except KeyboardInterrupt:
        pass
