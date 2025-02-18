"""
Configuration path management

This module provides the CONFIG_PATH constant to avoid circular imports
"""

import os

CONFIG_PATH = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'config.ini')
