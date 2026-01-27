#!/usr/bin/env python3
"""
Performance Monitor for ANPR System
Tracks detection times, accuracy, and system performance
"""

import time
import logging
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Monitor and track ANPR system performance metrics
    """
    
    def __init__(self, max_history: int = 1000):
        """Initialize performance monitor"""
        self.max_history = max_history
        self.detection_times = deque(maxlen=max_history)
        self.detection_results = deque(maxlen=max_history)
        self.method_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'success': 0})
        self.hourly_stats = defaultdict(lambda: {'detections': 0, 'successes': 0, 'avg_time': 0})
        
        self._lock = threading.Lock()
        self.start_time = time.time()
        
        logger.info("📊 Performance Monitor initialized")
    
    def record_detection(self, 
                        method: str, 
                        processing_time: float, 
                        success: bool, 
                        confidence: float = 0.0,
                        plate_text: str = None):
        """
        Record a detection attempt
        
        Args:
            method: Detection method used
            processing_time: Time taken for detection
            success: Whether detection was successful
            confidence: Detection confidence score
            plate_text: Detected plate text (if any)
        """
        with self._lock:
            timestamp = time.time()
            
            # Record detection time
            self.detection_times.append({
                'timestamp': timestamp,
                'method': method,
                'time': processing_time,
                'success': success,
                'confidence': confidence,
                'plate': plate_text
            })
            
            # Update method statistics
            self.method_stats[method]['count'] += 1
            self.method_stats[method]['total_time'] += processing_time
            if success:
                self.method_stats[method]['success'] += 1
            
            # Update hourly statistics
            hour_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d-%H')
            self.hourly_stats[hour_key]['detections'] += 1
            if success:
                self.hourly_stats[hour_key]['successes'] += 1
            
            # Update average time for this hour
            hour_detections = self.hourly_stats[hour_key]['detections']
            current_avg = self.hourly_stats[hour_key]['avg_time']
            self.hourly_stats[hour_key]['avg_time'] = (
                (current_avg * (hour_detections - 1) + processing_time) / hour_detections
            )
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        with self._lock:
            if not self.detection_times:
                return {"status": "no_data"}
            
            # Calculate overall statistics
            total_detections = len(self.detection_times)
            successful_detections = sum(1 for d in self.detection_times if d['success'])
            
            # Calculate average times
            all_times = [d['time'] for d in self.detection_times]
            successful_times = [d['time'] for d in self.detection_times if d['success']]
            
            avg_time = sum(all_times) / len(all_times) if all_times else 0
            avg_successful_time = sum(successful_times) / len(successful_times) if successful_times else 0
            
            # Calculate success rate
            success_rate = (successful_detections / total_detections * 100) if total_detections > 0 else 0
            
            # Get method performance
            method_performance = {}
            for method, stats in self.method_stats.items():
                if stats['count'] > 0:
                    method_performance[method] = {
                        'count': stats['count'],
                        'success_rate': (stats['success'] / stats['count'] * 100),
                        'avg_time': stats['total_time'] / stats['count'],
                        'total_time': stats['total_time']
                    }
            
            # Recent performance (last 100 detections)
            recent_detections = list(self.detection_times)[-100:]
            recent_success_rate = (
                sum(1 for d in recent_detections if d['success']) / len(recent_detections) * 100
                if recent_detections else 0
            )
            recent_avg_time = (
                sum(d['time'] for d in recent_detections) / len(recent_detections)
                if recent_detections else 0
            )
            
            return {
                "status": "active",
                "uptime_hours": (time.time() - self.start_time) / 3600,
                "total_detections": total_detections,
                "successful_detections": successful_detections,
                "success_rate": round(success_rate, 2),
                "avg_detection_time": round(avg_time, 3),
                "avg_successful_time": round(avg_successful_time, 3),
                "recent_success_rate": round(recent_success_rate, 2),
                "recent_avg_time": round(recent_avg_time, 3),
                "method_performance": method_performance,
                "fastest_method": self._get_fastest_method(),
                "most_accurate_method": self._get_most_accurate_method()
            }
    
    def _get_fastest_method(self) -> Optional[str]:
        """Get the fastest detection method"""
        fastest_method = None
        fastest_time = float('inf')
        
        for method, stats in self.method_stats.items():
            if stats['count'] > 5:  # Need at least 5 samples
                avg_time = stats['total_time'] / stats['count']
                if avg_time < fastest_time:
                    fastest_time = avg_time
                    fastest_method = method
        
        return fastest_method
    
    def _get_most_accurate_method(self) -> Optional[str]:
        """Get the most accurate detection method"""
        most_accurate_method = None
        highest_accuracy = 0
        
        for method, stats in self.method_stats.items():
            if stats['count'] > 5:  # Need at least 5 samples
                accuracy = (stats['success'] / stats['count']) * 100
                if accuracy > highest_accuracy:
                    highest_accuracy = accuracy
                    most_accurate_method = method
        
        return most_accurate_method
    
    def get_real_time_metrics(self) -> Dict:
        """Get real-time performance metrics"""
        with self._lock:
            # Last 10 detections
            recent = list(self.detection_times)[-10:]
            
            if not recent:
                return {"status": "no_recent_data"}
            
            # Calculate recent metrics
            recent_times = [d['time'] for d in recent]
            recent_successes = sum(1 for d in recent if d['success'])
            
            return {
                "last_10_avg_time": round(sum(recent_times) / len(recent_times), 3),
                "last_10_success_rate": round((recent_successes / len(recent)) * 100, 1),
                "last_detection_time": round(recent[-1]['time'], 3) if recent else 0,
                "last_detection_success": recent[-1]['success'] if recent else False,
                "last_detection_method": recent[-1]['method'] if recent else None,
                "detections_per_minute": self._calculate_detections_per_minute()
            }
    
    def _calculate_detections_per_minute(self) -> float:
        """Calculate detections per minute over last 5 minutes"""
        current_time = time.time()
        five_minutes_ago = current_time - 300  # 5 minutes
        
        recent_detections = [
            d for d in self.detection_times 
            if d['timestamp'] > five_minutes_ago
        ]
        
        return len(recent_detections) / 5.0  # per minute
    
    def export_metrics(self, filepath: str):
        """Export performance metrics to JSON file"""
        try:
            summary = self.get_performance_summary()
            summary['export_timestamp'] = datetime.now().isoformat()
            summary['detection_history'] = [
                {
                    'timestamp': d['timestamp'],
                    'method': d['method'],
                    'time': d['time'],
                    'success': d['success'],
                    'confidence': d['confidence']
                }
                for d in list(self.detection_times)
            ]
            
            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"📊 Performance metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        with self._lock:
            self.detection_times.clear()
            self.detection_results.clear()
            self.method_stats.clear()
            self.hourly_stats.clear()
            self.start_time = time.time()
            
        logger.info("📊 Performance metrics reset")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def record_detection_performance(method: str, processing_time: float, success: bool, 
                               confidence: float = 0.0, plate_text: str = None):
    """Convenience function to record detection performance"""
    performance_monitor.record_detection(method, processing_time, success, confidence, plate_text)
