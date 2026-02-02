# Quick Start: Getting Huberman Lab Transcripts with TapeSearch

## Why TapeSearch?

YouTube has **extremely aggressive rate limiting** that blocks your IP after just a few requests (as you experienced). TapeSearch is a paid API service ($60/month) that provides reliable access to podcast transcripts without rate limits (2000 requests/day).

## Steps to Get Started

### 1. Sign Up for TapeSearch

1. Go to https://www.tapesearch.com/api/access
2. Sign up for API access ($60/month or $720/year)
3. Create an API key at https://www.tapesearch.com/api/keys

### 2. Set Your API Key

```bash
export TAPESEARCH_API_KEY='your_api_key_here'
```

### 3. Initialize Database

```bash
poetry run python cli.py init-db
```

### 4. Scrape Huberman Lab Podcast

```bash
# Test with first 5 episodes
poetry run python cli.py tapesearch-scrape "Huberman Lab" --max-episodes 5

# Scrape all episodes (this will take a while!)
poetry run python cli.py tapesearch-scrape "Huberman Lab"
```

## What You Get

- **Reliable access**: No 429 rate limit errors
- **High quality transcripts**: Professional podcast transcripts
- **Fast scraping**: 1 second delay between episodes (vs 15+ seconds with YouTube)
- **Large collection**: Huberman Lab has hundreds of episodes available

## Verify Your Data

Check how many transcripts you've scraped:

```bash
poetry run python -c "from src.database import db; from src.models_tapesearch import PodcastTranscript; db.connect(); session = db.get_session(); successful = session.query(PodcastTranscript).filter(PodcastTranscript.has_transcript == True).count(); total = session.query(PodcastTranscript).count(); print(f'Successfully scraped: {successful}/{total} episodes'); session.close()"
```

## Cost Analysis

- **TapeSearch**: $60/month = $2/day for reliable access to 2000 episodes/day
- **YouTube**: Free but effectively unusable due to rate limiting
- **Recommendation**: Use TapeSearch for production, YouTube only for small-scale testing

## Alternative: Wait for YouTube Rate Limit Reset

If you don't want to pay for TapeSearch, you can:
1. Wait 6-12 hours for YouTube's rate limit to reset
2. Scrape 10-20 videos at a time
3. Spread scraping over multiple days
4. Use a VPN to change your IP address

However, this is **not reliable for production use**.

## Your Current Status

- ✓ YouTube: 16 successful transcripts before hitting rate limit
- ✓ Database: Ready for TapeSearch data (separate table)
- ⏳ Waiting: Either get TapeSearch API key or wait for YouTube rate limit reset
