#!/usr/bin/env python3
"""
MongoDB Atlas Service - Always-On Connection Manager
Ensures Atlas connection remains active even when PC is restarted
"""

import os
import sys
import time
import logging
import schedule
import threading
from datetime import datetime, timedelta
from src.database.persistent_atlas_connection import get_persistent_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atlas_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AtlasService:
    """
    Background service to maintain MongoDB Atlas connection
    """
    
    def __init__(self):
        """Initialize Atlas service"""
        self.connection = get_persistent_connection()
        self.running = False
        self.service_thread = None
        self.last_health_check = None
        
        logger.info("🚀 Atlas Service initialized")
    
    def start_service(self):
        """
        Start the Atlas service
        """
        if self.running:
            logger.info("⚠️ Atlas service already running")
            return
        
        logger.info("🔄 Starting Atlas Service...")
        
        # Connect to Atlas
        if not self.connection.connect():
            logger.error("❌ Failed to connect to Atlas on service start")
            return False
        
        self.running = True
        
        # Schedule periodic tasks
        schedule.every(1).minutes.do(self._health_check)
        schedule.every(5).minutes.do(self._connection_maintenance)
        schedule.every(30).minutes.do(self._log_status)
        
        # Start service thread
        self.service_thread = threading.Thread(target=self._service_loop, daemon=True)
        self.service_thread.start()
        
        logger.info("✅ Atlas Service started successfully")
        return True
    
    def stop_service(self):
        """
        Stop the Atlas service
        """
        logger.info("🛑 Stopping Atlas Service...")
        self.running = False
        
        if self.service_thread and self.service_thread.is_alive():
            self.service_thread.join(timeout=5)
        
        self.connection.close()
        logger.info("✅ Atlas Service stopped")
    
    def _service_loop(self):
        """
        Main service loop
        """
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Service loop error: {e}")
                time.sleep(30)  # Wait longer on error
    
    def _health_check(self):
        """
        Perform health check on Atlas connection
        """
        try:
            if self.connection.is_connected:
                # Test with a simple ping
                self.connection.client.admin.command('ping')
                self.last_health_check = datetime.now()
                logger.debug("💓 Atlas health check passed")
            else:
                logger.warning("⚠️ Atlas not connected during health check")
                self.connection.force_reconnect()
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            self.connection.force_reconnect()
    
    def _connection_maintenance(self):
        """
        Perform connection maintenance tasks
        """
        try:
            status = self.connection.get_connection_status()
            
            # Log connection status
            logger.info(f"🔧 Connection Status: {status}")
            
            # Force reconnect if connection is stale
            if status['last_ping']:
                last_ping = datetime.fromisoformat(status['last_ping'])
                if datetime.now() - last_ping > timedelta(minutes=10):
                    logger.warning("⚠️ Connection appears stale, forcing reconnect")
                    self.connection.force_reconnect()
            
        except Exception as e:
            logger.error(f"❌ Maintenance error: {e}")
    
    def _log_status(self):
        """
        Log detailed service status
        """
        try:
            status = self.connection.get_connection_status()
            logger.info(f"📊 Atlas Service Status: {status}")
            logger.info(f"🕐 Last Health Check: {self.last_health_check}")
            
        except Exception as e:
            logger.error(f"❌ Status logging error: {e}")
    
    def get_service_status(self) -> dict:
        """
        Get comprehensive service status
        """
        return {
            "service_running": self.running,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "connection_status": self.connection.get_connection_status(),
            "uptime": datetime.now().isoformat()
        }

# Global service instance
atlas_service = AtlasService()

def start_atlas_service():
    """Start the Atlas service"""
    return atlas_service.start_service()

def stop_atlas_service():
    """Stop the Atlas service"""
    atlas_service.stop_service()

def get_service_status():
    """Get service status"""
    return atlas_service.get_service_status()

if __name__ == "__main__":
    """
    Run Atlas service as standalone script
    """
    print("🚀 Starting MongoDB Atlas Service...")
    
    try:
        if start_atlas_service():
            print("✅ Atlas Service started successfully")
            print("📋 Service will maintain connection automatically")
            print("🔄 Press Ctrl+C to stop")
            
            # Keep service running
            while True:
                time.sleep(60)
                status = get_service_status()
                print(f"📊 Service Status: Connected={status['connection_status']['connected']}")
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping Atlas Service...")
        stop_atlas_service()
        print("✅ Service stopped")
        
    except Exception as e:
        print(f"❌ Service error: {e}")
        stop_atlas_service()
        sys.exit(1)
