# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Setup and Dependencies
```bash
# Install dependencies (Python 3.7+ required)
pip install -r requirements.txt

# If you encounter issues with encoding in requirements.txt, use:
pip install telethon aiohttp asyncio
```

### Running the Application
```bash
# Main script - interactive menu-based interface
python telegram-scraper.py
```

### Development Workflow
Since this is a single-file Python application without formal test/lint infrastructure:

1. **Code style**: Follow existing patterns in `telegram-scraper.py`
2. **Testing**: Manual testing through the interactive menu
3. **Dependencies**: Any new dependencies should be added to `requirements.txt`

## High-Level Architecture

### Core Components

The application is built around the `OptimizedTelegramScraper` class in `telegram-scraper.py`, which handles:

1. **State Management** (`state.json`)
   - Persists API credentials, channel list, and scraping progress
   - Enables resume capability after interruptions

2. **Database Layer** 
   - SQLite database per channel (`./channelname/channelname.db`)
   - Connection pooling for performance
   - Batch insertions (100 messages per batch)
   - Indexed on `message_id` and `date` for fast queries

3. **Async Architecture**
   - Built on `asyncio` and Telethon's async client
   - Concurrent media downloads (up to 3 simultaneous)
   - Non-blocking message processing

4. **Key Methods**
   - `scrape_channel()`: Main scraping logic with batch processing
   - `download_media_batch()`: Parallel media downloading with retry
   - `continuous_scraping()`: Real-time monitoring mode
   - `export_to_csv_optimized()` / `export_to_json_optimized()`: Memory-efficient exports

### Data Flow

1. User authenticates with Telegram API credentials
2. Channels are added to state and directories created
3. Messages fetched in batches, processed, and stored in SQLite
4. Media downloaded concurrently if enabled
5. Progress saved periodically (every 50 messages)

### Performance Optimizations

- Batch database operations (100 messages/batch)
- Parallel media downloads (3 concurrent)
- Connection pooling for database access
- Streaming exports for large datasets
- Exponential backoff for rate limit handling

### File Structure
```
./
├── telegram-scraper.py    # Main application
├── requirements.txt       # Python dependencies
├── state.json            # Persistent state (created on first run)
└── [channel_name]/       # Per-channel directory (created dynamically)
    ├── [channel_name].db # SQLite database
    ├── media/           # Downloaded media files
    ├── [channel_name].csv # Export file (on demand)
    └── [channel_name].json # Export file (on demand)
```