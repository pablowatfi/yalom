#!/usr/bin/env python3
"""
Download Huberman Lab transcripts from Kaggle.

Two options:
1. Manual download via Kaggle website (easier)
2. Automated download via Kaggle API (requires setup)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import subprocess
from pathlib import Path


def check_kaggle_setup():
    """Check if Kaggle API is configured."""
    kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
    return kaggle_json.exists()


def download_with_api(output_path: str = '.'):
    """Download using Kaggle API."""
    print("📥 Downloading Huberman Lab Transcripts from Kaggle...")
    print("Dataset: tkrsh09/huberman-lab-podcast-transcripts")
    print()

    try:
        # Download dataset
        cmd = [
            'kaggle', 'datasets', 'download',
            '-d', 'tkrsh09/huberman-lab-podcast-transcripts',
            '-p', output_path,
            '--unzip'
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)

        # Find the extracted folder
        dataset_folder = Path(output_path) / "HubermanLabTranscripts"
        if not dataset_folder.exists():
            # Try alternative name
            dataset_folder = Path(output_path) / "huberman-lab-podcast-transcripts"

        if dataset_folder.exists():
            print(f"\n✅ Success! Dataset downloaded to: {dataset_folder}")
            print(f"\n📁 Contents:")
            print(f"  - text/ : 197 plain text transcripts")
            print(f"  - videoID.json : Video metadata")
            print(f"  - TimestampedTranscriptions/ : Timestamped formats (CSV/JSON/SRT)")
            print(f"  - consolidated.txt : All transcripts in one file")
            print(f"\n🚀 Now run:")
            print(f"  poetry run python cli.py kaggle-load --path {dataset_folder}")
            return str(dataset_folder)
        else:
            print(f"\n⚠️  Dataset downloaded but folder not found at {dataset_folder}")
            print("Check the contents of the output directory.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error downloading dataset: {e}")
        print(e.stderr)
        return None
    except FileNotFoundError:
        print("\n❌ Kaggle CLI not found!")
        print("Install it with: pip install kaggle")
        return None


def manual_instructions():
    """Print manual download instructions."""
    print("📋 Manual Download Instructions:")
    print()
    print("1. Go to: https://www.kaggle.com/datasets/tkrsh09/huberman-lab-podcast-transcripts")
    print()
    print("2. Click 'Download' button (197 MB)")
    print()
    print("3. Extract the ZIP file to get 'HubermanLabTranscripts' folder")
    print()
    print("4. Note the path where you extracted it")
    print()
    print("5. Load into database:")
    print("   poetry run python cli.py kaggle-load --path /path/to/HubermanLabTranscripts")
    print()


def setup_kaggle_api():
    """Print instructions for setting up Kaggle API."""
    print("🔧 Kaggle API Setup:")
    print()
    print("1. Create a Kaggle account at https://www.kaggle.com")
    print()
    print("2. Go to Account Settings → API → 'Create New API Token'")
    print()
    print("3. This downloads kaggle.json with your credentials")
    print()
    print("4. Place it at: ~/.kaggle/kaggle.json")
    print("   mkdir -p ~/.kaggle")
    print("   mv ~/Downloads/kaggle.json ~/.kaggle/")
    print("   chmod 600 ~/.kaggle/kaggle.json")
    print()
    print("5. Install Kaggle CLI:")
    print("   pip install kaggle")
    print()


def main():
    """Main function."""
    print("=" * 70)
    print("  Huberman Lab Transcripts - Kaggle Dataset Downloader")
    print("=" * 70)
    print()
    print("Dataset: 197 episodes with timestamped transcripts")
    print("Size: ~197 MB")
    print("License: Apache 2.0")
    print()

    # Check if Kaggle API is set up
    if check_kaggle_setup():
        print("✅ Kaggle API is configured!")
        print()
        choice = input("Download automatically? (y/n): ").lower().strip()

        if choice == 'y':
            output_path = input("Output directory (default: current): ").strip() or '.'
            download_with_api(output_path)
        else:
            manual_instructions()
    else:
        print("⚠️  Kaggle API not configured")
        print()
        print("Choose an option:")
        print("  1. Download manually (easiest)")
        print("  2. Set up Kaggle API for automated downloads")
        print()
        choice = input("Enter 1 or 2: ").strip()

        if choice == '1':
            manual_instructions()
        elif choice == '2':
            setup_kaggle_api()
            print("\nAfter setup, run this script again!")
        else:
            print("Invalid choice. Showing manual instructions:")
            manual_instructions()


if __name__ == '__main__':
    main()
