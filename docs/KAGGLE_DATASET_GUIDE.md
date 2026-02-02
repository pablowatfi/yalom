# Loading Kaggle Dataset: Huberman Lab Transcripts

## Overview

The Kaggle dataset has **197 episodes** with multiple formats including timestamped transcripts!

**Dataset**: [tkrsh09/huberman-lab-podcast-transcripts-from-youtube](https://www.kaggle.com/datasets/tkrsh09/huberman-lab-podcast-transcripts-from-youtube)

## What's in the Dataset

```
HubermanLabTranscripts/
├── TimestampedTranscriptions/
│   ├── csv/          # Timestamped transcripts in CSV format
│   ├── json/         # Timestamped transcripts in JSON format
│   └── srt/          # Subtitle format with timestamps
├── text/             # 197 plain text transcripts (no timestamps)
├── consolidated.txt  # All transcripts in one file (24.53 MB)
└── videoID.json      # Maps video IDs to titles (19.64 kB)
```

## Download Instructions

### 1. Create Free Kaggle Account

Go to [kaggle.com](https://www.kaggle.com/) and sign up

### 2. Download Dataset

**Option A: Web Download**
```bash
# Visit the dataset page and click "Download"
https://www.kaggle.com/datasets/tkrsh09/huberman-lab-podcast-transcripts-from-youtube
```

**Option B: Kaggle API (Recommended)**
```bash
# Install Kaggle CLI
pip install kaggle

# Setup API credentials
# 1. Go to kaggle.com/settings
# 2. Click "Create New API Token"
# 3. Save kaggle.json to ~/.kaggle/

# Download dataset
kaggle datasets download -d tkrsh09/huberman-lab-podcast-transcripts-from-youtube

# Unzip
unzip huberman-lab-podcast-transcripts-from-youtube.zip
```

### 3. Load into Your Database

Once downloaded, you can adapt our GitHub loader to load from local files:

```python
from src.database import db, get_db_session
from src.models import VideoTranscript
import json
import os
from datetime import datetime

# Initialize database
db.connect()
session = get_db_session()

# Load videoID.json for metadata
with open('HubermanLabTranscripts/videoID.json') as f:
    video_metadata = json.load(f)

# Load transcripts from text folder
text_dir = 'HubermanLabTranscripts/text'
for filename in os.listdir(text_dir):
    if filename.endswith('.txt'):
        video_id = filename.replace('.txt', '')

        # Get title from metadata
        title = video_metadata.get(video_id, f'Episode {video_id}')

        # Read transcript
        with open(os.path.join(text_dir, filename)) as f:
            transcript_text = f.read()

        # Check if already exists
        existing = session.query(VideoTranscript).filter_by(
            video_id=video_id
        ).first()

        if existing:
            continue

        # Save to database
        record = VideoTranscript(
            video_id=video_id,
            title=title,
            channel_name="Huberman Lab",
            transcript_text=transcript_text,
            transcript_language='en',
            has_transcript=True,
            scraped_at=datetime.utcnow()
        )

        session.add(record)
        session.commit()
        print(f"Loaded: {title[:60]}...")

session.close()
```

## Advanced: Using Timestamped Transcripts

The dataset includes **timestamped** transcripts in multiple formats:

### JSON Format Example
```json
{
  "video_id": "nm1TxQj9IsQ",
  "segments": [
    {
      "start": 0.0,
      "duration": 5.0,
      "text": "Welcome to the Huberman Lab Podcast"
    }
  ]
}
```

### Benefits of Timestamped Data
- Precise citation to specific moments in videos
- Better chunking for RAG (chunk by time segments)
- Link directly to YouTube timestamps
- Create clips or highlight reels

## Comparison: GitHub vs Kaggle

| Feature | GitHub (prakhar625) | Kaggle (tkrsh09) |
|---------|---------------------|------------------|
| Episodes | 134 | 197 |
| Format | Plain text | Text + Timestamped (CSV/JSON/SRT) |
| Last Updated | Mar 2023 | ~2 years ago (but more episodes) |
| Access | Direct URL | Download required |
| Size | ~150-200KB per file | 196.89 MB total |
| Timestamps | ❌ No | ✅ Yes |
| Easy Integration | ✅ Already coded | ⚠️ Needs adaptation |

## Recommendation

1. **For Quick Start**: Use GitHub loader (already implemented)
2. **For More Episodes**: Download Kaggle dataset and adapt loader
3. **For Timestamps**: Definitely use Kaggle dataset

## Next Steps

Would you like me to create a Kaggle loader that:
1. Loads from downloaded Kaggle files
2. Preserves timestamp information
3. Stores timestamps in a new database table for precise citation?

Let me know if you want to implement this!
