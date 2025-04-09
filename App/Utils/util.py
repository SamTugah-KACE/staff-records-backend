from datetime import datetime
import re
from typing import Optional, Set

import pandas as pd
import math

def sanitize_row_data(row_data: dict) -> dict:
    """
    Recursively replace any NaN values in the dictionary with None.
    """
    sanitized = {}
    for key, value in row_data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_row_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_row_data(item) if isinstance(item, dict) else (None if pd.isna(item) else item) for item in value]
        else:
            # Check for NaN (works for both float('nan') and numpy.nan)
            sanitized[key] = None if pd.isna(value) else value
    return sanitized


def get_organization_acronym(org_name: str, stopwords: Optional[Set[str]] = None) -> str:
    """
    Generate an acronym for an organization name.

    Rules:
      - Split the name into tokens by whitespace.
      - The first token (primary) is processed separately:
          • If it contains a hyphen, split it into sub-tokens and take the first letter of each sub-token (in uppercase).
          • Otherwise, take the first letter (uppercase).
      - For the remaining tokens (secondary):
          • If there are 2 or fewer tokens, use them all in order:
              - For each token, if it is a stopword (e.g. "of", "the", etc.), use its first letter in lowercase.
                Otherwise, use its first letter in uppercase.
          • If there are more than 2 secondary tokens, filter out the stopwords and then take at most the first 4 tokens 
            from the remaining (using their first letters in uppercase).
      - If there is a secondary group and the primary token was hyphenated, join primary and secondary with a hyphen.
        Otherwise, simply concatenate.

    Examples:
      "Ministry of Communication" -> "MoC"
      "Accra-Boys Scout Corporation" -> "AB-SC"
      "Ghana-India Kofi Annan Centre of Excellence in ICT" -> "GI-KACE"

    Args:
        org_name (str): The organization name.
        stopwords (Optional[Set[str]]): A set of words to ignore (case-insensitive). 
            Defaults to {"of", "the", "and", "for", "in", "at", "by", "a", "an"}.

    Returns:
        str: The generated acronym.
        
    Raises:
        ValueError: If org_name is not a nonempty string.
    """
    if not isinstance(org_name, str) or not org_name.strip():
        raise ValueError("Organization name must be a nonempty string.")

    # Default stopwords (all lowercase).
    if stopwords is None:
        stopwords = {"of", "the", "and", "for", "in", "at", "by", "a", "an"}

    # Split the organization name by whitespace.
    tokens = org_name.strip().split()
    if not tokens:
        return ""

    # Process the primary token (first token)
    first_token = tokens[0]
    first_has_hyphen = "-" in first_token
    if first_has_hyphen:
        # Split on hyphen and take first letters of each part.
        sub_tokens = [sub for sub in first_token.split("-") if sub]
        primary = "".join(sub[0].upper() for sub in sub_tokens)
    else:
        primary = first_token[0].upper()

    # Process secondary tokens (tokens[1:])
    secondary_tokens = tokens[1:]
    secondary = ""
    if not secondary_tokens:
        return primary

    if len(secondary_tokens) <= 2:
        # Use all tokens.
        letters = []
        for token in secondary_tokens:
            word = token.strip(" ,.;:-")
            if not word:
                continue
            if word.lower() in stopwords:
                letters.append(word[0].lower())
            else:
                letters.append(word[0].upper())
        secondary = "".join(letters)
    else:
        # More than 2 tokens: filter out stopwords and take up to first 4 tokens.
        filtered = [token for token in secondary_tokens if token.strip(" ,.;:-").lower() not in stopwords and token.strip(" ,.;:-")]
        if not filtered:
            # Fallback to using all tokens if filtering removes all.
            filtered = [token for token in secondary_tokens if token.strip(" ,.;:-")]
        filtered = filtered[:4]
        secondary = "".join(token.strip(" ,.;:-")[0].upper() for token in filtered)

    # Return result.
    if first_has_hyphen:
        return f"{primary}-{secondary}"
    else:
        return primary + secondary







class Validator:
    @staticmethod
    def is_valid_email(email: str) -> bool:
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    @staticmethod
    def is_valid_dob(dob: datetime) -> bool:
        today = datetime.today()
        return dob < today and (today.year - dob.year) <= 120

def get_smtp_config():
        """Provides SMTP configuration for email."""
        return {
            "host": "smtp.gmail.com",  # Example SMTP host
            "port": 587,
            "username": "dev.aiti.com.gh@gmail.com",
            "password": "palvpbokbnisspps",
            "from_email": "dev.aiti.com.gh@gmail.com",
        }


