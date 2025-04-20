from core.wordstore import Wordstore
from faststream import ContextRepo, FastStream, Logger
from faststream.exceptions import AckMessage, RejectMessage
from faststream.nats import NatsBroker, NatsMessage, PullSub
from processor.processor import WebpageData, process_webpage

from debias.core.metastore import Metadata, Metastore
from debias.core.models import ProcessRequest
from debias.core.s3 import S3Client
from debias.processor.config import Config
from debias.processor.nlp.classifier import ZeroShotClassifier
from debias.processor.nlp.extractor import SpacyKeywordExtractor

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
        cls.s3 = S3Client(cls.config.s3)
        cls.metastore = Metastore(cls.config.pg.connection)
        cls.wordstore = Wordstore(cls.config.pg.connection)
        cls.keyword_extractor = SpacyKeywordExtractor(cls.config.spacy_path, cls.config.spacy_model)
        cls.classifier = ZeroShotClassifier(cls.config.transformers_model)

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

    await broker.connect(DI.config.nats.dsn.encoded_string())


@app.after_startup
async def app_after_startup(context: ContextRepo, logger: Logger):
    """Lifespan hook that is called after application is started"""
    await DI.metastore.init()
    await DI.wordstore.init()

    logger.info("app started")


@app.on_shutdown
async def app_on_shutdown(context: ContextRepo):
    """Lifespan hook that is called when application is shutting down
    after it stops accepting any request or declaring queues
    """
    pass


@broker.subscriber(subject="process-queue", stream="debias", pull_sub=PullSub(batch_size=1))
async def broker_stream_subscriber(msg: NatsMessage, data: ProcessRequest, logger: Logger, context: ContextRepo):
    """Handler which process each message from the queue.
    It subscribes to subject "process-queue", so all messages published exactly to "process-queue" subject
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
    logger.info(f"received message {msg.message_id} (corrid: {msg.correlation_id}) to process {data.filepath}")

    metainfo: Metadata | None = await DI.metastore.read(data.metadata)
    if metainfo is None:
        logger.info("recevied message with invalid metadata id, rejecting it")
        raise RejectMessage()  # raise it to completely reject message

    content = await DI.s3.download(data.filepath)

    result = process_webpage(
        DI.keyword_extractor,
        DI.classifier,
        WebpageData(
            url=data.url,
            target_id=data.target_id,
            filepath=data.filepath,
            content=content,
            metadata=data.metadata,
            datetime=data.datetime,
        ),
    )
    if result is None:
        logger.info("failed to process webpage, rejecting it")
        raise RejectMessage()  # raise it to completely reject message

    await DI.wordstore.save(result)
    raise AckMessage()  # successfully completed
