import re

try:
    import rookiepy
except ImportError:
    rookiepy = None

# this dictionary holds language name as key and corresponding ISO language code as value
LANG_NAME_TO_CODE_MAPPING = {
    "Arabic": "ar",
    "Afrikaans": "af",
    "Bangla": "bn",
    "Burmese": "my",
    "Chinese (Simplified)": "zh-Hans",
    "Chinese (Traditional)": "zh-Hant",
    "Chinese": "zh-CN",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "Finnish": "fi",
    "Greek": "el",
    "Hindi": "hi",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Malay": "ml",
    "Malayalam": "ml",
    "Portugese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Tamil": "ta",
    "Telegu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Urdu": "ur",
    "Vietnamese": "vi",
    "-ALL AVAILABLE": "all",
    "-NONE": "",
}

ALLOWED_BROWSERS = ["edge", "firefox", "brave"]

COURSERA_LEARN_RE = re.compile(r"coursera\.org/learn/([a-zA-Z0-9_\-]+)", re.IGNORECASE)
SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
EDX_COURSE_KEY_RE = re.compile(
    r"^course-v1:([a-zA-Z0-9_\-\.]+)[\+]([a-zA-Z0-9_\-\.]+)[\+]([a-zA-Z0-9_\-\.]+)$"
)
EDX_LEGACY_KEY_RE = re.compile(
    r"^([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)$"
)


def extract_slug_from_url(url_or_slug: str, strict: bool = False) -> str:
    """Extract canonical course slug from URL or validate slug string.

    If strict is True, raises ValueError if the input is not a valid Coursera learn URL or slug.
    If strict is False, returns empty string on failure.
    """
    target = url_or_slug.strip() if url_or_slug else ""
    if not target:
        if strict:
            raise ValueError("Empty course URL or slug provided.")
        return ""

    # 1. If it's a URL
    if target.startswith("http://") or target.startswith("https://"):
        match = COURSERA_LEARN_RE.search(target)
        if match:
            return match.group(1).lower()
        if strict:
            raise ValueError(
                f"Invalid Coursera URL: {url_or_slug}. "
                "Expected format: https://www.coursera.org/learn/course-name"
            )
        return ""

    # 2. If it's a plain slug
    if SLUG_PATTERN.match(target):
        return target.lower()

    if strict:
        raise ValueError(
            f"Invalid Coursera course identifier: {url_or_slug}. "
            "Expected slug or https://www.coursera.org/learn/course-name"
        )
    return ""


# extract class name from course home page url
def urltoclassname(homepageurl):
    """Extract class name from course home page url or slug. Returns empty string if invalid."""
    return extract_slug_from_url(homepageurl, strict=False)


def detect_platform(identifier_or_url: str) -> str:
    """Detect whether an identifier or URL belongs to Coursera or edX."""
    raw = identifier_or_url.strip() if identifier_or_url else ""
    if not raw:
        return "unknown"
    raw_lower = raw.lower()
    if "coursera.org/learn/" in raw_lower:
        return "coursera"
    if "learning.edx.org" in raw_lower or "courses.edx.org" in raw_lower or "edx.org" in raw_lower:
        return "edx"
    if EDX_COURSE_KEY_RE.match(raw) or EDX_LEGACY_KEY_RE.match(raw):
        return "edx"
    return "unknown"


def loadcauth(domain: str, browser: str):
    """this function returns the cauth code of browser for the specified domain.

    args:
        browser - must be in the ALLOWED_BROWSERS list

    example use: loadcauth('coursera.org').
    """
    if browser not in ALLOWED_BROWSERS:
        print(
            f"Browser not supported. Please login on one of these browsers: {', '.join(ALLOWED_BROWSERS)}"
        )
        return ""

    import cookies
    try:
        cj = cookies.load_cookies_from_browser(browser, domain=domain)
        for c in cj:
            if c.name == "CAUTH":
                return c.value
        return ""
    except Exception as e:
        print(f"Error fetching cookies: {e}")
        print("Could not fetch authentication. Maybe run the app as administrator.")
        return ""


def move_to_first(dictionary, key):
    if key not in dictionary:
        return dictionary  # Key not found, no changes needed

    value = dictionary[key]
    # Create a new dictionary with the desired key-value pair as the first item
    new_dict = {key: value}

    for k, v in dictionary.items():
        if k != key:
            # Insert the remaining key-value pairs into the new dictionary
            new_dict[k] = v

    return new_dict


# testing urltoclassname function
# url = "https://www.coursera.org/learn/model-thinking"
# url = "https://www.coursera.org/learn/model-thinking/home/week/1"
# url = "https://www.coursera.org/learn/neural-networks-deep-learning?specialization=deep-learning"
# url = "https://www.coursera.org/learn/java-programming-recommender/home/week/1https://www.coursera.org/learn/java-programming-recommender/home/week/1"
# url = "model-thinking-hell"
# url = "model-thinking?"
# cn = urltoclassname(url)
# print(cn)
if __name__ == "__main__":
    ca = loadcauth("coursera.org", browser="opera_gx")
    print(ca)
