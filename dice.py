import random
import re

pat = '\d{1,2}d\d{1,3}|\d{1,2}D\d{1,3}'
sp_pat = 'd|D'

def judge(msg):
    repat = re.compile(pat)
    result = repat.fullmatch(msg)
    if result is not None:
        return True
    else:
        return False

def splitD(msg):
    return re.split(sp_pat, msg)

def role(msg):
    result = []
    sum = 0
    role_i = splitD(msg)
    role_c = int(role_i[0])
    nDice = int(role_i[1])

    for i in range(role_c):
        tmp = random.randint(1, nDice)
        result.append(tmp)
        sum = sum + tmp

    is1dice = True if role_c == 1 else False

    return result, sum, is1dice

def nDn(msg):
    if judge(msg):
        result, sum, is1dice = role(msg)
        if is1dice:
            return msg, sum
        else:
            return msg, result, sum
    else:
        return None