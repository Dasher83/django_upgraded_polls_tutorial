from polls.models import User


def create_basic_user(return_json=False, return_plain_password=True):
    plain_password = "1234"
    user_data = {
        "username": "basic_user",
        "password": plain_password,
        "email": "",
        "first_name": "",
        "last_name": "",
    }
    User.objects.filter(username=user_data["username"]).delete()
    instance = User.create_user(**user_data)
    if return_json:
        user = user_data
    else:
        user = instance
    if return_plain_password:
        return user, plain_password
    else:
        return user
