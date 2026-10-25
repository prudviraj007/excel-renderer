"""Month parsing and normalization utilities."""
import re
from datetime import datetime, date
from typing import Optional


def normalize_month(value: any) -> Optional[str]:
    """
    Convert various month representations to YYYY-MM format.
    
    Supports:
    - Excel date numbers (e.g., 44927 for 2023-01-01)
    - Python datetime/date objects
    - ISO strings: YYYY-MM, YYYY-MM-DD
    - Month names: "Jan-26", "Jan'26", "January 2026", "Oct 2026"
    - Common date strings
    
    Returns None if the value cannot be parsed as a month.
    """
    if value is None:
        return None
    
    # Handle datetime/date objects
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m')
    
    # Handle Excel date numbers (stored as float/int)
    if isinstance(value, (int, float)):
        # Excel epoch is 1899-12-30 (serial 0)
        # Common range: 40000-50000 represents ~2009-2037
        if 30000 <= value <= 60000:  # Reasonable date range
            try:
                # Excel stores dates as days since 1899-12-30
                from datetime import timedelta
                excel_epoch = datetime(1899, 12, 30)
                dt = excel_epoch + timedelta(days=int(value))
                return dt.strftime('%Y-%m')
            except:
                pass
        return None
    
    # Convert to string for pattern matching
    value_str = str(value).strip()
    if not value_str:
        return None
    
    # Try ISO format: YYYY-MM or YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}(-\d{2})?$', value_str):
        try:
            dt = datetime.strptime(value_str[:7], '%Y-%m')
            return dt.strftime('%Y-%m')
        except ValueError:
            pass
    
    # Try various month name patterns
    patterns = [
        # "Jan-26", "Jan'26" - need special handling for 2-digit years
        (r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)['\-](\d{2})$", '%b-%y'),
        # "January 2026", "Jan 2026"
        (r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})$", '%B %Y'),
        (r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})$", '%b %Y'),
        # "2026-Jan", "2026 Jan"
        (r"^(\d{4})['\-\s]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$", '%Y-%b'),
        # "10/2026", "10-2026"
        (r"^(\d{1,2})[/\-](\d{4})$", '%m-%Y'),
        # "2026/10", "2026-10"
        (r"^(\d{4})[/\-](\d{1,2})$", '%Y-%m'),
    ]
    
    for pattern, fmt in patterns:
        match = re.match(pattern, value_str, re.IGNORECASE)
        if match:
            try:
                # Reconstruct the matched string for parsing
                if fmt in ['%b-%y']:
                    # Handle 2-digit year specially
                    month_str, year_str = match.groups()
                    # Assume 20xx for years
                    year = 2000 + int(year_str)
                    dt = datetime.strptime(f"{month_str}-{year}", '%b-%Y')
                elif fmt in ['%Y-%b', '%b %Y', '%B %Y']:
                    dt = datetime.strptime(value_str, fmt)
                elif fmt == '%m-%Y':
                    month, year = match.groups()
                    dt = datetime(int(year), int(month), 1)
                elif fmt == '%Y-%m':
                    year, month = match.groups()
                    dt = datetime(int(year), int(month), 1)
                else:
                    continue
                return dt.strftime('%Y-%m')
            except (ValueError, AttributeError):
                pass
    
    # Try pandas if available for more robust parsing
    try:
        import pandas as pd
        parsed = pd.to_datetime(value_str, errors='coerce')
        if pd.notna(parsed):
            return parsed.strftime('%Y-%m')
    except ImportError:
        pass
    
    return None


# Import pandas conditionally
try:
    import pandas as pd
except ImportError:
    pd = None


def is_likely_month_value(value: any) -> bool:
    """
    Check if a value is likely to represent a month.
    More lenient than normalize_month - used for discovery.
    """
    if value is None or value == "":
        return False
    
    # Date objects
    if isinstance(value, (datetime, date)):
        return True
    
    # Excel date numbers
    if isinstance(value, (int, float)):
        return 30000 <= value <= 60000
    
    # String patterns that look like months
    value_str = str(value).strip()
    month_indicators = [
        r'\d{4}-\d{2}',  # YYYY-MM
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month abbreviations
        r'(January|February|March|April|May|June|July|August|September|October|November|December)',  # Full names
    ]
    
    for pattern in month_indicators:
        if re.search(pattern, value_str, re.IGNORECASE):
            return True
    
    return False
