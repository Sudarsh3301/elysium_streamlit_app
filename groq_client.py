"""
Groq LLM Client Module
Handles all Groq API calls for the Elysium application.
Uses llama-3.1-8b-instant model with proper rate limiting and error handling.

Security:
- Supports both local development (.env) and Streamlit Cloud (secrets.toml)
- Never logs or prints API keys
- Validates key existence before initialization
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from groq import Groq

logger = logging.getLogger(__name__)

# Groq API Configuration
GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE = 0.6
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TOP_P = 1.0

# Rate limiting configuration
# RPM = 30, so we limit to 25 calls/min to be safe
MIN_CALL_INTERVAL = 0.04  # 40ms between calls = max 25 calls/min


def _get_api_key() -> str:
    """
    Securely retrieve Groq API key from environment or Streamlit secrets.

    Priority:
    1. Streamlit Cloud secrets (st.secrets["GROQ_API_KEY"])
    2. Environment variable (GROQ_API_KEY)
    3. Legacy environment variable (groq) - for backward compatibility

    Returns:
        API key string

    Raises:
        ValueError: If no API key is found in any location
    """
    api_key = None

    # Try Streamlit secrets first (for cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
            logger.info("Using Groq API key from Streamlit secrets")
            return api_key
    except (ImportError, FileNotFoundError, KeyError):
        # Streamlit not available or secrets not configured
        pass

    # Try standard environment variable
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        logger.info("Using Groq API key from GROQ_API_KEY environment variable")
        return api_key

    # Try legacy environment variable for backward compatibility
    api_key = os.getenv("groq")
    if api_key:
        logger.warning("Using legacy 'groq' environment variable. Please migrate to 'GROQ_API_KEY'")
        return api_key

    # No API key found
    raise ValueError(
        "Groq API key not found. Please set one of:\n"
        "  - Streamlit Cloud: Add GROQ_API_KEY to secrets.toml\n"
        "  - Local development: Set GROQ_API_KEY in .env file\n"
        "  - Environment: export GROQ_API_KEY='your-key-here'"
    )


class GroqClient:
    """Handles all Groq API interactions with rate limiting and error handling."""

    def __init__(self):
        """
        Initialize Groq client with API key from secure sources.

        Raises:
            ValueError: If API key is not found or invalid
        """
        try:
            # Securely retrieve API key (never log the actual key value)
            api_key = _get_api_key()

            # Validate key format (basic check)
            if not api_key or len(api_key) < 20:
                raise ValueError("Invalid Groq API key format")

            # Initialize Groq client
            self.client = Groq(api_key=api_key)
            self.last_call_time = 0

            # Log success without exposing key
            logger.info("Groq client initialized successfully with llama-3.1-8b-instant")

        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < MIN_CALL_INTERVAL:
            sleep_time = MIN_CALL_INTERVAL - time_since_last_call
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        stream: bool = False
    ) -> Optional[str]:
        """
        Generate text using Groq API with proper message formatting.
        
        Args:
            system_prompt: System message defining the AI's role and behavior
            user_prompt: User message with the actual query/request
            temperature: Controls randomness (0.0-1.0, default 0.6)
            max_tokens: Maximum tokens in response (default 1024)
            stream: Whether to stream the response (default False)
        
        Returns:
            Generated text or None if error occurs
        """
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Create messages in proper format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Make API call
            completion = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=DEFAULT_TOP_P,
                stream=stream,
                stop=None
            )
            
            if stream:
                # Return the stream object for caller to handle
                return completion
            else:
                # Extract and return the response text
                response_text = completion.choices[0].message.content
                return response_text.strip() if response_text else ""
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return None
    
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> Optional[Dict[str, Any]]:
        """
        Generate JSON response using Groq API.
        Automatically extracts JSON from the response.
        
        Args:
            system_prompt: System message defining the AI's role and behavior
            user_prompt: User message with the actual query/request
            temperature: Controls randomness (0.0-1.0, default 0.6)
            max_tokens: Maximum tokens in response (default 1024)
        
        Returns:
            Parsed JSON dict or None if error occurs
        """
        try:
            response_text = self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            if not response_text:
                return None
            
            # Try to extract JSON from response
            # First try direct parsing
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON object in the response
                import re
                json_match = re.search(r'\{[^}]*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                
                logger.warning(f"Could not extract JSON from response: {response_text[:100]}")
                return {}
            
        except Exception as e:
            logger.error(f"Error generating JSON response: {e}")
            return None

