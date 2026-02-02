# FREE Solution: Load Huberman Lab Transcripts from GitHub

## The Problem

- YouTube has aggressive rate limiting (you hit 429 errors)
- TapeSearch costs $60/month

## The Solution: GitHub Repository

Someone already scraped all Huberman Lab transcripts and uploaded them to GitHub! **This is completely FREE.**

## Quick Start

### Load ALL Huberman Lab Episodes

```bash
# Load all 134 episodes (takes ~2-3 minutes)
poetry run python cli.py github-load
```

### Load Specific Episodes

```bash
# Load episodes 1-10
poetry run python cli.py github-load --start 1 --end 10

# Load a single episode
poetry run python cli.py github-load --episode 50
```

### Check Your Database

```bash
poetry run python -c "from src.database import db; from src.models import VideoTranscript; db.connect(); session = db.get_session(); count = session.query(VideoTranscript).filter(VideoTranscript.has_transcript == True).count(); print(f'Total transcripts: {count}'); session.close()"
```

## What You Get

✅ **All 134 Huberman Lab episodes** (as of the repo's last update)
✅ **Completely FREE** - no API keys, no rate limits
✅ **Fast loading** - takes 2-3 minutes for all episodes
✅ **Same database structure** - works with all your existing code

## Comparison

| Method | Cost | Speed | Reliability | Episodes Available |
|--------|------|-------|-------------|-------------------|
| **GitHub** | FREE | ⚡ Fast (~2 min for all) | ✅ Perfect | 134 episodes |
| YouTube | FREE | 🐌 Very slow | ❌ Rate limited | All current |
| TapeSearch | $60/month | ⚡ Fast | ✅ Perfect | All podcasts |

## Repository Details

### Main Repo (Currently Used)
- **Repo**: [prakhar625/huberman-podcasts-transcripts](https://github.com/prakhar625/huberman-podcasts-transcripts)
- **Episodes**: 134 episodes (Dec 2020 - Mar 2023)
- **Format**: Plain text transcripts
- **Updates**: Last updated Mar 2023

### Alternative Sources

#### GitHub Alternative
- **Repo**: [lord-denning/Huberman-Lab-Podcast-Transcripts](https://github.com/lord-denning/Huberman-Lab-Podcast-Transcripts)
- **Episodes**: ~51 episodes (mostly early episodes 1-51)
- **Format**: Markdown (.md) and MS Word files
- **Last Updated**: 4 years ago (older, incomplete)

#### Kaggle Dataset
- **Dataset**: [tkrsh09/huberman-lab-podcast-transcripts-from-youtube](https://www.kaggle.com/datasets/tkrsh09/huberman-lab-podcast-transcripts-from-youtube)
- **Episodes**: 197 files (more recent, updated quarterly!)
- **Formats**: CSV, JSON, SRT (timestamped), and plain text
- **Size**: 196.89 MB
- **Features**:
  - Timestamped transcriptions (with CSV, JSON, SRT formats)
  - videoID.json maps video IDs to titles
  - consolidated.txt combines all transcripts
  - Updated quarterly (last update: 2 years ago, but more recent than GitHub)
- **Download**: Requires free Kaggle account

## Next Steps

1. **Load all transcripts**: `poetry run python cli.py github-load`
2. **Query transcripts**: Use SQL or build search tools
3. **Add embeddings**: For semantic search/RAG
4. **Chunking**: Split transcripts for better context

## Example: Load All Huberman Lab Episodes

```bash
# This will load all 134 episodes into your database
poetry run python cli.py github-load

# Skip episodes already in database (safe to re-run)
poetry run python cli.py github-load  # automatically skips existing
```

## Your Current Status

- ✅ 16 episodes from YouTube (before rate limit)
- ✅ 5 episodes from GitHub (test)
- 📦 **Ready to load 113 more episodes from GitHub!**

## Future Updates

### Getting Newer Episodes (after Mar 2023)

**Option 1: Kaggle Dataset (RECOMMENDED)**
- Download from [Kaggle](https://www.kaggle.com/datasets/tkrsh09/huberman-lab-podcast-transcripts-from-youtube)
- 197 episodes (more than GitHub's 134)
- Includes timestamped transcripts
- Updated quarterly
- Can adapt the GitHub loader to parse Kaggle's format

**Option 2: YouTube Scraper**
- Use during off-peak hours (10-20 episodes at a time)
- Wait 6-12 hours between batches for rate limits to reset
- Works for most recent episodes not in datasets

**Option 3: TapeSearch API**
- $60/month for production use
- Reliable, no rate limits
- 2000 requests/day

**For now, GitHub + Kaggle datasets give you 197+ episodes for FREE!** 🎉
