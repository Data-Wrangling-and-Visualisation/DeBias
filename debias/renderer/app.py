import asyncio
from collections import defaultdict
from datetime import datetime

import redis.asyncio as aioredis
from core.parser import Parser
from faststream import ContextRepo, FastStream, Logger
from faststream.exceptions import AckMessage, NackMessage, RejectMessage
from faststream.nats import NatsBroker, NatsMessage, PullSub
from renderer.renderer import Renderer

from debias.core.metastore import Metadata, Metastore
from debias.core.models import FetchRequest, ProcessRequest, RenderRequest
from debias.core.s3 import S3Client
from debias.renderer.config import Config
from debias.renderer.utils import absolute_url, extract_domain, hashsum, normalize_url

broker = NatsBroker(pedantic=True)
app = FastStream(broker)


class DI:
    """Dependency Injection Container"""

    @classmethod
    def init(cls, config: str):
        Config.model_config["toml_file"] = config

        # calling __init__ function of Config class will load all configuration
        # however, type checkers do not like it
        # type: ignore
        cls.config = Config()  # type: ignore
        cls.keyvalue = aioredis.Redis.from_url(cls.config.keyvalue.dsn)
        cls.s3 = S3Client(cls.config.s3)
        cls.metastore = Metastore(cls.config.pg.connection)
        cls.parsers: dict[str, Parser | None] = defaultdict(lambda: None)
        cls.renderer = Renderer()

        cls.fetch_queue_publisher = broker.publisher(subject="fetch-queue", stream="debias")
        cls.render_queue_publisher = broker.publisher(subject="render-queue", stream="debias")
        cls.process_queue_publisher = broker.publisher(subject="process-queue", stream="debias")
        cls.metadata_queue_publisher = broker.publisher(subject="metadata-queue", stream="debias")


@app.on_startup
async def app_on_startup(context: ContextRepo, config: str):
    """Lifespan hook that is called when application is starting
    before it starts accepting any request or declaring queues
    """
    DI.init(config)
    context.set_global("config", DI.config)

    for target_config in DI.config.app.targets:
        parser = Parser(target_config)
        DI.parsers[parser.domain] = parser
    await DI.renderer.init()

    await broker.connect(DI.config.nats.dsn.encoded_string())


@app.after_startup
async def app_after_startup(context: ContextRepo, logger: Logger):
    """Lifespan hook that is called after application is started"""
    await DI.metastore.init()

    logger.info("app started")


@app.on_shutdown
async def app_on_shutdown(context: ContextRepo):
    """Lifespan hook that is called when application is shutting down
    after it stops accepting any request or declaring queues
    """
    await DI.renderer.close()


@broker.subscriber(subject="render-queue", stream="debias", pull_sub=PullSub(batch_size=1))
async def broker_stream_subscriber(msg: NatsMessage, data: RenderRequest, logger: Logger, context: ContextRepo):
    """Handler which process each message from the queue.
    It subscribes to subject "render-queue", so all messages published exactly to "render-queue" subject
    would be processed by this handler.
    It subscribes to stream "debias" with retention policy "work_queue".
    This allows multiple subscribers to connect to the same stream and receive unqiue messages
    i.e. each message is received only once by only one subscriber).
    It utilizes pull subscription (other option is push subscription) which reduces load on the server
    by forcing each client to pull messages by its own.

    Read more about JetStream & Pulling Consumer here:
    - https://docs.nats.io/nats-concepts/jetstream
    - https://docs.nats.io/nats-concepts/jetstream/consumers
    - https://faststream.airt.ai/latest/nats/jetstream/pull
    """
    url = normalize_url(data.url)
    logger.info(f"received message {msg.message_id} (corrid: {msg.correlation_id}) to process {url}")

    parser = DI.parsers[extract_domain(url)]
    if parser is None:
        logger.warning(f"skipping url {url}: no parser registered")
        raise RejectMessage()  # refuse to process
    logger.debug(f"found registered parser for url {url}")

    logger.debug(f"checking if url {url} was rendered in last 12 hours")
    url_hash = hashsum(url)
    key = f"render:url_hash:{url_hash}"
    if (await DI.keyvalue.get(key)) is not None:
        logger.warning(f"skipping url {url}: url_hash {url_hash} is present")
        raise RejectMessage()  # refuse to process
    logger.debug(f"url hash {url_hash} is not present, processing url")
    await DI.keyvalue.set(key, "1", ex=60 * 60 * 12)  # expires in 12 hours

    content = await DI.renderer.render(url)
    content_hash = hashsum(content)

    filepath = f"{parser.config.id}/{url_hash}/{content_hash}.html"

    await finish(logger, parser, url, url_hash, content, content_hash, filepath)
    raise AckMessage()


async def finish(
    logger: Logger,
    parser: Parser,
    url: str,
    url_hash: str,
    content: str,
    content_hash: str,
    filepath: str,
):
    try:
        async with DI.metastore.with_transaction():
            await DI.s3.upload(filepath, content)

            metadata_id = await DI.metastore.save(
                Metadata(
                    target_id=parser.config.id,
                    target_name=parser.config.name,
                    absolute_url=normalize_url(url),
                    last_scrape=datetime.now(),
                    filepath=filepath,
                    url_hash=url_hash,
                    content_hash=content_hash,
                    content_size=len(content),
                )
            )

            await DI.process_queue_publisher.publish(
                ProcessRequest(
                    url=url,
                    target_id=parser.config.id,
                    filepath=filepath,
                    metadata=metadata_id,
                    datetime=datetime.now(),
                )
            )
    except Exception as e:
        logger.error(f"failed to finish message processing: {e}")
        raise NackMessage() from e

    try:
        next_urls = parser.extract_hrefs(content, logger)
        urls = [normalize_url(absolute_url(extract_domain(url), next_url)) for next_url in next_urls]
        await asyncio.gather(*[DI.fetch_queue_publisher.publish(FetchRequest(url=next_url)) for next_url in urls])
    except Exception as e:
        logger.warning(f"failed to spawn new fetch requests: {e}")
        raise NackMessage() from e
