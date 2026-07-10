# ==========================================
# Text
# ==========================================

def shorten_text(
        text,
        max_length=40,
        suffix="..."
    ):
    """
    Shorten text for display.

    Example
    -------
    ABCDEFGHIJKLMNOP

    ->
    ABCDEFG...
    """

    if text is None:
        return ""

    text = str(text)

    if len(text) <= max_length:
        return text

    if max_length <= len(suffix):
        return text[:max_length]

    return (

        text[:max_length - len(suffix)]

        + suffix

    )

# ==========================================
# Response Time
# ==========================================

def format_response_time(
    response_time
):
    """
    Second

    ->

    ms
    """

    if response_time is None:

        return ""

    return f"{response_time :.3f}"

# ==========================================
# Status
# ==========================================

def format_status(status):

    if status is None:
        return ""

    return status

# ==========================================
# Payload
# ==========================================

def format_payload(
    payload,
    max_length=40
):

    return shorten_text(

        payload,

        max_length

    )


# ==========================================
# Timestamp
# ==========================================

def format_timestamp(
    timestamp
):

    if timestamp is None:

        return ""

    return f"{timestamp:.3f}"