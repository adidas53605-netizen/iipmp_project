import re
from django.core.exceptions import ValidationError

class ComplexPasswordValidator:
    """
    Validator enforcing minimum 8 characters, at least one uppercase letter,
    one lowercase letter, one digit, and one special character.
    """
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                "Password must be at least 8 characters long.",
                code='password_too_short',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Password must contain at least one uppercase letter (A-Z).",
                code='password_no_uppercase',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                "Password must contain at least one lowercase letter (a-z).",
                code='password_no_lowercase',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                "Password must contain at least one numeric digit (0-9).",
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "Password must contain at least one special character (e.g. !@#$%^&*).",
                code='password_no_symbol',
            )

    def get_help_text(self):
        return (
            "Your password must be at least 8 characters long and include "
            "at least one uppercase letter, one lowercase letter, one numeric digit, "
            "and one special character (!@#$%^&*)."
        )
