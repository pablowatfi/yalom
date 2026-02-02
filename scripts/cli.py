"""
Command-line interface for the YouTube transcript scraper.
"""
import argparse
import logging
import sys
import os

from src import init_db, get_db_session, ChannelScraper
from src.ingestion import TapeSearchScraper, GitHubScraper, KaggleScraper
from src.config import LOG_LEVEL, LOG_FORMAT, DEFAULT_DELAY_SECONDS


def setup_logging(level: str = LOG_LEVEL):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def scrape_channel_command(args):
    """Handle the scrape-channel command."""
    logger = logging.getLogger(__name__)

    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db(args.database_url)

        # Create scraper
        session = get_db_session()
        scraper = ChannelScraper(session, delay=args.delay)

        # Scrape channel
        logger.info(f"Starting scrape of channel: {args.channel_url}")
        stats = scraper.scrape_channel(
            channel_url=args.channel_url,
            skip_existing=not args.reprocess,
            max_videos=args.max_videos
        )

        # Print summary
        print("\n" + "="*60)
        print("Scraping Complete!")
        print(f"  ✓ Success: {stats['success']}")
        print(f"  ✗ Failed: {stats['failed']}")
        print(f"  ⊘ Skipped: {stats['skipped']}")
        print(f"  Total: {stats['total']}")
        print("="*60)

        session.close()

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        sys.exit(1)


def scrape_video_command(args):
    """Handle the scrape-video command."""
    logger = logging.getLogger(__name__)

    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db(args.database_url)

        # Create scraper
        session = get_db_session()
        scraper = ChannelScraper(session)

        # Scrape video
        logger.info(f"Scraping video: {args.video_id}")
        success = scraper.scrape_video(args.video_id)

        if success:
            print(f"✓ Successfully scraped video: {args.video_id}")
        else:
            print(f"✗ Failed to scrape video: {args.video_id}")
            sys.exit(1)

        session.close()

    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        sys.exit(1)


