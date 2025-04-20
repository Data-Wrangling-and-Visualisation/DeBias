import asyncio
import hashlib
import logging
import os
import random
import string
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg
import psycopg.sql

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Keyword:
    text: str
    type: str


@dataclass
class Topic:
    text: str
    type: str


@dataclass
class ProcessingResult:
    absolute_url: str
    url_hash: str
    target_id: str
    scrape_datetime: datetime
    article_datetime: datetime
    snippet: str
    title: str
    keywords: list[Keyword]
    topics: list[Topic]


@dataclass
class Target:
    id: str
    main_page: str
    country: str
    alignment: str


class Wordstore:
    def __init__(self, connection: str):
        self._conn_str = connection
        self._connection: psycopg.AsyncConnection | None = None

    async def _get_connection(self) -> psycopg.AsyncConnection:
        if self._connection is None or self._connection.closed:
            self._connection = await psycopg.AsyncConnection.connect(self._conn_str)
        logger.debug(f"connected to {self._connection.info}")
        return self._connection

    async def init(self):
        logger.info("initializing wordstore")

        conn = await self._get_connection()
        async with conn.cursor() as cursor:
            logger.info("creating table targets")
            await cursor.execute("""
                create table if not exists public.targets (
                    id text not null primary key,
                    name text not null,
                    main_page text not null,
                    country text not null,
                    alignment text not null
                );
            """)
            logger.info("inserting into table targets")
            await cursor.execute("""
                insert into public.targets (id, name, main_page, country, alignment) values
                    ('SKY','Sky News','https://news.sky.com/','UK','Lean Left'),
                    ('GBN','GBN','https://www.gbnews.com/','UK','Lean Right'),
                    ('ABC','ABC News','http://abcnews.go.com/','USA','Lean Left'),
                    ('DMU','Daily Mail','https://www.dailymail.co.uk/home/index.html','UK','Right'),
                    ('TIM','The Times','https://www.thetimes.com/','UK','Center'),
                    ('MIR','The Mirror','https://www.mirror.co.uk/','UK','Left'),
                    ('MET','Metro','https://metro.co.uk/','UK','Lean Left'),
                    ('STD','The Standard','https://www.standard.co.uk/','UK','Center'),
                    ('WAL','Wales Online','https://www.walesonline.co.uk/','UK','Lean Left'),
                    ('SUN','The Sun','https://www.thesun.co.uk/','UK','Center'),
                    ('GRD','The Guardian','https://www.theguardian.com/uk-news','UK','Left'),
                    ('BBC','BBC News','http://www.bbc.com/','UK','Center'),
                    ('BLB','Bloomberg','http://www.bloomberg.com/','USA','Lean Left'),
                    ('BUS','Business Insider','https://www.insider.com/','USA','Lean Left'),
                    ('BFN','BuzzFeed News','https://www.buzzfeednews.com','USA','Left'),
                    ('CBS','CBS News','https://www.cbsnews.com','USA','Lean Left'),
                    ('CNN','CNN Digital','https://cnn.com','USA','Lean Left'),
                    ('FRB','Forbes','https://www.forbes.com','USA','Center'),
                    ('FND','Fox News Digital','http://www.foxnews.com/','USA','Right'),
                    ('NRN','National Review','https://www.nationalreview.com/news/','USA','Lean Right'),
                    ('NBC','NBC News Digital','https://www.nbcnews.com','USA','Lean Left'),
                    ('NYP','New York Post (News)','https://nypost.com','USA','Lean Right'),
                    ('NYT','New York Times (News)','https://www.nytimes.com','USA','Lean Left'),
                    ('NNN','NewsNation','https://www.newsnationnow.com','USA','Center'),
                    ('SPC','The American Spectator','https://spectator.org','USA','Right'),
                    ('ATL','The Atlantic','https://www.theatlantic.com/world/','USA','Left'),
                    ('DWN','The Daily Wire','https://www.dailywire.com','USA','Right'),
                    ('ECO','The Economist','https://www.economist.com','USA','Lean Left'),
                    ('FED','The Federalist','https://thefederalist.com','USA','Right'),
                    ('NYK','The New Yorker','https://www.newyorker.com','USA','Left'),
                    ('TIM','Time Magazine','https://time.com','USA','Lean Left'),
                    ('UTN','USA TODAY','https://www.usatoday.com','USA','Lean Left'),
                    ('VOX','Vox','https://www.vox.com','USA','Left'),
                    ('WSJ','Wall Street Journal (News)','https://www.wsj.com','USA','Center'),
                    ('WEN','Washington Examiner','https://washingtonexaminer.com','USA','Lean Right'),
                    ('WFB','Washington Free Beacon','https://freebeacon.com','USA','Right'),
                    ('WPN','Washington Post','https://www.washingtonpost.com','USA','Lean Left'),
                    ('WTN','Washington Times','https://www.washingtontimes.com','USA','Lean Right')
                on conflict (id) do nothing;
            """)
            logger.info("creating table documents")
            await cursor.execute("""
                create table if not exists public.documents (
                    id serial primary key,
                    title text not null,
                    absolute_url text not null,
                    url_hash text not null,
                    target_id text not null references targets(id),
                    scrape_datetime timestamp not null,
                    article_datetime timestamp,
                    snippet text not null
                );               
            """)
            logger.info("creating table keywords")
            await cursor.execute("""
                create table if not exists public.keywords (
                    id serial primary key,
                    type text not null,
                    keyword text not null,
                    count int not null
                );
            """)
            await cursor.execute("""
                create unique index if not exists keywords_type_keyword
                    on keywords(type, keyword);
            """)
            logger.info("creating table topics")
            await cursor.execute("""
                create table if not exists public.topics (
                    id serial primary key,
                    type text not null,
                    topic text not null,
                    count int not null
                );
            """)
            await cursor.execute(
                """
                create unique index if not exists topics_type_topic
                    on topics(type, topic);
            """
            )
            logger.info("creating table keyword_appearances")
            await cursor.execute("""
                create table if not exists public.keyword_appearances (
                    keyword_id int references keywords(id),
                    document_id int references documents(id),
                    count int,
                    primary key (keyword_id, document_id)
                );
            """)
            logger.info("creating table topic_appearances")
            await cursor.execute("""
                create table if not exists public.topic_appearances (
                    topic_id int references topics(id),
                    document_id int references documents(id),
                    count int,
                    primary key (topic_id, document_id)
                );
            """)
        await conn.commit()

    @asynccontextmanager
    async def with_transaction(self):
        async with (await self._get_connection()).transaction() as t:
            try:
                yield t
            except Exception as e:
                logger.error(f"transaction failed: {e}")
                raise e from e
            else:
                logger.debug("committing transaction")

    async def save(self, result: ProcessingResult):
        conn = await self._get_connection()
        async with self.with_transaction():
            async with conn.cursor() as c:
                insert_document = psycopg.sql.SQL("""
                    insert into public.documents (
                        title, absolute_url, url_hash, target_id, scrape_datetime, article_datetime, snippet
                    ) values (%s, %s, %s, %s, %s, %s, %s) returning id;
                """)
                r = await (
                    await c.execute(
                        insert_document,
                        (
                            result.title,
                            result.absolute_url,
                            result.url_hash,
                            result.target_id,
                            result.scrape_datetime,
                            result.article_datetime,
                            result.snippet,
                        ),
                    )
                ).fetchone()
                if r is None:
                    raise ValueError(f"failed to insert document <{result.absolute_url}>")
                document_id = r[0]

                # create new keywords if not exists, update count if exists
                insert_keywords = psycopg.sql.SQL("""
                    insert into public.keywords (type, keyword, count) values (%s, %s, 1)
                    on conflict (type, keyword) do update set count = keywords.count + 1
                    returning id;
                """)
                keyword_ids = []
                for keyword_id in result.keywords:
                    r = await (await c.execute(insert_keywords, (keyword_id.type, keyword_id.text))).fetchone()
                    if r is None:
                        raise ValueError(f"failed to insert keyword <{keyword_id.text}>")
                    keyword_ids.append(r[0])

                # create new topics if not exists, update count if exists
                insert_topics = psycopg.sql.SQL("""
                    insert into public.topics (type, topic, count) values (%s, %s, 1)
                    on conflict (type, topic) do update set count = topics.count + 1
                    returning id;
                """)
                topic_ids = []
                for topic in result.topics:
                    r = await (await c.execute(insert_topics, (topic.type, topic.text))).fetchone()
                    if r is None:
                        raise ValueError(f"failed to insert topic <{topic.text}>")
                    topic_ids.append(r[0])

                insert_keyword_appearances = psycopg.sql.SQL("""
                    insert into public.keyword_appearances (keyword_id, document_id, count)
                    values (%s, %s, 1)
                    on conflict (keyword_id, document_id) do update set count = keyword_appearances.count + 1;
                """)
                for keyword_id in keyword_ids:
                    await c.execute(insert_keyword_appearances, (keyword_id, document_id))

                insert_topic_appearances = psycopg.sql.SQL("""
                    insert into public.topic_appearances (topic_id, document_id, count)
                    values (%s, %s, 1)
                    on conflict (topic_id, document_id) do update set count = topic_appearances.count + 1;
                """)
                for topic_id in topic_ids:
                    await c.execute(insert_topic_appearances, (topic_id, document_id))


