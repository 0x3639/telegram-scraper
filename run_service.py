#!/usr/bin/env python3
"""
Telegram Scraper Service Runner
Automatically runs continuous scraping with proper error handling and logging
"""
import os
import sys
import time
import logging
import asyncio
import signal
import importlib.util
from datetime import datetime
from pathlib import Path

# Import the main scraper module (handles hyphenated filename)
script_dir = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("telegram_scraper", os.path.join(script_dir, "telegram-scraper.py"))
telegram_scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(telegram_scraper)

OptimizedTelegramScraper = telegram_scraper.OptimizedTelegramScraper

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'telegram_scraper_{datetime.now():%Y%m%d}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('TelegramScraperService')

class TelegramScraperService:
    def __init__(self):
        self.scraper = OptimizedTelegramScraper()
        self.running = True
        self.shutdown_requested = False
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self.shutdown_handler)
    
    def shutdown_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        if self.shutdown_requested:
            logger.warning("Force shutdown requested, exiting immediately...")
            sys.exit(0)
        
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown_requested = True
        self.running = False
        self.scraper.continuous_scraping_active = False
        
    async def run_service(self):
        """Main service loop"""
        logger.info("Starting Telegram Scraper Service")
        
        try:
            # Initialize the client
            await self.scraper.initialize_client()
            logger.info("Telegram client initialized successfully")
            
            # Check if we have channels configured
            if not self.scraper.state['channels']:
                logger.error("No channels configured! Add channels before running as service.")
                return
            
            # Run continuous scraping
            while self.running and not self.shutdown_requested:
                try:
                    logger.info(f"Starting scrape cycle for {len(self.scraper.state['channels'])} channels")
                    
                    for channel in self.scraper.state['channels']:
                        if not self.running or self.shutdown_requested:
                            logger.info("Shutdown requested, stopping channel processing...")
                            break
                            
                        logger.info(f"Scraping channel: {channel}")
                        try:
                            await self.scraper.scrape_channel(
                                channel, 
                                self.scraper.state['channels'][channel]
                            )
                        except Exception as e:
                            logger.error(f"Error scraping channel {channel}: {e}")
                            # Continue with other channels
                    
                    if self.running and not self.shutdown_requested:
                        # Wait before next cycle (configurable) - interruptible sleep
                        wait_time = int(os.environ.get('SCRAPE_INTERVAL', 300))  # Default 5 minutes
                        logger.info(f"Waiting {wait_time} seconds before next cycle...")
                        
                        # Sleep in small chunks so we can respond to shutdown signals
                        for _ in range(wait_time):
                            if not self.running or self.shutdown_requested:
                                logger.info("Shutdown requested during wait, exiting...")
                                break
                            await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error in scraping cycle: {e}")
                    if self.running:
                        # Wait before retry
                        await asyncio.sleep(60)
                        
        except Exception as e:
            logger.error(f"Fatal error in service: {e}")
        finally:
            logger.info("Cleaning up...")
            self.scraper.close_db_connections()
            if self.scraper.client:
                await self.scraper.client.disconnect()
            logger.info("Service stopped")

async def main():
    service = TelegramScraperService()
    await service.run_service()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service crashed: {e}")
        sys.exit(1)