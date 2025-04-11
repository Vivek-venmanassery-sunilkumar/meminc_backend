
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail
from django.conf import settings

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):

    # the below like concatinates your websites reset password url and the reset email token which will be required at a later stage
    reset_url= f"https://www.meminc.store/reset-password/?token={reset_password_token.key}"
    print('user email to send link', reset_password_token.user.email)
    
    email_plaintext_message = f"""
    Hai guys,
    You have requested to reset your password. Please click the link below to reset your password:
    {reset_url}

    If you didn't requeste this password reset, please ignore this email.

    Best regards,
    MEMInc Team
    """
    send_mail(
        subject="Password Reset for MEMInc Account.",
        message = email_plaintext_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reset_password_token.user.email],
        fail_silently=False,
    )