# Sample data for generation
TARGET_IDS = [
    "SKY",
    "GBN",
    "ABC",
    "DMU",
    "TIM",
    "MIR",
    "MET",
    "STD",
    "WAL",
    "SUN",
    "GRD",
    "BBC",
    "BLB",
    "BUS",
    "BFN",
    "CBS",
    "CNN",
    "FRB",
    "FND",
    "NRN",
]

KEYWORD_TYPES = ["entity", "person", "organization", "location", "event", "concept", "product"]

TOPIC_TYPES = ["main", "secondary", "tertiary", "related"]

# Sample keywords by category
KEYWORDS = {
    "person": [
        "Joe Biden",
        "Donald Trump",
        "Rishi Sunak",
        "Keir Starmer",
        "Emmanuel Macron",
        "Vladimir Putin",
        "Volodymyr Zelensky",
        "Kamala Harris",
        "Elon Musk",
        "Taylor Swift",
    ],
    "organization": [
        "NATO",
        "United Nations",
        "European Union",
        "Amazon",
        "Google",
        "Microsoft",
        "Apple",
        "Facebook",
        "Twitter",
        "Tesla",
        "Labour Party",
        "Conservative Party",
    ],
    "location": [
        "United States",
        "United Kingdom",
        "Russia",
        "Ukraine",
        "China",
        "Israel",
        "Palestine",
        "France",
        "Germany",
        "Canada",
        "India",
        "London",
        "Washington DC",
    ],
    "event": [
        "Election",
        "Olympic Games",
        "Climate Summit",
        "Pandemic",
        "Conference",
        "War",
        "Festival",
        "Protest",
        "Demonstration",
        "Scandal",
    ],
    "concept": [
        "Democracy",
        "Climate Change",
        "Inflation",
        "Recession",
        "Freedom of Speech",
        "Privacy",
        "Healthcare",
        "Education",
        "Immigration",
        "Social Media",
    ],
    "product": [
        "iPhone",
        "Tesla Model S",
        "COVID Vaccine",
        "PlayStation 5",
        "Xbox",
        "Artificial Intelligence",
        "ChatGPT",
        "Windows 11",
        "Netflix",
        "Amazon Prime",
    ],
    "entity": [
        "Parliament",
        "Congress",
        "Supreme Court",
        "White House",
        "Downing Street",
        "Pentagon",
        "NHS",
        "BBC",
        "FBI",
        "CIA",
        "MI6",
        "Kremlin",
    ],
}

