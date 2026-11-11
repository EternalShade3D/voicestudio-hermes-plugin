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


def describe_failure(result, base_url="", timeout=None, voice=""):
    """One short sentence a person can act on, for an envelope from api_get/api_post_form.

    The app's own 500 body is a JSON paragraph of advice; pasting it into a toast is useless.
    """
    kind = str(result.get("kind") or "")
    err = str(result.get("error") or "")
    status = result.get("status")
    body = _decode(result.get("body") or b"") if result.get("body") else ""
    low = body.lower()

    if not status:
        if "timed out" in err.lower() or kind == "TimeoutError":
            return ("VoiceStudio did not answer in time%s. It may still be loading a voice; "
                    "increase the timeout or try again."
                    % (" (%ss)" % timeout if timeout else ""))
        return ("VoiceStudio is not running, or not reachable at %s. Open VoiceStudio and try again."
                % (normalize_base_url(base_url) or "the configured address"))

    if status == 500 and ("gpu" in low or "oom" in low or "out of memory" in low):
        return ("VoiceStudio ran out of graphics memory. Try freeing VRAM and closing heavy "
                "apps, or change VoiceStudio Settings.")
    if status == 500 and ("model" in low and "load" in low):
        return "VoiceStudio could not load the voice model. Try again, or pick a smaller engine in the app."
    if status == 404:
        return ("VoiceStudio did not recognize the voice: %s. Run /voicestudio refresh, "
                "then pick a valid voice." % (voice or "you selected"))
    if status >= 500:
        return "VoiceStudio reported an internal error (HTTP %s). Check its own log or restart it." % status
    return "VoiceStudio refused the request (HTTP %s)." % status


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


def _fetch_profiles(base_url, timeout=PROBE_TIMEOUT_S):
    """Fetch saved voices; return [] for a valid empty result and None on request/parse failure."""
    r = api_get(base_url, PROFILES_PATH, timeout=timeout)
    if r.get("status") != 200:
        return None
    try:
        payload = json.loads(_decode(r.get("body") or b""))
    except Exception:
        return None
    items = payload.get("profiles") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return None
    return [p for p in items if isinstance(p, dict) and p.get("id")]


def list_profiles(base_url, timeout=PROBE_TIMEOUT_S):
    """Saved voices from GET /profiles. Returns [] on any failure."""
    return _fetch_profiles(base_url, timeout=timeout) or []


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
    if not force and cache["key"] == key and (now - cache["at"]) < ttl:
        return cache["voices"]
    profiles = _fetch_profiles(base_url)
    if profiles is None:
        # A forced refresh must report failure instead of presenting the stale cache as fresh.
        if force:
            return []
        return cache["voices"] if cache["key"] == key else []
    voices = [{"id": p["id"], "display": p.get("name") or p["id"],
               "language": p.get("language") or "",
               "gender": _gender(p)} for p in profiles]
    cache.update({"key": key, "at": now, "voices": voices})
    return voices


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
