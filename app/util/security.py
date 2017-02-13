import random
import string

def generate_random_csrf_string(n=10, chars=string.letters+string.digits):
    return ''.join(random.SystemRandom().choice(chars) for _ in range(n))
