from django.db import IntegrityError, transaction

from .models import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
)


def create_notification(
    *,
    school,
    recipient,
    title,
    message,
    category=Notification.Category.SYSTEM,
    idempotency_key=None,
):
    if recipient.school_id and recipient.school_id != school.pk:
        raise ValueError("The notification recipient belongs to another school.")

    with transaction.atomic():
        if idempotency_key:
            try:
                notification, created = Notification.unfiltered_objects.get_or_create(
                    school=school,
                    idempotency_key=idempotency_key,
                    defaults={
                        "recipient": recipient,
                        "title": title,
                        "message": message,
                        "category": category,
                    },
                )
            except IntegrityError:
                notification = Notification.unfiltered_objects.get(
                    school=school, idempotency_key=idempotency_key
                )
                created = False
        else:
            notification = Notification.unfiltered_objects.create(
                school=school,
                recipient=recipient,
                title=title,
                message=message,
                category=category,
            )
            created = True

        if not created:
            return notification, False

        preferences, _ = NotificationPreference.unfiltered_objects.get_or_create(
            school=school,
            user=recipient,
        )
        deliveries = []
        if preferences.email_enabled and recipient.email:
            deliveries.append(
                NotificationDelivery(
                    notification=notification,
                    channel=NotificationDelivery.Channel.EMAIL,
                    destination=recipient.email,
                )
            )
        if preferences.sms_enabled and recipient.phone_number:
            deliveries.append(
                NotificationDelivery(
                    notification=notification,
                    channel=NotificationDelivery.Channel.SMS,
                    destination=recipient.phone_number,
                )
            )
        NotificationDelivery.unfiltered_objects.bulk_create(deliveries)

    return notification, True




"""Notification services — email + SMS with graceful fallbacks.

If credentials aren't configured, requests are logged to NotificationDelivery
with status=PENDING so they can be retried once credentials exist.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def email_configured():
    """Return True if SMTP is configured (EMAIL_HOST set)."""
    return bool(getattr(settings, "EMAIL_HOST", ""))


def sms_configured():
    """Return True if Africa's Talking is configured."""
    return bool(
        getattr(settings, "AFRICASTALKING_USERNAME", "")
        and getattr(settings, "AFRICASTALKING_API_KEY", "")
    )


def send_email(to, subject, body):
    """Send email via Django's configured backend. Returns (success, info)."""
    if not to:
        return False, "No recipient email."
    if not email_configured():
        logger.warning("Email not configured. Would have sent: %s -> %s", subject, to)
        return False, "Email not configured."
    try:
        sent = send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to],
            fail_silently=False,
        )
        return bool(sent), "Sent."
    except Exception as e:
        logger.exception("Email failed: %s", e)
        return False, str(e)


def send_sms(phone, message):
    """Send SMS via Africa's Talking. Returns (success, info)."""
    if not phone:
        return False, "No phone number."
    if not sms_configured():
        logger.warning("SMS not configured. Would have sent: %s -> %s", message[:50], phone)
        return False, "SMS not configured."
    try:
        import africastalking
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY,
        )
        sms = africastalking.SMS
        response = sms.send(
            message,
            [phone],
            sender_id=getattr(settings, "AFRICASTALKING_SENDER_ID", None) or None,
        )
        logger.info("SMS response: %s", response)
        return True, "Sent."
    except Exception as e:
        logger.exception("SMS failed: %s", e)
        return False, str(e)


# ---- Delivery record helpers ----

def _save_delivery(student, channel, target, message, subject, success, info):
    """Save a NotificationDelivery record. Best effort, never raises."""
    try:
        from .models import Notification, NotificationDelivery
    except Exception:
        logger.warning("Notification models not importable. Skipping save.")
        return None

    try:
        notification, _ = Notification.objects.get_or_create(
            school=student.school,
            title=subject or f"{channel.upper()} notification",
            defaults={
                "message": message[:5000],
            },
        )

        delivery = NotificationDelivery.objects.create(
            notification=notification,
            channel=channel,
            recipient=target,
            status=(
                NotificationDelivery.Status.SENT
                if success
                else NotificationDelivery.Status.PENDING
            ),
            sent_at=timezone.now() if success else None,
            error_message="" if success else info,
        )
        return delivery
    except Exception:
        logger.exception("Failed to save delivery record.")
        return None


def notify_parent(student, subject, message, channels=("email", "sms")):
    """Notify the parent of a student via the requested channels."""
    parent = student.parent_guardian
    email = getattr(parent, "email", None) or None
    phone = getattr(parent, "phone_number", None) or student.parent_contact or None

    results = {}

    if "email" in channels:
        ok, info = send_email(email, subject, message)
        _save_delivery(student, "email", email or "", message, subject, ok, info)
        results["email"] = (ok, info)

    if "sms" in channels:
        ok, info = send_sms(phone, f"{subject}\n{message}")
        _save_delivery(student, "sms", phone or "", message, subject, ok, info)
        results["sms"] = (ok, info)

    return results
