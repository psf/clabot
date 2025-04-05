from django import forms


class SignEmailForm(forms.Form):
    email = forms.ChoiceField(
        label="Select an email address for your signature.",
        help_text=(
            "Because you are using a GitHub noreply email address, "
            "we need you to choose one of your verified GitHub verified email addresses "
            "in order to sign."
        ),
        widget=forms.Select,
    )