# Sample topics
TOPICS = [
    "Politics",
    "Economics",
    "Technology",
    "Science",
    "Health",
    "Environment",
    "Sport",
    "Entertainment",
    "International Relations",
    "War",
    "Crime",
    "Education",
    "Social Issues",
    "Business",
    "Energy",
    "Transportation",
    "Housing",
    "Agriculture",
    "Finance",
    "Arts",
    "Media",
    "Religion",
    "Weather",
    "Labor",
    "Development",
]

# Sample domains for URLs
DOMAINS = {
    "SKY": "news.sky.com",
    "GBN": "gbnews.com",
    "ABC": "abcnews.go.com",
    "DMU": "dailymail.co.uk",
    "TIM": "thetimes.com",
    "MIR": "mirror.co.uk",
    "MET": "metro.co.uk",
    "STD": "standard.co.uk",
    "WAL": "walesonline.co.uk",
    "SUN": "thesun.co.uk",
    "GRD": "theguardian.com",
    "BBC": "bbc.com",
    "BLB": "bloomberg.com",
    "BUS": "insider.com",
    "BFN": "buzzfeednews.com",
    "CBS": "cbsnews.com",
    "CNN": "cnn.com",
    "FRB": "forbes.com",
    "FND": "foxnews.com",
    "NRN": "nationalreview.com",
}

