"""
Catalogue Module
Modular components for the Elysium Model Catalogue system.
"""

# Data Processing Components
from .data_processing import (
    DataLoader,
    AttributeMatcher,
    DivisionMapper,
    HeightCalculator,
    ImageHandler
)

# Filtering System Components
from .filter_engine import (
    FilterEngine,
    OllamaClient
)

# UI Components
from .ui_components import (
    ModelCardRenderer,
    SearchRenderer,
    ExpandedModelRenderer,
    ModelProfilePage
)

__all__ = [
    # Data Processing
    'DataLoader',
    'AttributeMatcher', 
    'DivisionMapper',
    'HeightCalculator',
    'ImageHandler',
    
    # Filtering
    'FilterEngine',
    'OllamaClient',
    
    # UI Components
    'ModelCardRenderer',
    'SearchRenderer',
    'ExpandedModelRenderer',
    'ModelProfilePage'
]
