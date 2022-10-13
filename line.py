from numpy import character


class Line:
    ''' A class representing a line of dialogue spoken by a character in a script '''

    def __init__(self, character, line):
        '''
        Parameters:
            character (string) that says the line
            line (string) that is said
        '''

        self.character = character
        self.line = line

    def to_string(self):
        ''' Returns a string describing this instance '''
        return "{}: {}".format(self.character.upper(), self.line)
