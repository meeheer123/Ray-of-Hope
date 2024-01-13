from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = session.get('user_role')  # Get the user role from the session
        if user_role == "helpee" and "user_id" not in session:
            return redirect("/sign_in_helpee")
        elif user_role == "helper" and "helper_user_id" not in session:
            return redirect("/sign_in_helper")
        return f(*args, **kwargs)

    return decorated_function
