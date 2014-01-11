import re

"""
There are two types of checks: a header check and a body check.
"""

class BaseCheck:
    """
    code used by both header and body checks
    """
    def __init__(self, name, group, regex, meta_token = 0):
        self.name = name
        self.group = (group or name)
        self.regex = regex
        self.meta_token = meta_token

    def mangle(self, tokens):
        if self.meta_token:
            return [self.group] * len(tokens)
        else:
            return [self.group + x for x in tokens]

    
class Header(BaseCheck):
    def __init__(self, header, name, group, regex, meta_token = 0):
        BaseCheck.__init__(self, name, group, regex, meta_token)
        self.header = header

    def get_tokens(self, targets):
        matches = [self.regex(x) for x in targets]
        tokens = []
        for m in matches:
            tokens += self.mangle(m)
        return tokens

class Body(BaseCheck):
    def get_tokens(self, target):
        return self.mangle(self.regex(target))

if __name__ == "__main__":
    b = Body("A", None, re.compile(r"ab[cd]\b").findall, 0)
    print b.get_tokens("abc abe abd abdd")

    h = Header("X-Something", "B", "C", re.compile(r"\b\w+'?\w+\b").findall, 1)
    print h.get_tokens(["hi there", "how are you", "i'm fine"])
