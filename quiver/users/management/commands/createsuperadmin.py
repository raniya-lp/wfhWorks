from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.hashers import make_password

from users import models as user_models


class Command(BaseCommand):
    help = 'Creates a Super Admin'

    def get_validate_email(self):
        email = None
        while True:
            email = input("Email address: ").strip()
            try:
                validate_email(email)
            except ValidationError:
                self.stdout.write(
                    self.style.ERROR_OUTPUT('Enter a valid email address.'))
                continue
            break
        return email

    def get_validate_text(self,
                          help_text: str,
                          min_length: int = 3,
                          max_length: int = 30):
        name = None
        while True:
            name = input(f"{help_text}: ").strip()
            if len(name) < min_length:
                self.stdout.write(
                    self.style.ERROR_OUTPUT(
                        f'Minimum {min_length} characters are required for {help_text.lower()}.'
                    ))
                continue
            elif len(name) > max_length:
                self.stdout.write(
                    self.style.ERROR_OUTPUT(
                        f'Maximum {max_length} characters are allowed for {help_text.lower()}.'
                    ))
                continue
            break
        return name

    def get_confirm_password(self, password1):
        password2 = input("Password (again):").strip()
        if password1 != password2:
            return False
        return True

    def create_super_admin(self, email, firstname, lastname, password1):
        user = user_models.User.objects.filter(username=email)
        if user.exists():
            return False, "Email already exists."
        password_hash = make_password(password1)

        user = user_models.User.objects.create(first_name=firstname,
                                               last_name=lastname,
                                               username=email,
                                               is_staff=True,
                                               is_superuser=True,
                                               password=password_hash)

        user_models.Role.objects.create(
            user=user, role=user_models.Role.RoleName.superadmin)

        return True, "Super Admin created successfully!"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Creating Super Admin..."))
        try:
            email = self.get_validate_email()
            firstname = self.get_validate_text("First name", 3)
            lastname = self.get_validate_text("Last name", 1)
            password1 = self.get_validate_text("Password", 8, 16)
            password2 = self.get_confirm_password(password1)
            if not password2:
                self.stdout.write(
                    self.style.ERROR_OUTPUT(
                        "Mismatched passwords. Exiting..."))
                raise SystemExit(0)

            result, message = self.create_super_admin(email, firstname,
                                                      lastname, password1)
            if result:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR_OUTPUT(message))
        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR_OUTPUT("Operation cancelled."))
