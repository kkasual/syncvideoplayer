
def ms_to_str(l, sign_always=False):
    if not l:
        return '0'
    if l < 0:
        sign = '-'
        l = -l
    else:
        if sign_always:
            sign = '+'
        else:
            sign = ''
    mins = l // 60000
    s = (l // 1000) % 60
    ms = l % 1000
    if mins > 0:
        return '%s%02d:%02d.%03d' % (sign, mins, s, ms)
    else:
        return '%s%d.%03d' % (sign, s, ms)

def ms_to_str_full(l, sign_always=False):
    if not l:
        return '00:00.000'
    if l < 0:
        sign = '-'
        l = -l
    else:
        if sign_always:
            sign = '+'
        else:
            sign = ''

    mins = l // 60000
    s = (l // 1000) % 60
    ms = l % 1000

    return '%s%02d:%02d.%03d' % (sign, mins, s, ms)
