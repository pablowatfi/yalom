# TapeSearch Integration

This project includes integration with [TapeSearch](https://www.tapesearch.com/) API for fetching podcast transcripts. TapeSearch provides access to over 4 million podcast transcripts from thousands of podcasts.

## Features

- Search and scrape entire podcasts by name
- Fetch individual episode transcripts
- Store transcripts in PostgreSQL database
- Automatic duplicate prevention
- Rate limiting and retry logic

## Setup

### 1. Get TapeSearch API Key

1. Sign up for TapeSearch API access at [https://www.tapesearch.com/api/access](https://www.tapesearch.com/api/access)
2. Pricing: $60/month (or $720/year) for API access
   - Includes 2000 requests per day
   - Access to all podcast transcripts in database
3. Create an API key at [https://www.tapesearch.com/api/keys](https://www.tapesearch.com/api/keys)

### 2. Configure API Key

Set your API key as an environment variable:

```bash
export TAPESEARCH_API_KEY='your_api_key_here'
```

Or add it to your `.env` file:

```bash
TAPESEARCH_API_KEY=your_api_key_here
```

### 3. Initialize Database

The TapeSearch integration uses a separate table (`podcast_transcripts`):

```bash
poetry run python cli.py init-db
```

## Usage

### Scrape a Podcast

Search for and scrape all episodes from a podcast:

```bash
poetry run python cli.py tapesearch-scrape "Huberman Lab"
```

**Options:**

- `--max-episodes N`: Limit to first N episodes
- `--delay SECONDS`: Delay between episode fetches (default: 1.0)
- `--reprocess`: Re-scrape episodes already in database

**Examples:**

```bash
# Scrape first 10 episodes from Huberman Lab
poetry run python cli.py tapesearch-scrape "Huberman Lab" --max-episodes 10

# Scrape with 2 second delay between episodes
poetry run python cli.py tapesearch-scrape "Huberman Lab" --delay 2.0

# Re-scrape all episodes (including existing ones)
poetry run python cli.py tapesearch-scrape "Huberman Lab" --reprocess
```

## Database Schema

TapeSearch transcripts are stored in the `podcast_transcripts` table:

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| episode_uid | String(100) | TapeSearch episode UID (unique, indexed) |
| episode_title | String(500) | Episode title |
| podcast_uid | String(100) | TapeSearch podcast UID (indexed) |
| podcast_title | String(500) | Podcast name |
| published_date | String(50) | Publication date |
| duration | Integer | Episode duration in seconds |
| transcript_text | Text | Full transcript |
| has_transcript | Boolean | Whether transcript was successfully fetched |
| error_message | Text | Error message if fetch failed |
| scraped_at | DateTime | When transcript was scraped |

## API Limits

- **Rate Limit**: 2000 requests per day
- **Pricing**: $60/month or $720/year
- **Database Size**: 4+ million episodes from 5000+ podcasts

## Comparison: YouTube vs TapeSearch

| Feature | YouTube (yt-dlp) | TapeSearch API |
|---------|------------------|----------------|
| Cost | Free | $60/month |
| Rate Limits | Very aggressive (429 errors) | 2000 requests/day |
| Reliability | Low (frequent blocks) | High (official API) |
| Content Type | YouTube videos | Podcasts only |
| Transcript Quality | Varies | High quality |

## Code Structure

- `src/tapesearch_fetcher.py`: TapeSearch API client
- `src/tapesearch_scraper.py`: Podcast scraping logic
- `src/models_tapesearch.py`: Database model for podcast transcripts
- All YouTube code remains unchanged in `src/transcript_fetcher.py` and `src/scraper.py`

## Example: Python API Usage

You can also use the TapeSearch client directly in Python:

```python
from src.tapesearch_fetcher import TapeSearchClient
from src.database import db, get_db_session
from src.tapesearch_scraper import TapeSearchScraper

# Initialize
db.connect()
session = get_db_session()

# Search for podcasts
client = TapeSearchClient(api_key='your_key')
podcasts = client.search_podcast("Huberman Lab")
print(f"Found {len(podcasts)} podcasts")

# Scrape a podcast
scraper = TapeSearchScraper(session, api_key='your_key')
stats = scraper.search_and_scrape_podcast("Huberman Lab", max_episodes=5)
print(f"Scraped {stats['success']} episodes")
```

## Troubleshooting

### "TAPESEARCH_API_KEY environment variable not set"

Make sure you've exported the API key:

```bash
export TAPESEARCH_API_KEY='your_key_here'
```

### "429 Too Many Requests"

You've exceeded the 2000 requests/day limit. Wait until the next day or contact TapeSearch for a higher limit.

### "No podcast found matching"

Try variations of the podcast name:
- "Huberman Lab"
- "The Huberman Lab Podcast"
- "Andrew Huberman"

## Next Steps

- Query transcripts from database
- Implement vector embeddings for semantic search
- Add chunking strategies for RAG applications
- Export transcripts to different formats
