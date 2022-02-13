import copy
from view.utils.keys import ENTER, SPACE, HASHTAG

reserved_keys = {
        '<ENTER>' : ENTER,
        '<SPACE>' : SPACE,
        '#' : HASHTAG,
        }

def decode_command(values, enter_after):
    output = []
    rkeys = reserved_keys
    for word in values:
        tword = word
        while len(tword):
            found = False
            for k in rkeys:
                if tword.startswith(k):
                    tword = tword[len(k):]
                    output.append(rkeys[k])
                    found = True
                    break
            if not found:
                char = tword[0]
                output.append(ord(char))
                tword = tword[1:]

        if enter_after:
            output.append(ENTER)
    return output

