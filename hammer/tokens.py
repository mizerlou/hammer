import re, email, html, sys

html_hack_re = re.compile(r"<!\w{1,8}>")
html_tag_re = re.compile(r"<.*?>")
word_re = re.compile(r"\w(?:[\w']+)\w")

banned_attrs = {"src":None, "href":None, "alt":None,
                "id":None, "action":None, "background":None}
def unique(i):
    u = {}
    for t in i:
        if t not in u:
            u[t] = None
    return u.keys()

def mangle(prefix, list):
    return [prefix + x for x in list]

def tokenize_body(msg, config):
    if msg.is_multipart():
        rv = []
        for m in msg.get_payload():
            rv += tokenize(m, config)
        return rv
    else:
        type = msg.get("content-type", "text/plain")
        if type.startswith("text/"):
            payload = msg.get_payload(decode=True)
            if payload:
                tokens = []
                if type.startswith("text/html"):
                    try:
                        (payload, tags) = html.parse(payload)
                        tags = [(x,y) for (x,y) in tags
                                if x not in banned_attrs]
                        tags = [y and "%s=%s" % (x,y) or x for (x,y) in tags]
                        tokens += mangle("HTML", [x[:251] for x in tags])
                    except Exception, e:
#                        print >> sys.stderr, "crap:", e
                        tokens += ["BUGhtml"]
                        try:
                            payload = html_tag_re.sub("", payload)
                        except:
                            pass

                words = word_re.findall(payload)
                tokens += mangle("BODY",
                                 [x for x in words if 3 <= len(x) <= 20])
                if len(words) > 1 and config.double:
                    tokens += mangle("BODY",
                                     ["%s %s".lower() % (x, y)
                                      for (x,y) in zip(words[:-1], words[1:])
                                      if 3 <= len(x) <= 20 and 3 <= len(y) <= 20])
                
                for key, body in config.bodies.iteritems():
                    tokens += body.get_tokens(payload)
                return tokens
    return []

def tokenize_headers(msg, config):
    tokens = []
        
    for key, header in config.headers.iteritems():
        tokens += header.get_tokens(msg.get_all(header.header, []))

    return tokens

def check_SA_part(msg):
    part = msg.get_payload(0).get_payload(decode=True)
    return part and part.find("---- Start SpamAssassin results") >= 0

def tokenize(msg, config):
    tokens = tokenize_headers(msg, config)

    # if the message was rewritten by SA, then slurp out the original
    # message and work on that
    if (msg.get("content-type", "").startswith("multipart/mixed")
        and msg.get("X-Spam-Status", "").startswith("Yes")
        and check_SA_part(msg)):
        tokens += tokenize(msg.get_payload(1), config)
    else:
        tokens += tokenize_body(msg, config)

    tokens = unique(tokens)

    return tokens

if __name__ == "__main__":
    import email.Parser, sys, config, util

    opt = util.Options()
    opt.getopt(sys.argv[1:], "c")
    config = config.Config(opt["c"])

    parser = email.Parser.Parser()
    msg = parser.parse(open(opts.arg[0]))
    toks = tokenize(msg, config)
    toks.sort()
    print toks

