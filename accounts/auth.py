import random
import string


def generate_password():

    password_length = 12
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ""   
    for index in range(password_length):
        password = password + random.choice(characters)

    return password