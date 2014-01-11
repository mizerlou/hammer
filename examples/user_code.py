import re

spam_status_re = re.compile(r"""
  ^
  (?P<spam>Yes|No),
  \s+
  hits=(?P<hits>-?\d+(?:\.\d+))
  \s+
  required=\d+(?:\.\d+)
  \s+
  tests=(?P<tests>[A-Z_0-9\s,]*?)
  (?:autolearn=(?:\S+)\s+)?
  version=.*?
  $
  """, re.VERBOSE | re.MULTILINE)

tests_re = re.compile(r"\w+")
def tokenize_SA(status):
    m = spam_status_re.match(status)
    if m:
        return tests_re.findall(m.group("tests"))
    else:
        return []
    
