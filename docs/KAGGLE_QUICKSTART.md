# Kaggle Dataset - Quick Start

## 🚀 Fastest Way to Get 197 Huberman Lab Transcripts!

### Step 1: Download the Dataset

**Option A: Manual Download (Easiest)**
1. Go to: https://www.kaggle.com/datasets/tkrsh09/huberman-lab-podcast-transcripts
2. Click the **Download** button (197 MB)
3. Extract the ZIP file (you'll get `HubermanLabTranscripts` folder)

**Option B: Using Kaggle API**
```bash
# If you have Kaggle API configured
poetry run python download_kaggle.py
```

### Step 2: Load into Database

Once you have the extracted folder, run:

```bash
poetry run python cli.py kaggle-load --path /path/to/HubermanLabTranscripts
```

**Example:**
```bash
# If you extracted to Downloads
poetry run python cli.py kaggle-load --path ~/Downloads/HubermanLabTranscripts
```

### What You Get

✅ **197 complete transcripts** (63 more than GitHub!)
✅ **Timestamped versions** in multiple formats:
   - JSON with precise timestamps
   - CSV for spreadsheet analysis
   - SRT subtitle format
✅ **No rate limits** - instant loading
✅ **Clean, formatted text** ready for analysis
✅ **Video metadata** mapping (videoID.json)

### Loading Stats

Expected results:
- **Total episodes**: 197
- **New episodes**: 63 (if you already loaded GitHub's 134)
- **Load time**: ~2-3 minutes
- **Final database**: 213 transcripts (150 current + 63 new)

### Command Options

Load all episodes (default):
```bash
poetry run python cli.py kaggle-load --path /path/to/dataset
```

Load a single video by ID:
```bash
poetry run python cli.py kaggle-load --path /path/to/dataset --video-id dQw4w9WgXcQ
```

Skip existing episodes (default behavior):
```bash
poetry run python cli.py kaggle-load --path /path/to/dataset --skip-existing
```

### After Loading

Check your database:
```bash
poetry run python -c "from src.database import db; from src.models import VideoTranscript; db.connect(); session = db.get_session(); count = session.query(VideoTranscript).filter(VideoTranscript.has_transcript == True).count(); print(f'Total transcripts: {count}'); session.close()"
```

### Next Steps

With 197+ transcripts loaded, you can:

1. **Vector Embeddings** - Add semantic search capabilities
2. **Chunking Strategies** - Test different chunking methods
3. **RAG Application** - Build Q&A system over Huberman content
4. **Timestamp Analysis** - Use timestamped data for precise citations

### Dataset Structure

```
HubermanLabTranscripts/
├── text/                        # 197 plain text transcripts
│   ├── dQw4w9WgXcQ.txt
│   ├── ...
├── TimestampedTranscriptions/   # Timestamped versions
│   ├── csv/                     # CSV format with timestamps
│   ├── json/                    # JSON with precise timing
│   └── srt/                     # Subtitle format
├── videoID.json                 # Video metadata (titles, IDs)
└── consolidated.txt             # All transcripts in one file (24.53 MB)
```

### Troubleshooting

**Dataset folder not found?**
- Make sure you've extracted the ZIP file
- Use the full absolute path
- Check the folder name (should be `HubermanLabTranscripts`)

**Permission errors?**
- Make sure PostgreSQL is running: `docker-compose up -d`
- Check database connection in `.env`

**Want to reload transcripts?**
- Remove `--skip-existing` flag to reprocess existing episodes

### Why Kaggle Dataset?

| Feature | Kaggle | GitHub | YouTube |
|---------|--------|--------|---------|
| Episodes | **197** | 134 | 16 (rate limited) |
| Timestamps | ✅ | ❌ | ✅ (if working) |
| Rate Limits | ❌ | ❌ | ✅ (strict) |
| Speed | ⚡ Fast | ⚡ Fast | 🐌 Very slow |
| Updates | Quarterly | Occasional | Real-time |
| Format | Multiple | Markdown | JSON |
| Cost | FREE | FREE | FREE |

**Verdict**: Kaggle is the best source for bulk transcript loading!
