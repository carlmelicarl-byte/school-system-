import functools
import hmac
import secrets
from urllib.parse import urljoin, urlparse

from flask import abort, g, redirect, request, session, url_for


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf():
    expected = session.get("_csrf_token", "")
    supplied = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.full_path))
        return view(**kwargs)

    return wrapped_view


def roles_required(*roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))
            if g.user["role"] not in roles:
                abort(403)
            return view(**kwargs)

        return wrapped_view

    return decorator


def is_safe_redirect(target):
    if not target:
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ("http", "https") and host_url.netloc == redirect_url.netloc
