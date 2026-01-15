import json
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

    @classmethod
    def jsonl_text_to_list(cls, text:str) -> list[str]:
        #
        # this is a slow but effective way to do it. to go faster we'd
        # want to actually parse the JSON, but for most purposes we won't
        # face a time crunch. pretty printing a large file would be a
        # problem, but pretty printing is elective.
        #
        if text is None:
            return ""
        text = text.replace("\n", "")
        text = text.strip()
        buf = ""
        lines = []
        out = True
        last = ""
        for i, c in enumerate(text):
            if out is True and c == "\t":
                continue
            if out is True and last == " " and c == " ":
                continue
            buf += c
            if c in ["]", "}"]:
                try:
                    json.loads(buf)
                    lines.append(buf)
                    buf = ""
                except Exception as e:
                    ...
            elif c == '"':
                out = not out
            last = c
        if buf.strip() != "":
            lines.append(buf)
        return lines

    @classmethod
    def jsonl_text_to_lines(cls, text:str) -> list[str]:
        lines = cls.jsonl_text_to_list(text)
        return "\n".join(lines)



