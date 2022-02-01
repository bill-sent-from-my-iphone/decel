

# Note: text must be less than width
def align_text(text, width, alignment='r'):
    if len(text) >= width:
        return text[:width]
    diff = width - len(text)
    if alignment == 'r':
        return ' ' * diff + text
    if alignment == 'l':
        return text + ' ' * diff
    if alignment == 'c':
        l = int(diff / 2)
        r = diff - l
        return ' ' * l + text + ' ' * r
    raise Exception("Invalid Alignment: {}".format(alignment))

    pass

def fix_text_to_width(message, width, alignment='l'):
    lines = []
    words = message.split(' ')
    current_line = ''
    for word in words:
        diff = width - len(current_line)
        if len(word) + 1 < diff:
            current_line += " {}".format(word)
        else:
            if alignment == 'l':
                current_line += ' ' * diff
            if alignment == 'r':
                current_line = ' ' * diff + current_line
            if alignment == 'c':
                first_half = int(diff/2)
                second_half = diff - first_half
                current_line = ' ' * first_half + current_line + ' ' * second_half
            lines.append(current_line)
            current_line = ''
    if current_line:
        lines.append(current_line)
    return lines
