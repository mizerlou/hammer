import util, sys, re, os.path, datetime

month = {'Jan': 1,
         'Feb': 2,
         'Mar': 3,
         'Apr': 4,
         'May': 5,
         'Jun': 6,
         'Jul': 7,
         'Aug': 8,
         'Sep': 9,
         'Oct': 10,
         'Nov': 11,
         'Dec': 12}

forced_re = re.compile(r"^X-Hammer-Status:.*forced")
date_re = re.compile(r"X-From-Line:.*(?P<M>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?P<d>\d\d?) (?P<h>\d\d):(?P<m>\d\d):(?P<s>\d\d) (?P<y>\d\d\d\d)$")
SA_re = re.compile(r"^X-Spam-Status: (Yes|No)")
def getHeaders(file):
    f = open(file)
    date = None
    forced = 0
    SA = None
    
    header = f.readline()
    if header.startswith("To: "):
        return None
    
    l = f.readline()
    if l[0] == " ":
        header = header[:-1] + l
        l = None
    m = date_re.match(header)
    if not m:
        print >> sys.stderr, "%s: %s" % (header, file)
        return None
    else:
        date = datetime.datetime(int(m.group("y")),
                                 int(month[m.group("M")]),
                                 int(m.group("d")),
                                 int(m.group("h")),
                                 int(m.group("m")),
                                 int(m.group("s")))

    # the hammer status won't be the second header, so...
    for l in f:
        if not l:
            break
        if forced_re.match(l):
            forced = 1
        else:
            m = SA_re.match(l)
            if m:
                SA = m.group(1)
    f.close()

    return (date, forced, SA)

def measure(show, title, files, saMatch, oldest=None):
    data = [getHeaders(f) for f in files]
    data = [d for d in data if d is not None]
    
    if oldest is not None:
        data = [(t,f,s) for (t,f,s) in data if t >= oldest ]

    data.sort()

    oldest = data[0][0]
    data = [(t - oldest, f, s) for (t,f, s) in data]

    show(title, data, saMatch)

    return oldest

def cumulative(title, data, saMatch):
    print '"%s"' % title
    count = 0
    for (delta, forced, SA) in data:
        count += 1
        print (delta.days * 86400 + delta.seconds)/86400.0, count
    print

    print '"%s misclassified"' % title
    count = 0
    for (delta, forced, SA) in data:
        if forced:
            count += 1
            print (delta.days * 86400 + delta.seconds)/86400.0, count
    print

    print '"%s SA misclassified"' % title
    count = 0
    for (delta, forced, SA) in data:
        if saMatch == SA:
            count += 1
            print (delta.days * 86400 + delta.seconds)/86400.0, count
    print

def divy(delta):
    return delta.days

def rate(title, data, saMatch):
    print '"%s"' % title
    rates = [0] * (divy(data[-1][0]) + 1)
    for (delta, forced, SA) in data:
        rates[divy(delta)] += 1
    for i in xrange(0,len(rates)):
        print i, rates[i]
    print

    print '"%s misclassified"' % title
    forced = re.compile(r"^X-Hammer-Status:.*forced")
    rates = [0] * (divy(data[-1][0]))
    for (delta, forced, SA) in data:
        if forced:
            rates[divy(delta)] += 1
    for i in xrange(0,len(rates)):
        print i, rates[i]
    print

show = cumulative

oldest = measure(show, "spam",
                 util.find(sys.argv[1], re.compile(r"\d+")), "No")
measure(show, "ham", util.find(sys.argv[2], re.compile(r"\d+")), "Yes", oldest)
measure(show, "lists",
        util.find(sys.argv[3], re.compile(r"\d+")), "Yes", oldest)



