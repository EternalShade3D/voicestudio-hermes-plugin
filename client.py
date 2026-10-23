"""VoiceStudio HTTP layer - stdlib only, no VS semantics here.

Transport rules:
- base URL from plugin settings, default http://127.0.0.1:3900
- short connect/probe timeout, long read timeout for generation
- /generate is form-encoded (JSON gets a 422); the response body is the audio bytes
- /v1/audio/speech is NOT used: it is the OpenAI-protocol route and is
  non-deterministic for this app (same request produced three different voices)
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "http://127.0.0.1:3900"
PROBE_TIMEOUT_S = 3
DEFAULT_READ_TIMEOUT_S = 180
SETUP_STATUS_PATH = "/setup/status"
PROFILES_PATH = "/profiles"
GENERATE_PATH = "/generate"

_VOICES_TTL_S = 60
_voices_cache = {"key": None, "at": 0.0, "voices": []}


def normalize_base_url(raw, default=DEFAULT_BASE_URL):
    """Clean base URL with no trailing slash."""
    if not raw or not str(raw).strip():
        return default
    return str(raw).strip().rstrip("/")


def _decode(body):
    if isinstance(body, bytes):
        try:
            return body.decode("utf-8")
        except Exception:
            return body.decode("utf-8", errors="replace")
    return body


def api_get(base_url, path, timeout=PROBE_TIMEOUT_S):
    """GET path; returns {status, body, headers} or {error, kind}. Never raises."""
    url = normalize_base_url(base_url) + path
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": resp.status, "body": resp.read(),
                    "headers": {k.lower(): v for k, v in resp.headers.items()}}
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return {"status": e.code, "body": body, "headers": {}, "error": "http_%d" % e.code}
    except Exception as e:
        return {"error": str(e), "kind": type(e).__name__}


def api_post_form(base_url, path, fields, timeout=DEFAULT_READ_TIMEOUT_S):
    """POST application/x-www-form-urlencoded; returns the same envelope shape. Never raises."""
    url = normalize_base_url(base_url) + path
    data = urllib.parse.urlencode({k: v for k, v in (fields or {}).items() if v is not None}).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": resp.status, "body": resp.read(),
                    "headers": {k.lower(): v for k, v in resp.headers.items()}}
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return {"status": e.code, "body": body, "headers": {}, "error": "http_%d" % e.code}
    except Exception as e:
        return {"error": str(e), "kind": type(e).__name__}


def is_available(base_url, timeout=PROBE_TIMEOUT_S):
    """Availability probe: GET /setup/status answering 200 within ~3 s."""
    r = api_get(base_url, SETUP_STATUS_PATH, timeout=timeout)
    return r.get("status") == 200


def looks_like_wav(body):
    """True when bytes are RIFF....WAVE, which is what this app returns."""
    return isinstance(body, (bytes, bytearray)) and body[:4] == b"RIFF" and body[8:12] == b"WAVE"


def list_profiles(base_url, timeout=PROBE_TIMEOUT_S):
    """Saved voices from GET /profiles. Returns [] on any failure."""
    r = api_get(base_url, PROFILES_PATH, timeout=timeout)
    if r.get("status") != 200:
        return []
    try:
        payload = json.loads(_decode(r.get("body") or b""))
    except Exception:
        return []
    items = payload.get("profiles") if isinstance(payload, dict) else payload
    return [p for p in (items or []) if isinstance(p, dict) and p.get("id")]


def _gender(profile):
    """Gender from the profile's vd_states JSON blob (it is a string, not a dict)."""
    raw = profile.get("vd_states")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return ""
    if isinstance(raw, dict):
        return str(raw.get("Gender") or "").lower()
    return ""


def list_voices_cached(base_url, ttl=_VOICES_TTL_S, force=False):
    """Cached voice catalog so a warm loop does not re-hit the app on every reply."""
    key = normalize_base_url(base_url)
    now = time.time()
    cache = _voices_cache
    if not force and cache["key"] == key and (now - cache["at"]) < ttl and cache["voices"]:
        return cache["voices"]
    voices = [{"id": p["id"], "display": p.get("name") or p["id"],
               "language": p.get("language") or "",
               "gender": _gender(p)} for p in list_profiles(base_url)]
    if voices:
        cache.update({"key": key, "at": now, "voices": voices})
    return cache["voices"] if cache["key"] == key else voices


def resolve_voice(base_url, name, timeout=PROBE_TIMEOUT_S):
    """Resolve a voice name to its id. Ids pass through unchanged; names are looked up.

    The app accepts a profile name in place of the id, but an id always wins, so
    resolving here keeps behaviour identical to the app panel and gives a clear
    error instead of speaking the wrong voice.
    """
    if not name:
        return None
    name = str(name).strip()
    if len(name) == 8 and all(c in "0123456789abcdef" for c in name.lower()):
        return name
    for p in list_profiles(base_url, timeout=timeout):
        if (p.get("name") or "").strip().lower() == name.lower():
            return p.get("id")
    return None


def generate(base_url, text, profile_id, engine="", timeout=DEFAULT_READ_TIMEOUT_S):
    """POST /generate; returns transport envelope. Body is the audio bytes."""
    fields = {"text": text, "profile_id": profile_id}
    if engine:
        fields["engine"] = engine
    return api_post_form(base_url, GENERATE_PATH, fields, timeout=timeout)
