from faststream import ContextRepo, FastStream, Logger
from faststream.nats import NatsBroker, NatsMessage, PullSub

from debias_spider.config import Config
from debias_spider.models import FetchRequest

broker = NatsBroker(pedantic=True)
app = FastStream(broker)


@app.on_startup
async def app_on_startup(context: ContextRepo):
    """Lifespan hook that is called when application is starting
    before it starts accepting any request or declaring queues
    """
    # calling __init__ function of Config class will load all configuration
    # however, type checkers do not like it
    config = Config()  # type: ignore

    context.set_global("config", config)
    await broker.connect(config.nats.dsn.encoded_string())


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
    logger.info(f"received message {msg} ({data})")
    await msg.ack()
