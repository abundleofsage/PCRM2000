import re
import datetime

def is_valid_date(date_string):
    """
    Validates that a date string is in YYYY-MM-DD format.
    """
    if not date_string:
        return True # Allow empty date
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def is_valid_email(email):
    """
    Validates the format of an email address.
    """
    if not email:
        return True # Allow empty email
    # A simple regex for basic email validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None
