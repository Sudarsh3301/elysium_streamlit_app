"""
Centralized Path Configuration for Elysium Streamlit Application
Provides cross-platform compatible path management for cloud deployment.

This module handles all file path resolution to ensure the application works
correctly when deployed to cloud platforms like Streamlit Cloud, Heroku, etc.
"""

import os
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

class ElysiumPaths:
    """Centralized path management for the Elysium application."""
    
    def __init__(self):
        """Initialize path configuration based on current working directory."""
        # Determine the project root directory
        # This works whether we're running from elysium_streamlit_app/ or from project root
        self._project_root = self._find_project_root()
        logger.info(f"Elysium project root: {self._project_root}")
        
    def _find_project_root(self) -> Path:
        """
        Find the project root directory by looking for key marker files.
        
        Returns:
            Path to the project root directory
        """
        current_dir = Path.cwd().resolve()
        
        # Look for marker files that indicate project root
        marker_files = [
            'elysium_streamlit_app',  # Directory
            'out',                    # Directory  
            'elysium_kb',            # Directory
            'requirements.txt'        # File
        ]
        
        # Check current directory first
        if self._has_markers(current_dir, marker_files):
            return current_dir
            
        # Check parent directories
        for parent in current_dir.parents:
            if self._has_markers(parent, marker_files):
                return parent
                
        # If we can't find markers, assume current directory is project root
        logger.warning(f"Could not find project root markers, using: {current_dir}")
        return current_dir
    
    def _has_markers(self, directory: Path, markers: list) -> bool:
        """Check if directory contains the expected marker files/directories."""
        found_markers = 0
        for marker in markers:
            if (directory / marker).exists():
                found_markers += 1
        
        # Require at least 2 markers to be confident this is project root
        return found_markers >= 2
    
    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory (out/)."""
        # REFACTORED: Data files are now in elysium_streamlit_app/out/
        # Check if we're running from within elysium_streamlit_app directory
        current_dir = Path.cwd().resolve()
        if current_dir.name == "elysium_streamlit_app":
            # We're running from within the app directory
            return current_dir / "out"
        else:
            # We're running from project root
            return self.app_dir / "out"
    
    @property
    def images_dir(self) -> Path:
        """Get the images directory (elysium_kb/images/)."""
        return self._project_root / "elysium_kb" / "images"
    
    @property
    def elysium_kb_dir(self) -> Path:
        """Get the elysium_kb directory."""
        return self._project_root / "elysium_kb"
    
    @property
    def app_dir(self) -> Path:
        """Get the streamlit app directory."""
        return self._project_root / "elysium_streamlit_app"
    
    @property
    def templates_dir(self) -> Path:
        """Get the templates directory."""
        return self.app_dir / "templates"
    
    @property
    def pdfs_dir(self) -> Path:
        """Get the PDFs directory."""
        return self.app_dir / "pdfs"
    
    def get_data_file(self, filename: str) -> Path:
        """
        Get path to a data file in the out/ directory.
        
        Args:
            filename: Name of the data file (e.g., 'models_normalized.csv')
            
        Returns:
            Path to the data file
        """
        return self.data_dir / filename
    
    def get_image_path(self, relative_path: str) -> Optional[Path]:
        """
        Resolve an image path relative to the elysium_kb/images directory.
        
        Args:
            relative_path: Relative path to image (e.g., 'eleena_mills/thumbnail.jpg')
            
        Returns:
            Resolved Path object if file exists, None otherwise
        """
        if not relative_path:
            return None
            
        # Clean the path - remove leading slashes and normalize separators
        clean_path = relative_path.lstrip('/').replace('\\', '/')
        
        # Try the main images directory first
        full_path = self.images_dir / clean_path
        if full_path.exists():
            return full_path
            
        # Try alternative locations for backward compatibility
        alternative_paths = [
            self.elysium_kb_dir / clean_path,  # Direct under elysium_kb
            self._project_root / clean_path,   # Direct under project root
        ]
        
        for alt_path in alternative_paths:
            if alt_path.exists():
                logger.debug(f"Found image at alternative location: {alt_path}")
                return alt_path
                
        logger.warning(f"Image not found: {relative_path}")
        return None
    
    def get_template_path(self, template_name: str) -> Path:
        """
        Get path to a template file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Path to the template file
        """
        return self.templates_dir / template_name
    
    def ensure_directory_exists(self, directory: Union[str, Path]) -> Path:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path to create
            
        Returns:
            Path object for the directory
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    def validate_data_files(self) -> dict:
        """
        Validate that all expected data files exist.
        
        Returns:
            Dictionary with file status information
        """
        expected_files = [
            'models_normalized.csv',
            'bookings.csv',
            'clients.csv',
            'model_performance.csv',
            'athena_events.csv'
        ]
        
        status = {}
        for filename in expected_files:
            file_path = self.get_data_file(filename)
            status[filename] = {
                'exists': file_path.exists(),
                'path': str(file_path),
                'size': file_path.stat().st_size if file_path.exists() else 0
            }
            
        return status
    
    def get_relative_path(self, absolute_path: Union[str, Path]) -> str:
        """
        Convert an absolute path to a relative path from project root.
        
        Args:
            absolute_path: Absolute path to convert
            
        Returns:
            Relative path string
        """
        abs_path = Path(absolute_path)
        try:
            return str(abs_path.relative_to(self._project_root))
        except ValueError:
            # Path is not relative to project root
            return str(abs_path)

# Global instance for use throughout the application
paths = ElysiumPaths()

# Convenience functions for backward compatibility
def get_data_file(filename: str) -> Path:
    """Get path to a data file."""
    return paths.get_data_file(filename)

def get_image_path(relative_path: str) -> Optional[Path]:
    """Get resolved image path."""
    return paths.get_image_path(relative_path)

def get_project_root() -> Path:
    """Get the project root directory."""
    return paths.project_root
