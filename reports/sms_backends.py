"""Pluggable SMS backends. Default: console (logs, no real send)."""
import logging
import os

import requests

log = logging.getLogger(__name__)


class SMSBackend:
    name = "base"

    def send(self, phone, message):
        """Return (success: bool, response: str)."""
        raise NotImplementedError


class ConsoleBackend(SMSBackend):
    name = "console"

    def send(self, phone, message):
        log.info("[SMS console] to=%s body=%s", phone, message)
        print(f"[SMS console] -> {phone}: {message}")
        return True, "console-ok"


class AfricasTalkingBackend(SMSBackend):
    name = "africastalking"

    def __init__(self):
        self.username = os.environ.get("AT_USERNAME", "")
        self.api_key = os.environ.get("AT_API_KEY", "")
        self.sender = os.environ.get("AT_SENDER_ID", "")
        self.url = "https://api.africastalking.com/version1/messaging"

    def send(self, phone, message):
        if not self.username or not self.api_key:
            return False, "Africa's Talking credentials not configured"
        headers = {
            "apiKey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {"username": self.username, "to": phone, "message": message}
        if self.sender:
            data["from"] = self.sender
        try:
            r = requests.post(self.url, headers=headers, data=data, timeout=20)
            ok = r.status_code in (200, 201)
            return ok, r.text[:500]
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


def get_backend():
    """Read SMS_BACKEND from env. Defaults to console."""
    which = (os.environ.get("SMS_BACKEND") or "console").lower()
    if which == "africastalking":
        return AfricasTalkingBackend()
    return ConsoleBackend()