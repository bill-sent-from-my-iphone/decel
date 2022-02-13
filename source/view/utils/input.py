
from .keys import *


class BasicInput:

    def __init__(self, on_confirm=None, on_cancel=None):
        self.text = ''
        self.cursor = 0
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

    def cancel(self):
        if self.on_cancel:
            self.on_cancel()

    def confirm(self):
        if self.on_confirm:
            self.on_confirm()

    def clear(self):
        self.text = ''
        self.cursor = 0

    def process_text(self, text):
        for c in text:
            self.process_char(ord(c))

    def process_char(self, charval):
        inp = self.text
        pos = self.cursor
        pre_cursor = inp[:pos]
        post_cursor = inp[pos:]

        if charval == ESCAPE:
            self.cancel()
        elif charval == LEFT:
            ncursor = pos - 1
            if ncursor >= 0:
                self.cursor = ncursor
        elif charval == RIGHT:
            ncursor = pos + 1
            if ncursor <= len(self.text):
                self.cursor = ncursor
            pass
        elif charval == BACKSPACE:
            pre_cursor = pre_cursor[:-1]
            self.cursor -= 1
            self.text = pre_cursor + post_cursor
        elif charval == ENTER:
            self.confirm()
        else:
            self.text = pre_cursor + chr(charval) + post_cursor
            self.cursor += 1