# Title templates
TITLE_TEMPLATES = [
    "{person} announces new {concept} initiative",
    "{organization} faces criticism over {concept} policies",
    "New report shows {concept} crisis in {location}",
    "{person} speaks out on {event} controversy",
    "{location} prepares for upcoming {event}",
    "Breaking: {event} in {location} causes widespread concern",
    "{organization} launches new {product} amid {concept} debate",
    "Analysis: How {concept} is changing {location}",
    "{person} to lead {organization} following {event}",
    "Report: {location}'s approach to {concept} draws international attention",
    "{person} criticizes {organization} over {concept} stance",
    "Special report: {event} reshapes {concept} in {location}",
    "Opinion: Why {concept} matters more than ever",
    "{organization} announces partnership with {person} on {concept}",
    "Investigation reveals {concept} problems within {organization}",
    "{location} residents protest against {concept} regulations",
    "{person} denies involvement in {event} scandal",
    "Studies show {concept} improving in {location} despite {event}",
    "{organization} CEO discusses {product} development",
    "New poll: {concept} becomes top concern in {location}",
]

# Snippet templates
SNIPPET_TEMPLATES = [
    "In a significant development today, {title_lowercase}. This marks a turning point for {keyword1} as it grapples with {topic1}.",
    "Sources confirmed yesterday that {title_lowercase}. Experts from {keyword2} are calling this a watershed moment for {topic1}.",
    "According to recent reports, {title_lowercase}. This development comes amidst growing concerns about {topic1} across {keyword3}.",
    "Breaking news: {title_lowercase}. Analysts at {keyword2} suggest this could have far-reaching implications for {topic2}.",
    "In an unexpected turn of events, {title_lowercase}. This has sparked debate among {keyword4} about the future of {topic1}.",
    "Officials announced today that {title_lowercase}. Representatives from {keyword1} declined to comment on how this might affect {topic2}.",
    "New data reveals that {title_lowercase}. This contradicts previous statements from {keyword2} regarding {topic1} strategies.",
    "In an exclusive interview, {keyword1} confirmed that {title_lowercase}. This development aligns with ongoing {topic2} initiatives.",
    "A spokesperson for {keyword2} stated that {title_lowercase}. This announcement follows months of speculation about {topic1} reforms.",
    "Leaked documents suggest that {title_lowercase}. Insiders at {keyword3} express concern over potential impacts on {topic1}.",
]


def generate_url_and_hash(target_id):
    """Generate a realistic URL and its hash for a given target ID"""
    domain = DOMAINS.get(target_id, "news.example.com")
    path_elements = []

    # Add year/month/day
    current_date = datetime.now()
    path_elements.append(str(current_date.year))
    path_elements.append(f"{current_date.month:02d}")
    path_elements.append(f"{current_date.day:02d}")

    # Add slug
    slug_words = random.randint(3, 7)
    slug = "-".join("".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8))) for _ in range(slug_words))
    path_elements.append(slug)

    # Create URL
    url = f"https://{domain}/{'/'.join(path_elements)}"

    # Create hash
    url_hash = hashlib.md5(url.encode()).hexdigest()

    return url, url_hash


def generate_title(keywords):
    """Generate a realistic article title using keywords"""
    template = random.choice(TITLE_TEMPLATES)

    # Find required placeholders in the template
    placeholders = []
    parts = template.split("{")
    for part in parts[1:]:  # Skip the first part which doesn't have a placeholder
        if "}" in part:
            placeholder = part.split("}")[0]
            placeholders.append(placeholder)

    # Create a mapping of placeholders to keywords
    mapping = {}
    for placeholder in placeholders:
        keyword_candidates = [k for k in keywords if k.type.lower() == placeholder]
        if keyword_candidates:
            mapping[placeholder] = random.choice(keyword_candidates).text
        else:
            # Fallback if no matching keyword type
            if placeholder in KEYWORDS:
                mapping[placeholder] = random.choice(KEYWORDS[placeholder])
            else:
                mapping[placeholder] = random.choice(KEYWORDS[random.choice(list(KEYWORDS.keys()))])

    # Fill template
    for placeholder, value in mapping.items():
        template = template.replace(f"{{{placeholder}}}", value)

    return template


