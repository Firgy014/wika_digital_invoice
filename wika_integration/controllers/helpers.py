import random
import string

def _get_wdigi_token():
    N = 28
    return ''.join(random.choices(string.ascii_letters + string.digits, k=N))
