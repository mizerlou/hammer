import os, re, sys, checks

GLOBAL_CONFIG_FILE = "/etc/hammer/hammer.conf"

header_re = re.compile(r"""
\s*header
\s+
(?P<name>\w+)
\s+
(?:(?P<group>\w+)\s+)?
(?P<header>[-\w]+)
\s+
(?:/(?P<regex>.*?)/(?P<modifiers>[im]*)|eval:(?P<eval>\w+)|(?P<var>\w+))
\s*
""", re.VERBOSE)

body_re = re.compile(r"""
^
\s*body
\s+
(?P<name>\w+)
\s+
(?:(?P<group>\w+)\s+)?
(?:/(?P<regex>.*?)/(?P<modifiers>[im]+)|(?P<var>\w+)|eval:(?P<eval>\w+))
\s*
$
""", re.VERBOSE)

regex_re = re.compile(r"""
\s*regex
\s+
(?P<key>\w+)
\s+
/(?P<regex>.*?)/
(?P<modifiers>\w*)
\s*
""", re.VERBOSE)

set_re = re.compile(r"""
\s*
(?P<key>\w+)
\s*
=
\s*
(?P<value>.*)
\s*
""", re.VERBOSE)

load_re = re.compile(r"""
\s*
load
\s+
(?P<file>.*)
\s*
""", re.VERBOSE)

meta_re = re.compile(r"""
\s*
meta-token
\s+
(?P<name>\w+)
\s*
""", re.VERBOSE)

group_re = re.compile(r"""
\s*
group
\s+
(?P<name>\w+)
(?P<group>(?:\s+(\w+))+)
\s*
""", re.VERBOSE)

class Config:
    def __init__(self, config_dir=None):
        self.config_dir = (config_dir \
                          or os.path.join(os.environ["HOME"], ".hammer"))
        self.prefs_file = os.path.join(self.config_dir, "prefs")
        self.prefs = {}
        self.good_tokens = os.path.join(self.config_dir, "tokens-good")
        self.bad_tokens = os.path.join(self.config_dir, "tokens-bad")
        self.msg_cache = os.path.join(self.config_dir, "msg-cache")
        self.lock = os.path.join(self.config_dir, "lock")
        
        # all user code that is loaded and run will be run within the
        # context of this "sandbox"
        self.sandbox = {}
        
        self.level = 0.9
        self.double = 1

        # a dictionary of stored regexs, these can be referenced by the
        # various header and body checks
        self.regexs = {}

        # the header and body checks
        self.headers = {}
        self.bodies = {}
        
        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)

        self.read_prefs(GLOBAL_CONFIG_FILE)
        self.read_prefs(self.prefs_file)

    def read_prefs(self, prefs_file):
        """
        grok a prefs file
        """
        
        if not os.path.exists(prefs_file):
            return

        def grok_header(m):
            header = m.group("header")
            (name, regex, group) = self.match_common(m)
            self.headers[name] = checks.Header(header, name,
                group, regex)

        def grok_body(m):
            (name, regex, group) = self.match_common(m)
            self.bodies[name] = checks.Body(name, group, regex)

        def grok_meta(m):
            name = m.group("name")
            check = self.headers.get(name) or self.bodies.get(name)
            if not check:
                print >> sys.stderr, ("meta-token: check '%s' not found"
                                      % name)
            else:
                check.meta_token = 1

        def grok_group(m):
            name = m.group("name")

            for c in m.group("group").split():
                check = self.headers.get(c) or self.bodies.get(c)
                if not check:
                    print >> sys.stderr, ("group(%s): check '%s' not found"
                                          % (name, c))
                else:
                    check.group = name

        def grok_regex(m):
            key = m.group("key")
            regex = m.group("regex")
            modifiers = self.parse_modifers(m.group("modifiers"))
            self.regexs[key] = re.compile(regex, modifiers).findall

        def grok_set(m):
            key = m.group("key")
            value = m.group("value")
            if key == "level":
                self.level = float(value)
            elif key == "double":
                self.double = value.lower() in ("on", "true", "yes")
            else:
                self.prefs[key] = value

        def grok_load(m):
            source = m.group("file")
            if not source.startswith("/"):
                source = os.path.join(self.config_dir, source)
            execfile(source, self.sandbox)

        parser = [
            (header_re, grok_header),
            (body_re, grok_body),
            (meta_re, grok_meta),
            (group_re, grok_group),
            (regex_re, grok_regex),
            (set_re, grok_set),
            (load_re, grok_load),
            ]
        
        o = open(prefs_file)
        for line in o:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue

            found = 0
            for (regex, grokker) in parser:
                m = regex.match(line)
                if m:
                    found = 1
                    grokker(m)
                    break

            if not found:
                raise Exception("cannot parse: '%s'" % line)

        o.close()
        
    def match_common(self, m):
        """
        match the comment elements of a header or body line
        """
        name = m.group("name")
        if m.group("regex"):
            modifiers = self.parse_modifers(m.group("modifiers"))
            regex = re.compile(m.group("regex"),modifiers).findall
        elif m.group("var"):
            regex = self.regexs[m.group("var")]
        else:
            regex = eval(m.group("eval"), self.sandbox)
        group = m.group("group")

        return (name, regex, group)

    def parse_modifers(self, m):
        """
        parse the regex modifers and return a bitwise or'ing of the values
        """
        rv = 0
        for x in m:
            if x == "i":
                rv |= re.IGNORECASE
            elif x == "m":
                rv |= re.MULTILINE
        return rv

    def is_spam(self, level):
        """
        return true iff level is greater than or equal to the spam cutoff level
        """
        return level >= self.level
    
if __name__ == "__main__":
    c = Config()
    print c.regexs
    print c.headers
    print c.bodies
    print c.bodies['THIS_IS_NOT_SPAM'].__dict__

    print [ h.name for h in c.headers.values() if h.group == "EMAIL" ]
