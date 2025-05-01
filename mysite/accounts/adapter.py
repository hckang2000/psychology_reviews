from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_email_verified(self, request, email_address):
        if isinstance(email_address, EmailAddress):
            user = email_address.user
            if user.is_superuser or user.username in ['admin', 'administrator']:
                return True
        return super().is_email_verified(request, email_address) 