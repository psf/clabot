import re


def normalize_email(email):
    return re.sub(r"\+[^)]*@(?!users.noreply.github.com)", "@", email).lower()
