
from math import log

CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def get_digit(x, i, n=10):
    return x // n**i % n

def get_num_digits(x, n=10):
    if x > 0:
        digits = int(log(x, n)) + 1
    elif x == 0:
        digits = 1
    else:
        digits = int(log(-x, n)) + 2
    return digits

def identification_string(x, chars=None):
    string = ''
    if chars is None:
        chars = '0123456789'
    n = len(chars)
    for i in range(get_num_digits(x, n)):
        d = get_digit(x, i, n)
        string = chars[d] + string
    return string

if __name__ == '__main__':
    for i in range(1000):
        print(identification_string(i, 'abcde'), end='  ')