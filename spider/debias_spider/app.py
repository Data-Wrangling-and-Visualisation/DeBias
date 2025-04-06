from collections import defaultdict
from datetime import datetime

import httpx
import redis.asyncio as aioredis
from faststream import ContextRepo, FastStream, Logger
from faststream.exceptions import AckMessage, NackMessage, RejectMessage
from faststream.nats import NatsBroker, NatsMessage, PullSub

from debias_spider.config import Config
from debias_spider.metastore import Metadata, Metastore
from debias_spider.models import FetchRequest, ProcessRequest, RenderRequest
from debias_spider.parser import Parser
from debias_spider.s3 import S3Client
from debias_spider.utils import extract_domain, hashsum, normalize_url

# calling __init__ function of Config class will load all configuration
# however, type checkers do not like it
config = Config()  # type: ignore

broker = NatsBroker(pedantic=True)
app = FastStream(broker)

fetch_queue_publisher = broker.publisher(subject="fetch-queue", stream="debias")
render_queue_publisher = broker.publisher(subject="render-queue", stream="debias")
process_queue_publisher = broker.publisher(subject="process-queue", stream="debias")
metadata_queue_publisher = broker.publisher(subject="metadata-queue", stream="debias")
keyvalue = aioredis.Redis.from_url(config.keyvalue.dsn)
http = httpx.AsyncClient(headers={"User-Agent": config.http.user_agent})
s3 = S3Client(config.s3)
metastore = Metastore(config.pg.connection)
parsers: dict[str, Parser | None] = defaultdict(lambda: None)


@app.on_startup
async def app_on_startup(context: ContextRepo):
    """Lifespan hook that is called when application is starting
    before it starts accepting any request or declaring queues
    """
    context.set_global("config", config)
    await http.__aenter__()

    await metastore.init()

    for target_config in config.app.targets:
        parser = Parser(target_config)
        parsers[parser.domain] = parser

    await broker.connect(config.nats.dsn.encoded_string())


@app.on_shutdown
async def app_on_shutdown(context: ContextRepo):
    """Lifespan hook that is called when application is shutting down
    after it stops accepting any request or declaring queues
    """
    await http.__aexit__(None, None, None)


@broker.subscriber(subject="fetch-queue", stream="debias", pull_sub=PullSub(batch_size=1))
async def broker_stream_subscriber(msg: NatsMessage, data: FetchRequest, logger: Logger, context: ContextRepo):
    """Handler which process each message from the queue.
    It subscribes to subject "fetch-queue", so all messages published exactly to "fetch-queue" subject
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

    parser = parsers[extract_domain(url)]
    if parser is None:
        logger.warning(f"skipping url {url}: no parser registered")
        raise RejectMessage()  # refuse to process
    logger.debug(f"found registered parser for url {url}")

    logger.debug(f"checking if url {url} was scraped in last 12 hours")
    url_hash = hashsum(url)
    if (await keyvalue.get(f"url_hash:{url_hash}")) is not None:
        logger.warning(f"skiping url {url}: url_hash {url_hash} is present")
        raise RejectMessage()  # refuse to process
    logger.debug(f"url hash {url_hash} is not present, processing url")
    await keyvalue.set(f"url_hash:{url_hash}", "1", ex=60 * 60 * 12)  # expires in 12 hours

    logger.debug(f"retrieving url {url}")
    response = await http.get(url)
    if response.status_code // 100 != 2:  # not 2XX code
        logger.warning(f"failed to retrieve {url}: status code {response.status_code}")
        raise NackMessage()  # failed, retry later
    logger.debug(f"retrieved url {url}")

    logger.debug(f"checking content hash for url {url}")
    content = response.text
    content_hash = hashsum(content)
    if (await keyvalue.get(f"content_hash:{url_hash}")) == content_hash:
        logger.warning(f"skiping url {url}: content_hash {content_hash} has not changed")
        raise AckMessage()  # ok, no retry needed
    await keyvalue.set(f"content_hash:{url_hash}", content_hash, ex=60 * 60 * 24 * 30)  # expires in 30 days
    logger.debug(f"content hash {content_hash} is not present, processing content")

    filepath = f"{parser.config.id}/{url_hash}/{content_hash}.html"

    if parser.need_render == "never":
        await finish(logger, parser, url, url_hash, content, content_hash, filepath)
        raise AckMessage()

    if parser.need_render == "always":
        await render(logger, parser, url)
        raise AckMessage()

    if parser.need_render == "auto":
        text = parser.extract_text(content, logger)
        if len(text) < 300:
            await render(logger, parser, url)
        else:
            await finish(logger, parser, url, url_hash, content, content_hash, filepath)
        raise AckMessage()

    raise NackMessage() # didnt hit any path

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
        async with await metastore.with_transaction():
            await s3.upload(filepath, content)

            id = await metastore.save_metadata(
                Metadata(
                    target_id=parser.config.id,
                    target_name=parser.config.name,
                    absolute_url=url,
                    last_scrape=datetime.now(),
                    filepath=filepath,
                    url_hash=url_hash,
                    content_hash=content_hash,
                    content_size=len(content),
                )
            )

            await process_queue_publisher.publish(
                ProcessRequest(
                    url=url,
                    target_id=parser.config.id,
                    filepath=filepath,
                    metadata=id,
                    datetime=datetime.now(),
                )
            )
    except Exception as e:
        logger.error(f"failed to finish message processing: {e}")
        raise NackMessage() from e


async def render(logger: Logger, parser: Parser, url: str):
    try:
        await render_queue_publisher.publish(RenderRequest(url=url, target_id=parser.config.id))
    except Exception as e:
        logger.error(f"failed to finish message processing: {e}")
        raise NackMessage() from e
