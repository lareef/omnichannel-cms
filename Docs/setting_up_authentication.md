Below is a complete guide to setting up authentication with django-allauth, a custom user model, and crispy-tailwind for beautifully styled forms. All code is ready to copy into your project.

1. Install Required Packages
Make sure these are in your requirements.txt (or installed via pip):

text
django-allauth==0.61.1
django-crispy-forms==2.3
crispy-tailwind==2.0
2. Settings (settings.py)
Add the following to your Django settings. Adjust paths as needed.

python
# ======================
# AUTHENTICATION & USERS
# ======================
AUTH_USER_MODEL = 'accounts.User'

# django-allauth
INSTALLED_APPS += [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',  # optional – remove if not using social login
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # or 'username', 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # or 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/'          # after logout
LOGIN_REDIRECT_URL = '/dashboard/'         # after login
LOGIN_URL = '/accounts/login/'

# Allauth forms – point to your custom forms (see next step)
ACCOUNT_FORMS = {
    'login': 'accounts.forms.CustomLoginForm',
    'signup': 'accounts.forms.CustomSignupForm',
    'change_password': 'accounts.forms.CustomChangePasswordForm',
    'reset_password': 'accounts.forms.CustomResetPasswordForm',
    'reset_password_from_key': 'accounts.forms.CustomResetPasswordKeyForm',
}

# ======================
# CRISPY FORMS (TAILWIND)
# ======================
INSTALLED_APPS += [
    'crispy_forms',
    'crispy_tailwind',
]
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'
3. Custom User Model (accounts/models.py)
Ensure your User model includes the get_initials property used in templates:

python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # ... your existing fields (role, department, etc.) ...
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    is_active_employee = models.BooleanField(default=True)

    @property
    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()

    def __str__(self):
        return self.get_full_name() or self.username
4. Custom Allauth Forms with Crispy Helpers (accounts/forms.py)
Create this file in your accounts app. It contains styled versions of allauth’s built‑in forms.

python
from allauth.account.forms import (
    LoginForm,
    SignupForm,
    ChangePasswordForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('login', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('password', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('remember'),
            Submit('submit', 'Sign In', css_class='bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('email', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('username', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('password1', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('password2', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Submit('submit', 'Sign Up', css_class='bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )


class CustomChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('oldpassword', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('password1', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('password2', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Submit('submit', 'Change Password', css_class='bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )


class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('email', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Submit('submit', 'Reset Password', css_class='bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('password1', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('password2', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Submit('submit', 'Set New Password', css_class='bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )
5. Template Overrides for Allauth Pages
Create the following templates inside templates/account/. Each template uses {% crispy form %} to render the styled form.

templates/account/login.html
html
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block content %}
<div class="max-w-md mx-auto py-12">
    <h2 class="text-2xl font-bold mb-6">Sign In</h2>
    {% crispy form %}
    <p class="mt-4">
        <a href="{% url 'account_reset_password' %}" class="text-indigo-600">Forgot password?</a> |
        <a href="{% url 'account_signup' %}" class="text-indigo-600">Create account</a>
    </p>
</div>
{% endblock %}
templates/account/signup.html
html
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block content %}
<div class="max-w-md mx-auto py-12">
    <h2 class="text-2xl font-bold mb-6">Sign Up</h2>
    {% crispy form %}
    <p class="mt-4">
        Already have an account? <a href="{% url 'account_login' %}" class="text-indigo-600">Sign In</a>
    </p>
</div>
{% endblock %}
templates/account/logout.html
html
{% extends 'base.html' %}

{% block content %}
<div class="max-w-md mx-auto py-12 text-center">
    <h2 class="text-2xl font-bold mb-4">Sign Out</h2>
    <p class="mb-6">Are you sure you want to sign out?</p>
    <form method="post" action="{% url 'account_logout' %}">
        {% csrf_token %}
        <button type="submit" class="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700">Sign Out</button>
        <a href="/" class="ml-2 bg-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-400">Cancel</a>
    </form>
</div>
{% endblock %}
templates/account/password_change.html
html
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block content %}
<div class="max-w-md mx-auto py-12">
    <h2 class="text-2xl font-bold mb-6">Change Password</h2>
    {% crispy form %}
    <p class="mt-4">
        <a href="{% url 'account_reset_password' %}" class="text-indigo-600">Forgot password?</a>
    </p>
</div>
{% endblock %}
templates/account/password_reset.html
html
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block content %}
<div class="max-w-md mx-auto py-12">
    <h2 class="text-2xl font-bold mb-6">Reset Password</h2>
    <p class="mb-4">Enter your email address and we'll send you a link to reset your password.</p>
    {% crispy form %}
    <p class="mt-4">
        <a href="{% url 'account_login' %}" class="text-indigo-600">Back to login</a>
    </p>
</div>
{% endblock %}
Create similarly for password_reset_done.html, password_reset_from_key.html, password_reset_from_key_done.html, and email.html as needed. All follow the same pattern.

6. Update base.html to Show User Status
Make sure your navigation bar includes login/logout links and a user dropdown (already covered earlier). A minimal example:

html
<div class="flex items-center space-x-4">
    {% if user.is_authenticated %}
        <span class="text-sm text-gray-700">{{ user.get_full_name|default:user.username }}</span>
        <a href="{% url 'dashboard' %}" class="text-gray-500 hover:text-gray-700">Dashboard</a>
        <a href="{% url 'account_logout' %}" class="text-gray-500 hover:text-gray-700">Logout</a>
    {% else %}
        <a href="{% url 'account_login' %}" class="text-gray-500 hover:text-gray-700">Login</a>
        <a href="{% url 'account_signup' %}" class="text-gray-500 hover:text-gray-700">Sign Up</a>
    {% endif %}
</div>
7. Final Steps
Run migrations: python manage.py migrate

Restart your development server (or Docker containers).

Visit /accounts/login/ – you should see beautifully styled forms.

If you still encounter the AttributeError, double‑check that:

The class name in accounts/forms.py matches the one in ACCOUNT_FORMS.

The file is saved and the server is restarted.

There are no syntax errors in forms.py.

Now your authentication system is fully integrated with crispy Tailwind forms and ready for production.

🔐 Authentication & Account Management Templates
Template File	Purpose	Typical URL
login.html	Login form	/accounts/login/
signup.html	Registration form	/accounts/signup/
logout.html	Logout confirmation page	/accounts/logout/
password_change.html	Change password form	/accounts/password/change/
password_change_done.html	Success page after password change	/accounts/password/change/done/
password_reset.html	Password reset request form	/accounts/password/reset/
password_reset_done.html	Email sent confirmation	/accounts/password/reset/done/
password_reset_from_key.html	Set new password using reset key	/accounts/password/reset/key/<uidb36>-<key>/
password_reset_from_key_done.html	Password reset completed	/accounts/password/reset/key/done/
email.html	Email address management	/accounts/email/
email_confirm.html	Confirm email address	/accounts/confirm-email/<key>/
account_inactive.html	Message when account is inactive	/accounts/inactive/
verified_email_required.html	Message requiring verified email	/accounts/confirm-email/
login_code.html (if using login codes)	Code verification	/accounts/login/code/
login_code_confirm.html	Confirm login code	/accounts/login/code/confirm/
reauthenticate.html	Re‑authentication form	/accounts/reauthenticate/
📁 Social Account Templates (if using social login)
If you also use django-allauth.socialaccount, you may want to override:

Template File	Purpose
socialaccount/login_cancelled.html	Login cancelled by provider
socialaccount/login_error.html	Error during social login
socialaccount/signup.html	Social signup form
socialaccount/connections.html	Manage social account connections
socialaccount/authentication_error.html	Authentication error
✏️ Basic Template Example (login.html)
Create templates/account/login.html with:

html
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block content %}
<div class="max-w-md mx-auto py-12">
    <h2 class="text-2xl font-bold mb-6">Sign In</h2>
    {% crispy form %}
    <p class="mt-4">
        <a href="{% url 'account_reset_password' %}" class="text-indigo-600">Forgot password?</a> |
        <a href="{% url 'account_signup' %}" class="text-indigo-600">Create account</a>
    </p>
</div>
{% endblock %}
Repeat similarly for other templates, adjusting headings and links as needed.

⚙️ Important: Custom Forms
To make crispy work with allauth, you need to attach a FormHelper to each form. You can do this either by:

Defining custom form classes and setting ACCOUNT_FORMS in settings.py (as shown in the previous answer), or

Manually attaching a helper in the view – but that’s more complex.

The easiest way is to create custom forms with helpers and point allauth to them via ACCOUNT_FORMS. For example:

python
# accounts/forms.py
from allauth.account.forms import LoginForm, SignupForm, ResetPasswordForm, ChangePasswordForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            Field('login', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('password', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('remember'),
            Submit('submit', 'Sign In', css_class='bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )

# Similar for other forms
Then in settings.py:

python
ACCOUNT_FORMS = {
    'login': 'accounts.forms.CustomLoginForm',
    'signup': 'accounts.forms.CustomSignupForm',
    'reset_password': 'accounts.forms.CustomResetPasswordForm',
    'change_password': 'accounts.forms.CustomChangePasswordForm',
    # etc.
}
Now you have all the template names and the method to apply crispy styling. Override them one by one to achieve a consistent, polished look across your authentication pages.

