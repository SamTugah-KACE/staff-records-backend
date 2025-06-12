from datetime import datetime
import json
import re
from typing import Optional, Set

import pandas as pd
import math

from fastapi import Request, HTTPException
from typing import Any, Dict, List, TypeVar, Union

T = TypeVar("T")


def extract_attachments(data: dict) -> list[dict]:
    """
    Only consider items whose key contains 'path' as attachments.
    Values may be:
      - dict of {filename: url}
      - JSON‐encoded dict strings
    """
    attachments = []
    for key, val in data.items():
        if "path" not in key.lower():
            continue

        # Case 1: native dict
        if isinstance(val, dict):
            for fn, url in val.items():
                attachments.append({"filename": fn, "url": url})
            continue

        # Case 2: JSON‐encoded dict string
        if isinstance(val, str) and val.strip().startswith("{") and val.strip().endswith("}"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, dict):
                    for fn, url in parsed.items():
                        attachments.append({"filename": fn, "url": url})
                    continue
            except json.JSONDecodeError:
                pass

    return attachments




def extract_items(param: Union[Dict[Any, T], List[T], T]) -> T:
    """
    Normalize an incoming parameter into a single value.

    - If param is a dict, return its first value.
    - If param is a list, return its first element.
    - If param is a string (or any other scalar), return it as-is.

    Raises:
        HTTPException: if the dict or list is empty.
    """
    # Strings are iterable, so check them before lists
    if isinstance(param, str):
        return param  # return the string unchanged

    if isinstance(param, dict):
        try:
            return next(iter(param.values()))
        except StopIteration:
            raise HTTPException(status_code=400, detail="Dict parameter is empty")

    if isinstance(param, list):
        try:
            return param[0]
        except IndexError:
            raise HTTPException(status_code=400, detail="List parameter is empty")

    # For any other type (int, float, custom object, etc.), return as-is
    return param


def get_create_user_url(request: Request) -> str:
    """
    Returns the backend host URL with `/api/users/create` appended.
    Example: if the base URL is http://example.com/, returns http://example.com/api/users/create.
    """
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/api/users/create"

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


def get_organization_acronym_(org_name: str, stopwords: Optional[Set[str]] = None) -> str:
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
    
    #if org_name is a single token or the token is hyphenated, return its entire word with first letter capitalized.
    # If there's only one token, return it with first letter capitalized.
    # If the token is hyphenated, return the first letter of each part capitalized.
    if len(tokens) == 0:
        return ""
    # If there's only one token, return it with first letter capitalized.
    if len(tokens) == 1:
        return tokens[0][0].upper() + tokens[0][1:].lower()
    
    #if the token is two but hyphenated, return the entire word with first letter capitalized.
    if len(tokens) == 2 and "-" in tokens[0]:
        # Split on hyphen and take first letters of each part.
        sub_tokens = [sub for sub in tokens[0].split("-") if sub]
        return "".join(sub[0].upper() for sub in sub_tokens)
    

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





from typing import Optional, Set

DEFAULT_STOPWORDS = {"of", "the", "and", "for", "in", "at", "by", "a", "an"}


def get_organization_acronym(
    org_name: str,
    *,
    stopwords: Optional[Set[str]] = None,
    max_original_length: int = 10,
    max_original_tokens: int = 2,
    max_acronym_secondary: int = 4,
) -> str:
    """
    Return a user-friendly label for an organization name:
      - If the name is a single “short” word (<= max_original_length chars),
        returns it title-cased (e.g. "pixar" -> "Pixar").
      - If the name is 2 words or fewer (<= max_original_tokens) and its total
        length is <= max_original_length * max_original_tokens,
        returns title-cased original (e.g. "acme corp" -> "Acme Corp").
      - Otherwise, generates an acronym, stripping common stopwords.

    Args:
        org_name: Raw organization name.
        stopwords: Words to ignore in acronym (defaults to common small words).
        max_original_length: Max chars for a “short” single word.
        max_original_tokens: Max words to keep as original title.
        max_acronym_secondary: Max non-stopword tokens for acronym.

    Returns:
        A cleaned title or an acronym (all in ASCII letters).
    """
    if not isinstance(org_name, str) or not org_name.strip():
        raise ValueError("Organization name must be a nonempty string.")

    stopwords = stopwords or DEFAULT_STOPWORDS

    # Normalize whitespace
    parts = org_name.strip().split()
    total_length = len(org_name.strip())

    # 1) Short single word → Title-case
    if len(parts) == 1 and len(parts[0]) <= max_original_length:
        return parts[0].capitalize()

    # 2) Very short multi-word name → Title-case full name
    if len(parts) <= max_original_tokens and total_length <= max_original_length * max_original_tokens:
        return " ".join(p.capitalize() for p in parts)

    # 3) Fallback to acronym
    return _make_acronym(parts, stopwords, max_acronym_secondary)


def _make_acronym(tokens: list[str], stopwords: Set[str], max_secondary: int) -> str:
    """
    Build an acronym from token list:
      - Take first letter of first token (hyphenated → each sub-piece).
      - From remaining tokens, drop stopwords, take up to max_secondary,
        first letters only.
      - Join with hyphen if the first token was hyphenated.
    """
    # Primary
    first = tokens[0]
    if "-" in first:
        subtoks = [s for s in first.split("-") if s]
        primary = "".join(s[0].upper() for s in subtoks)
        hyphenated = True
    else:
        primary = first[0].upper()
        hyphenated = False

    # Secondary
    second_tokens = tokens[1:]
    # Filter stopwords
    filtered = [
        t for t in second_tokens
        if t.strip(" ,.;:-").lower() not in stopwords and t.strip(" ,.;:-")
    ]
    if not filtered:
        filtered = [t for t in second_tokens if t.strip(" ,.;:-")]

    secondary_letters = [t.strip(" ,.;:-")[0].upper() for t in filtered[:max_secondary]]
    secondary = "".join(secondary_letters)

    if not secondary:
        return primary
    if hyphenated:
        return f"{primary}-{secondary}"
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


