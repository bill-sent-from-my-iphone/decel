
import curses

from .window import Window
from .utils import fix_text_to_width


class Popup(Window):

    '''
        title - title of popup
        message - message
        height - height of popup
        width - width of popup
        actions - list of actions. eg: [('O', 'Okay', confirm_func), ('C', 'Cancel', deny_func)]
                  key to press, name of button, function to call
    '''

    def __init__(self, title, message, height=None, width=None,
                 actions=None, parent=None, colors=None):
        if not actions:
            actions = []
            actions.append(('O', 'Ok', lambda:None))
            actions.append(('C', 'Cancel', lambda:None))
        self.actions = actions
        if not height:
            height = int(parent.height * (0.4))
        if not width:
            width = int(parent.width * (0.4))

        row = int((parent.height - height) / 2)
        col = int((parent.width - width) / 2)

        self.title = title
        self.message = message
        super().__init__(col, row, height, width, parent=parent, colors=colors)
        self.create_body()

    def create_body(self):
        mod = self.colors.get_color_id("Red", "Green")
        self.draw_border(modifier=mod)
        self.draw_title(self.title, modifier=mod)

        button_len = min([12, max([len(i[1]) for i in self.actions])]) + 2
        buttons_per_row = int(self.width / button_len)

        top_of_button = self.height - 4
        button_col = self.width

        for char, body, action in self.actions:
            b_text = body + " ({})".format(char)
            button_col = button_col - (len(b_text) + 5)
            self.draw_button(button_col, top_of_button, b_text)

        text_height = self.height - 11
        self.draw_text_box(self.message, 4, 3, text_height, self.width - 4)
        
        body_lines = fix_text_to_width(self.message, self.width, alignment='l')

        empty_lines = 1
        #for r in range(len(body_lines))


