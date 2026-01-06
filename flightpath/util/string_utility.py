#import json
import string

class StringUtility:

    @classmethod
    def sanitize_json(cls, text:str) -> bool:
        # Create a translation table to remove all control characters (0 to 31)
        # except for the standard JSON allowed ones: \n, \r, \t, and the space (32)
        # Note: Newlines, tabs, etc. must be escaped in JSON strings,
        # so here we strip the *literal* control characters from the raw input.
        control_chars = ''.join(map(chr, range(0,32)))
        # Allowed whitespace in JSON outside of strings are tab, newline, carriage return, and space.
        # But *inside* a string literal, they must be escaped.
        # This function removes all literal control characters to ensure the string is clean.
        text = text.translate(str.maketrans('', '', control_chars))
        return text


