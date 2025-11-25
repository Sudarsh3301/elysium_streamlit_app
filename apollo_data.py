"""
Apollo Data Loading Module
Handles loading and processing of all data sources for the Apollo Intelligence Dashboard.

Purpose: Centralized data management for Apollo with graceful error handling
Inputs: CSV files from out/ directory
Outputs: Processed DataFrames and calculated metrics
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Any

# Import unified data loader and Apollo image utilities
from unified_data_loader import unified_loader
from apollo_image_utils import ApolloImageHandler, apollo_model_cache
from path_config import paths

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApolloDataLoader:
    """Centralized data loader for Apollo Intelligence Dashboard."""
    
    def __init__(self, data_dir: str = None):
        """Initialize with data directory path."""
        # Use centralized path management
        self.data_dir = paths.data_dir if data_dir is None else Path(data_dir).resolve()
        self._cache = {}
        logger.info(f"Apollo data directory: {self.data_dir}")
        
    @st.cache_data
    def load_all_data(_self) -> Dict[str, pd.DataFrame]:
        """
        Load all required data files for Apollo dashboard.
        
        Returns:
            Dict containing all loaded DataFrames with graceful error handling
        """
        data = {}
        
        # REFACTORED: Use unified loader for models, CSV for other data
        files_to_load = {
            'models': (None, _self._load_models_unified),  # Use unified loader
            'bookings': ('bookings.csv', _self._load_bookings),
            'performance': ('model_performance.csv', _self._load_performance),
            'clients': ('clients.csv', _self._load_clients),
            'athena_events': ('athena_events.csv', _self._load_athena_events)
        }

        for key, (filename, loader_func) in files_to_load.items():
            try:
                if filename is None:  # Special case for unified loader
                    data[key] = loader_func()
                    logger.info(f"✅ Loaded {key}: {len(data[key])} records")
                else:
                    file_path = _self.data_dir / filename
                    if file_path.exists():
                        data[key] = loader_func(file_path)
                        logger.info(f"✅ Loaded {key}: {len(data[key])} records")
                    else:
                        logger.warning(f"⚠️ File not found: {filename}")
                        data[key] = pd.DataFrame()  # Empty DataFrame as fallback
            except Exception as e:
                logger.error(f"❌ Failed to load {filename or key}: {e}")
                data[key] = pd.DataFrame()  # Empty DataFrame as fallback
        
        return data
    
    def _load_models_unified(self) -> pd.DataFrame:
        """
        REFACTORED: Load models using unified data loader from models_final.jsonl.
        """
        try:
            df = unified_loader.load_models()

            if df.empty:
                logger.warning("No models loaded from unified loader")
                return pd.DataFrame()

            # Ensure all required columns exist for Apollo compatibility
            required_cols = ['model_id', 'name', 'division', 'height_cm', 'hair_color', 'eye_color', 'primary_thumbnail']
            for col in required_cols:
                if col not in df.columns:
                    if col == 'primary_thumbnail':
                        df[col] = df.get('thumbnail', "https://via.placeholder.com/150x200/cccccc/666666?text=No+Image")
                    else:
                        df[col] = None

            logger.info(f"✅ Loaded {len(df)} models from unified loader")
            return df

        except Exception as e:
            logger.error(f"❌ Failed to load models from unified loader: {e}")
            return pd.DataFrame()

    def _load_models(self, file_path: Path) -> pd.DataFrame:
        """
        DEPRECATED: Legacy CSV loading method kept for compatibility.
        Use _load_models_unified instead.
        """
        logger.warning("_load_models is deprecated. Using unified loader instead.")
        return self._load_models_unified()
    
    def _load_bookings(self, file_path: Path) -> pd.DataFrame:
        """Load and process bookings data."""
        df = pd.read_csv(file_path)
        
        # Convert date columns
        date_cols = ['casting_received_date', 'confirmed_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = ['time_to_book_days', 'revenue_usd']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert boolean columns
        bool_cols = ['is_digital', 'cancelled', 'athena_assisted']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        return df
    
    def _load_performance(self, file_path: Path) -> pd.DataFrame:
        """Load and process model performance data."""
        df = pd.read_csv(file_path)
        
        # Convert numeric columns
        numeric_cols = [
            'total_bookings', 'revenue_total_usd', 'avg_time_to_book_days',
            'utilization_rate_pct', 'digital_booking_pct', 'cancellation_rate_pct',
            'rebook_rate_pct', 'casting_to_booking_conversion_pct'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _load_clients(self, file_path: Path) -> pd.DataFrame:
        """Load and process clients data."""
        df = pd.read_csv(file_path)
        
        # Convert VIP column to boolean
        if 'vip' in df.columns:
            df['vip'] = df['vip'].astype(bool)
        
        return df
    
    def _load_athena_events(self, file_path: Path) -> pd.DataFrame:
        """Load and process Athena events data."""
        df = pd.read_csv(file_path)
        
        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Convert selected to boolean
        if 'selected' in df.columns:
            df['selected'] = df['selected'].astype(bool)
        
        return df

class ApolloMetrics:
    """Calculate key metrics for Apollo dashboard."""
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        """Initialize with loaded data."""
        self.data = data
        self.current_date = datetime.now()
        self.last_90_days = self.current_date - timedelta(days=90)
        self.prev_90_days = self.current_date - timedelta(days=180)
    
    def calculate_kpi_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate all KPI metrics for the hero tiles.
        
        Returns:
            Dict with metric name as key and dict with value, delta, insight as values
        """
        metrics = {}
        
        if not self.data['bookings'].empty:
            bookings_df = self.data['bookings']
            
            # Filter for last 90 days and previous 90 days
            current_bookings = bookings_df[
                bookings_df['confirmed_date'] >= self.last_90_days
            ] if 'confirmed_date' in bookings_df.columns else pd.DataFrame()
            
            prev_bookings = bookings_df[
                (bookings_df['confirmed_date'] >= self.prev_90_days) & 
                (bookings_df['confirmed_date'] < self.last_90_days)
            ] if 'confirmed_date' in bookings_df.columns else pd.DataFrame()
            
            # Total Revenue
            current_revenue = current_bookings['revenue_usd'].sum() if not current_bookings.empty else 0
            prev_revenue = prev_bookings['revenue_usd'].sum() if not prev_bookings.empty else 0
            revenue_delta = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
            
            metrics['total_revenue'] = {
                'value': current_revenue,
                'delta': revenue_delta,
                'insight': self._get_revenue_insight(revenue_delta)
            }
            
            # Conversion Rate (from performance data)
            if not self.data['performance'].empty:
                avg_conversion = self.data['performance']['casting_to_booking_conversion_pct'].mean()
                metrics['conversion_rate'] = {
                    'value': avg_conversion,
                    'delta': 0,  # Would need historical data for delta
                    'insight': "Strong casting performance"
                }
            
            # Rebooking Rate
            if not self.data['performance'].empty:
                avg_rebook = self.data['performance']['rebook_rate_pct'].mean()
                metrics['rebook_rate'] = {
                    'value': avg_rebook,
                    'delta': 0,  # Would need historical data for delta
                    'insight': "Client satisfaction indicator"
                }
            
            # Average Time to Book
            avg_time_to_book = current_bookings['time_to_book_days'].mean() if not current_bookings.empty else 0
            prev_avg_time = prev_bookings['time_to_book_days'].mean() if not prev_bookings.empty else 0
            time_delta = ((avg_time_to_book - prev_avg_time) / prev_avg_time * 100) if prev_avg_time > 0 else 0
            
            metrics['avg_time_to_book'] = {
                'value': avg_time_to_book,
                'delta': -time_delta,  # Negative because lower is better
                'insight': "Booking efficiency metric"
            }
            
            # Automation Assist Rate
            athena_bookings = current_bookings['athena_assisted'].sum() if not current_bookings.empty else 0
            total_bookings = len(current_bookings) if not current_bookings.empty else 1
            automation_rate = (athena_bookings / total_bookings * 100) if total_bookings > 0 else 0
            
            metrics['automation_rate'] = {
                'value': automation_rate,
                'delta': 0,  # Would need historical data
                'insight': "AI efficiency boost"
            }
        
        # Active Model Ratio
        if not self.data['models'].empty and not self.data['bookings'].empty:
            total_models = len(self.data['models'])
            active_models = self.data['bookings']['model_id'].nunique()
            active_ratio = (active_models / total_models * 100) if total_models > 0 else 0
            
            metrics['active_model_ratio'] = {
                'value': active_ratio,
                'delta': 0,  # Would need historical data
                'insight': "Portfolio utilization"
            }
        
        return metrics
    
    def _get_revenue_insight(self, delta: float) -> str:
        """Generate insight text based on revenue delta."""
        if delta > 15:
            return "↑ Strong growth momentum"
        elif delta > 5:
            return "↑ Steady growth trend"
        elif delta > -5:
            return "→ Stable performance"
        else:
            return "↓ Needs attention"
    
    def get_top_performers(self, limit: int = 10) -> pd.DataFrame:
        """Get top performing models by revenue."""
        if self.data['performance'].empty or self.data['models'].empty:
            return pd.DataFrame()

        # Ensure model_id columns have consistent data types
        performance_df = self.data['performance'].copy()
        models_df = self.data['models'].copy()

        # Convert model_id to string for consistent merging
        performance_df['model_id'] = performance_df['model_id'].astype(str)
        models_df['model_id'] = models_df['model_id'].astype(str)

        # Merge performance with model data
        top_performers = performance_df.merge(
            models_df[['model_id', 'name', 'division']],
            on='model_id',
            how='left'
        ).sort_values('revenue_total_usd', ascending=False).head(limit)
        
        return top_performers
    
    def get_inactive_models(self, days_threshold: int = 90) -> pd.DataFrame:
        """Get DataFrame of models with no recent bookings."""
        if self.data['bookings'].empty or self.data['models'].empty:
            return pd.DataFrame()

        # Get models with recent bookings
        recent_cutoff = self.current_date - timedelta(days=days_threshold)
        recent_bookings = self.data['bookings'][
            self.data['bookings']['confirmed_date'] >= recent_cutoff
        ] if 'confirmed_date' in self.data['bookings'].columns else pd.DataFrame()

        active_model_ids = set(recent_bookings['model_id'].unique()) if not recent_bookings.empty else set()
        all_model_ids = set(self.data['models']['model_id'].unique())

        inactive_model_ids = all_model_ids - active_model_ids

        # Get full data of inactive models
        inactive_models = self.data['models'][
            self.data['models']['model_id'].isin(inactive_model_ids)
        ].head(20)  # Limit to 20 for display

        return inactive_models
    
    def get_vip_clients(self) -> pd.DataFrame:
        """Get VIP client information with booking stats."""
        if self.data['clients'].empty:
            return pd.DataFrame()
        
        vip_clients = self.data['clients'][self.data['clients']['vip'] == True].copy()
        
        if not self.data['bookings'].empty and not vip_clients.empty:
            # Add booking stats
            client_stats = self.data['bookings'].groupby('client_id').agg({
                'revenue_usd': 'sum',
                'booking_id': 'count'
            }).rename(columns={'booking_id': 'total_bookings'}).reset_index()

            # Ensure client_id columns have consistent data types
            vip_clients['client_id'] = vip_clients['client_id'].astype(str)
            client_stats['client_id'] = client_stats['client_id'].astype(str)

            vip_clients = vip_clients.merge(client_stats, on='client_id', how='left')
            vip_clients['revenue_usd'] = vip_clients['revenue_usd'].fillna(0)
            vip_clients['total_bookings'] = vip_clients['total_bookings'].fillna(0)
        
        return vip_clients.sort_values('revenue_usd', ascending=False) if 'revenue_usd' in vip_clients.columns else vip_clients
