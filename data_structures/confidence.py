
def reg_or(a, *b):
    args = [a, *b]
    result = a
    for i in range(1, len(args)):
        result = result + args[i] - (result * args[i])
    return result

def reg_and(a, *b):
    args = [a, *b]
    result = a
    for i in range(1, len(args)):
        result = result * args[i]
    return result

def neg_or(a, *b):
    return -reg_and(*[-x for x in [a, *b]])

def neg_and(a, *b):
    return -reg_or(*[-x for x in [a, *b]])

def or_conf(a, *b):
    args = [a, *b]
    if any([x >= 0 for x in args]):
        return reg_or(*[max(0, x) for x in args])
    else:
        return neg_or(*args)

def and_conf(a, *b):
    args = [a, *b]
    if all([x >= 0 for x in args]):
        return reg_and(*args)
    else:
        return neg_and(*[min(0, x) for x in args])