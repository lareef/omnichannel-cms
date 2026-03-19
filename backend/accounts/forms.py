# accounts/forms.py
from allauth.account.forms import LoginForm, SignupForm, ResetPasswordForm, ChangePasswordForm, ResetPasswordKeyForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from notifications.utils import notify_admins

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
    
    # def save(self, request):
    #     # Create the user using the parent method
    #     user = super().save(request)
    #     # Mark as inactive
    #     user.is_active = False
    #     user.save(update_fields=['is_active'])
    #     # Optional: Send notification to admins here
    #     # e.g., send_mail(...) or create a Notification object
    #     # Notify admins
    #     notify_admins(
    #         subject="New user registration pending approval",
    #         message=f"User {user.username} ({user.email}) has signed up and requires activation & role assignment.",
    #         related_object=user,
    #         send_email=True
    #     )
    #     return user

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

# Similar for other forms