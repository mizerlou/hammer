import HTMLParser, htmlentitydefs
import re

class Parser(HTMLParser.HTMLParser):
    """

    a simple parser that removes, but keeps track of, tags from an html
    document.  the non-tag data is held in the "tag" attribute and the tag
    data is held in the "tags" attribute.

    the tags attribute is a list of unique tuples of the form:
    (tag_name, None)
    or
    (attribute_name, attribute_value)
    
    """
    
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.data = ""
        self.tags = {}
        
    def process_data(self):
        if self.data and self.data[-1] == " ":
            self.data += " "
#            print self.data
#        self.data = ""

    def process_entity(self, name):
        try:
            self.data += chr(htmlentitydefs.name2codepoint[name])
        except:
            self.data += "?"
        
    def handle_starttag(self, tag, attr):
        self.tags[(tag, None)] = None
        for (k,v) in attr:
            self.tags[(k,v)] = None
        self.process_data()
        
    def handle_endtag(self, tag):
        self.process_data()
        
    def handle_data(self, data):
        self.data += data
        
    def handle_charref(self, name):
        try:
            self.data += chr(int(name))
        except:
            self.data += "?"

    def handle_entityref(self, name):
        self.process_entity(name)

crap_re = re.compile("<!.*?>", re.DOTALL)

def parse(s):
    """
    the html represented by s is "cleansed" by removing all bogus tags,
    ie: <!.*?>

    then the tags are split from the text

    a tuple of the following form is returned:

    (text, tag/attribute set)
    """
    
    s = crap_re.sub("", s)
    p = Parser()
    p.feed(s)
    p.close()
    return (p.data, p.tags.keys())

if __name__ == "__main__":
    print parse('''
<!..."fooey
  bazey bar
  xxx>
  
<html>
<body>
<div align="center">

<p align="center"><small><small><small><small><small><small><font
color="#ffffff">!....logging....!....nectarine....!....slim....!...capture....!....indiscriminate....
</font></small></small></small></small></small></small></p>
<div align="center"><center>

<table width="748" cellpadding="15" border="0">
  <tr>
    <td width="716"><font face="arial" size="5" color="red"><b>10<!....prime....>0% pu<!....singapore....>re h<!....bathurst...>gh yo<!....gagging....>ur's fr<!....molten....>ee</b></font>
    <font face="arial" size="2"><p>as se<!....wisconsin....>en on nb<!....xylem....>c, cb<!....hilton....>s, c<!....java....>n<!....straightaway....>n, and even opr<!....crucify....>ah! the he<!....miff....>alth disco<!....clear....>very
    that actua<!....bp....>lly reve<!....preface....>rses agi<!....electric....>ng whivle burn<!....donor....>ing f<!....premier....>at, witho<!....stodgy....>ut die<!....bernoulli....>ting or exer<!....asynchrony....>cise! th<!....abreact....>is proven
''')
