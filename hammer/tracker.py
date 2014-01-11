import anydbm, os.path, time, bsddb, sys

class MessageTracker:
    def __init__(self, tracker_file):
        flag = (os.path.exists(tracker_file) and "w") or "c"
        #self.tracker = anydbm.open(tracker_file, flag)
        self.tracker = bsddb.hashopen(tracker_file, flag)
        
    def close(self):
        self.tracker.close()

    def get_id(self, msg):
        return msg["message-id"]
#        return (msg["message-id"]
#                + "/" + msg.get("x-from-line", msg.get("from", ""))
#                + "/" + msg.get("to", ""))

    def ham(self, msg):
        self._add(msg, "h")

    def spam(self, msg):
        self._add(msg, "s")
        
    def _add(self, msg, val):
        try:
            key = self.get_id(msg)
            self.tracker[key] = val
        except:
            print >> sys.stderr, "ERROR: '%s' => '%s'", (key, val)
            raise
        
    def get(self, msg, failobj=None):
        key = self.get_id(msg)
        try:
            return self.tracker[key]
        except KeyError:
            return failobj

    def seen(self, msg):
        return self.tracker.has_key(self.get_id(msg))

    def remove(self, msg):
        del self.tracker[self.get_id(msg)]

    def dump(self):
        for (k,v) in self.tracker.iteritems():
            print k, "---", v
