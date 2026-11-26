import logging
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

log = logging.getLogger(__name__)

CODE_TTL = timedelta(minutes=10)
MAX_TENTATIVES = 5


def generer_code():
    return f'{secrets.randbelow(1_000_000):06d}'


def code_actif(user):
    return bool(
        user.otp_code
        and user.otp_expire
        and user.otp_expire > timezone.now()
        and user.otp_tentatives < MAX_TENTATIVES
    )


def envoyer_code(user):
    code = generer_code()
    user.otp_code = make_password(code)
    user.otp_expire = timezone.now() + CODE_TTL
    user.otp_tentatives = 0
    user.save(update_fields=['otp_code', 'otp_expire', 'otp_tentatives'])
    sujet = 'SmartWater IoT – Vérification de votre e-mail'
    texte = render_to_string('accounts/otp_email.txt', {
        'user': user,
        'code': code,
        'minutes': int(CODE_TTL.total_seconds() // 60),
    })
    send_mail(sujet, texte, None, [user.email])
    return code


def verifier_code(user, code):
    if not code_actif(user):
        return False, 'Le code a expiré. Demandez un nouveau code.'
    if check_password(code, user.otp_code):
        user.email_verifie = True
        user.otp_code = ''
        user.otp_expire = None
        user.otp_tentatives = 0
        user.save(update_fields=['email_verifie', 'otp_code', 'otp_expire', 'otp_tentatives'])
        return True, ''
    user.otp_tentatives += 1
    user.save(update_fields=['otp_tentatives'])
    if user.otp_tentatives >= MAX_TENTATIVES:
        return False, 'Trop de tentatives. Demandez un nouveau code.'
    return False, 'Code incorrect.'
