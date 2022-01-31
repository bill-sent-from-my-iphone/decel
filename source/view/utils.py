

def fix_text_to_width(message, width, alignment='l'):
    lines = []
    words = message.split(' ')
    current_line = ''
    for word in words:
        print(word)
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