def generate_snippet(title, keywords, topics):
    """Generate a realistic snippet based on title, keywords, and topics"""
    template = random.choice(SNIPPET_TEMPLATES)

    # Replace placeholders
    replacements = {
        "title_lowercase": title[0].lower() + title[1:],
        "keyword1": keywords[0].text if keywords else "experts",
        "keyword2": keywords[1].text if len(keywords) > 1 else "analysts",
        "keyword3": keywords[2].text if len(keywords) > 2 else "observers",
        "keyword4": keywords[3].text if len(keywords) > 3 else "commentators",
        "topic1": topics[0].text if topics else "the situation",
        "topic2": topics[1].text if len(topics) > 1 else "recent developments",
    }

    for placeholder, value in replacements.items():
        template = template.replace(f"{{{placeholder}}}", value)

    return template


def generate_random_data(num_documents=100):
    """Generate random data for the Wordstore database"""
    results = []

    # Generate dates - at least 10 distinct dates
    base_date = datetime.now() - timedelta(days=30)
    dates = [base_date + timedelta(days=i) for i in range(15)]

    for _ in range(num_documents):
        # Select target
        target_id = random.choice(TARGET_IDS)

        # Generate URL and hash
        url, url_hash = generate_url_and_hash(target_id)

        # Generate dates
        article_date = random.choice(dates)
        scrape_date = article_date + timedelta(hours=random.randint(1, 24))

        # Generate keywords
        keywords = []
        used_keywords = set()
        for _ in range(10):
            keyword_type = random.choice(KEYWORD_TYPES)
            keyword_text = random.choice(KEYWORDS[keyword_type])

            # Ensure we don't use the same keyword twice
            attempts = 0
            while keyword_text in used_keywords and attempts < 10:
                keyword_text = random.choice(KEYWORDS[keyword_type])
                attempts += 1

            used_keywords.add(keyword_text)
            keywords.append(Keyword(text=keyword_text, type=keyword_type))

        # Generate topics
        topics = []
        used_topics = set()
        for _ in range(2):
            topic_type = random.choice(TOPIC_TYPES)
            topic_text = random.choice(TOPICS)

            # Ensure we don't use the same topic twice
            attempts = 0
            while topic_text in used_topics and attempts < 10:
                topic_text = random.choice(TOPICS)
                attempts += 1

            used_topics.add(topic_text)
            topics.append(Topic(text=topic_text, type=topic_type))

        # Generate title
        title = generate_title(keywords)

        # Generate snippet
        snippet = generate_snippet(title, keywords, topics)

        # Create ProcessingResult
        result = ProcessingResult(
            absolute_url=url,
            url_hash=url_hash,
            target_id=target_id,
            scrape_datetime=scrape_date,
            article_datetime=article_date,
            snippet=snippet,
            title=title,
            keywords=keywords,
            topics=topics,
        )

        results.append(result)

    return results


def print_sample_data(data):
    """Print a sample of the generated data for verification"""
    for i, result in enumerate(data[:5], 1):
        print(f"\n--- Document {i} ---")
        print(f"Title: {result.title}")
        print(f"URL: {result.absolute_url}")
        print(f"Target ID: {result.target_id}")
        print(f"Article Date: {result.article_datetime}")
        print(f"Snippet: {result.snippet[:100]}...")
        print(f"Keywords: {', '.join(k.text for k in result.keywords[:5])}...")
        print(f"Topics: {', '.join(t.text for t in result.topics)}")


async def main():
    conn_str = os.environ["POSTGRES_CONNECTION"]
    logger.info(f"Connecting to database using connection string: {conn_str}")

    # Initialize the database
    wordstore = Wordstore(conn_str)
    logger.info("Initializing database schema...")
    await wordstore.init()

    # Generate data
    logger.info("Generating random data...")
    num_documents = 120  # Generate 120 documents (more than the required 100)
    data = generate_random_data(num_documents)

    logger.info(f"Generated {len(data)} documents")
    print_sample_data(data)

    # Save to database
    logger.info("Saving data to database...")
    for i, result in enumerate(data, 1):
        await wordstore.save(result)
        if i % 10 == 0:
            logger.info(f"Saved {i}/{len(data)} documents")

    logger.info(f"Successfully saved {len(data)} documents to the database")


if __name__ == "__main__":
    asyncio.run(main())