def init_db_command(args):
    """Handle the init-db command."""
    logger = logging.getLogger(__name__)

    try:
        logger.info("Initializing database...")
        init_db(args.database_url)
        print("✓ Database initialized successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)


def tapesearch_scrape_podcast_command(args):
    """Handle the tapesearch-scrape command."""
    logger = logging.getLogger(__name__)

    try:
        # Get API key from environment
        api_key = os.environ.get('TAPESEARCH_API_KEY')
        if not api_key:
            logger.error("TAPESEARCH_API_KEY environment variable not set")
            print("✗ Please set TAPESEARCH_API_KEY environment variable")
            print("  export TAPESEARCH_API_KEY='your_api_key_here'")
            sys.exit(1)

        # Initialize database
        logger.info("Initializing database...")
        init_db(args.database_url)

        # Create scraper
        session = get_db_session()
        scraper = TapeSearchScraper(session, api_key=api_key, delay=args.delay)

        # Scrape podcast
        logger.info(f"Starting scrape of podcast: {args.podcast_name}")
        stats = scraper.search_and_scrape_podcast(
            podcast_name=args.podcast_name,
            skip_existing=not args.reprocess,
            max_episodes=args.max_episodes
        )

        # Print summary
        print("\n" + "="*60)
        print("Scraping Complete!")
        print(f"  ✓ Success: {stats['success']}")
        print(f"  ✗ Failed: {stats['failed']}")
        print(f"  ⊘ Skipped: {stats['skipped']}")
        print(f"  Total: {stats['total']}")
        print("="*60)

        session.close()

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        sys.exit(1)


def github_load_command(args):
    """Handle the github-load command."""
    logger = logging.getLogger(__name__)

    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db(args.database_url)

        # Create scraper
        session = get_db_session()
        scraper = GitHubScraper(session, repo=args.repo)

        # Load transcripts
        if args.episode:
            logger.info(f"Loading single episode: {args.episode}")
            success = scraper.scrape_episode(args.episode)
            if success:
                print(f"✓ Successfully loaded episode {args.episode}")
            else:
                print(f"✗ Failed to load episode {args.episode}")
                sys.exit(1)
        else:
            logger.info("Loading all transcripts from GitHub")
            stats = scraper.scrape_all_transcripts(
                start_episode=args.start,
                end_episode=args.end,
                skip_existing=not args.reprocess
            )

            # Print summary
            print("\n" + "="*60)
            print("GitHub Load Complete!")
            print(f"  ✓ Success: {stats['success']}")
            print(f"  ✗ Failed: {stats['failed']}")
            print(f"  ⊘ Skipped: {stats['skipped']}")
            print(f"  Total: {stats['total']}")
            print("="*60)

        session.close()

    except KeyboardInterrupt:
        logger.info("Load interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Load failed: {e}", exc_info=True)
        sys.exit(1)


def kaggle_load_command(args):
    """Handle the kaggle-load command."""
    logger = logging.getLogger(__name__)

    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db(args.database_url)

        # Create scraper
        session = get_db_session()
        scraper = KaggleScraper(session, dataset_path=args.path)

        if args.video_id:
            # Load single video
            logger.info(f"Loading video {args.video_id} from Kaggle")
            success = scraper.scrape_video(args.video_id)

            if success:
                print(f"\n✓ Successfully loaded video {args.video_id}")
            else:
                print(f"\n✗ Failed to load video {args.video_id}")
                sys.exit(1)
        else:
            # Load all transcripts
            logger.info("Loading all transcripts from Kaggle dataset")
            stats = scraper.scrape_all_transcripts(skip_existing=args.skip_existing)

            # Print summary
            print("\n" + "="*60)
            print("Kaggle Load Complete!")
            print(f"  ✓ Success: {stats['success']}")
            print(f"  ✗ Failed: {stats['failed']}")
            print(f"  ⊘ Skipped: {stats['skipped']}")
            print(f"  Total: {stats['total']}")
            print("="*60)

        session.close()

    except KeyboardInterrupt:
        logger.info("Load interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Load failed: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="YouTube transcript scraper and analyzer"
    )
    parser.add_argument(
        '--log-level',
        default=LOG_LEVEL,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level'
    )
    parser.add_argument(
        '--database-url',
        default=None,
        help='PostgreSQL database URL (overrides config)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Scrape channel command
    scrape_channel_parser = subparsers.add_parser(
        'scrape-channel',
        help='Scrape all videos from a YouTube channel'
    )
    scrape_channel_parser.add_argument(
        'channel_url',
        help='YouTube channel URL (e.g., https://www.youtube.com/@channelname)'
    )
    scrape_channel_parser.add_argument(
        '--delay',
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f'Delay between requests in seconds (default: {DEFAULT_DELAY_SECONDS})'
    )
    scrape_channel_parser.add_argument(
        '--max-videos',
        type=int,
        default=None,
        help='Maximum number of videos to process (default: all)'
    )
    scrape_channel_parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess videos already in database'
    )
    scrape_channel_parser.set_defaults(func=scrape_channel_command)

    # Scrape video command
    scrape_video_parser = subparsers.add_parser(
        'scrape-video',
        help='Scrape a single video by ID'
    )
    scrape_video_parser.add_argument(
        'video_id',
        help='YouTube video ID'
    )
    scrape_video_parser.set_defaults(func=scrape_video_command)

    # Init database command
    init_parser = subparsers.add_parser(
        'init-db',
        help='Initialize the database (create tables)'
    )
    init_parser.set_defaults(func=init_db_command)

    # TapeSearch scrape podcast command
    tapesearch_parser = subparsers.add_parser(
        'tapesearch-scrape',
        help='Scrape podcast episodes from TapeSearch'
    )
    tapesearch_parser.add_argument(
        'podcast_name',
        help='Podcast name to search for (e.g., "Huberman Lab")'
    )
    tapesearch_parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    tapesearch_parser.add_argument(
        '--max-episodes',
        type=int,
        default=None,
        help='Maximum number of episodes to process (default: all)'
    )
    tapesearch_parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess episodes already in database'
    )
    tapesearch_parser.set_defaults(func=tapesearch_scrape_podcast_command)

    # GitHub load transcripts command
    github_parser = subparsers.add_parser(
        'github-load',
        help='Load transcripts from GitHub repository (FREE!)'
    )
    github_parser.add_argument(
        '--repo',
        default='prakhar625/huberman-podcasts-transcripts',
        help='GitHub repo in format owner/repo (default: prakhar625/huberman-podcasts-transcripts)'
    )
    github_parser.add_argument(
        '--episode',
        type=int,
        default=None,
        help='Load a single episode by number'
    )
    github_parser.add_argument(
        '--start',
        type=int,
        default=None,
        help='Start episode number (for loading range)'
    )
    github_parser.add_argument(
        '--end',
        type=int,
        default=None,
        help='End episode number (for loading range)'
    )
    github_parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess episodes already in database'
    )
    github_parser.set_defaults(func=github_load_command)

    # Kaggle load transcripts command
    kaggle_parser = subparsers.add_parser(
        'kaggle-load',
        help='Load transcripts from Kaggle dataset (197 episodes!)'
    )
    kaggle_parser.add_argument(
        '--path',
        required=True,
        help='Path to extracted Kaggle dataset folder (HubermanLabTranscripts)'
    )
    kaggle_parser.add_argument(
        '--skip-existing',
        action='store_true',
        default=True,
        help='Skip episodes already in database (default: True)'
    )
    kaggle_parser.add_argument(
        '--video-id',
        type=str,
        default=None,
        help='Load a single video by YouTube ID'
    )
    kaggle_parser.set_defaults(func=kaggle_load_command)

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
