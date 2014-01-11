import bsddb, cPickle
from cStringIO import StringIO
import time

def create(config):
    type = config.prefs.get("datastore", "BDBDataStore")
#    type = config.prefs.get("datastore", "MySQLDataStore")

    if type == "BDBDataStore":
        return BDBDataStore(config)
    elif type == "MySQLDataStore":
        return MySQLDataStore(config)

class DataStore:
    def __init__(self, config):
        pass
    def close(self):
        pass

    def update(self, tokens, values):
        for token in ["msg-count"] + tokens:
            val = self.get(token)

            val = (max(0, val[0] + values[0]),
                   max(0, val[1] + values[1]),
                   int(time.time()))

            self._save(token, val)

    def get(self, token):
        val = self._load(token)
        if val is None:
            val = (0, 0, int(time.time()))
        return val
    
    def get_message_counts(self):
        return self.get("msg-count")
    
    def ham(self, msg):
        self._track(msg["message-id"], "h")

    def spam(self, msg):
        self._track(msg["message-id"], "s")

    def is_known(self, msg):
        return self._get_status(msg["message-id"]) is not None
    
    def is_spam(self, msg):
        return self._get_status(msg["message-id"]) == "s"

    def is_ham(self, msg):
        return self._get_status(msg["message-id"]) == "h"

    def remove(self, msg):
        self._forget_status(msg["message-id"])

    def dump(self):
        pass

class BDBDataStore(DataStore):
    def __init__(self, config):
        self.token_file = "%s/tokens" % config.config_dir
        self.messages_file = "%s/messages" % config.config_dir
        self.tokens = bsddb.btopen(self.token_file, "c")
        self.messages = bsddb.hashopen(self.messages_file, "c")

        # in 2.2, bsddb doesn't define a get method, so we fallback on
        # synthesizing one
        try:
            self.get_token = self.tokens.get
            self.get_message = self.messages.get
        except AttributeError, e:
            def get_token(key, failobj=None):
                try:
                    return self.tokens[key]
                except KeyError, e:
                    return failobj
            def get_message(key, failobj=None):
                try:
                    return self.messages[key]
                except KeyError, e:
                    return failobj
                
            self.get_token = get_token
            self.get_message = get_message
        
    def close(self):        
        try:
            self.tokens.close()
        finally:
            self.messages.close()

    def _save(self, token, val):
        self.tokens[token] = "%d %d %d" % val

    def _load(self, token):
        val = self.get_token(token)
        if val:
            return map(int, val.split())
        return None
    
    def _track(self, msg_id, value):
        self.messages[msg_id] = value

    def _get_status(self, msg_id):
        return self.get_message(msg_id)

    def _forget_status(self, msg_id):
        del self.messages[msg_id]

    def dump(self):
        for (k, v) in self.tokens.iteritems():
            print "%s\t%s" % (k,v)

class MySQLDataStore(DataStore):
    def __init__(self, config):
        import MySQLdb

        self.connection = MySQLdb.connect(db=config.prefs["dbname"],
                                          user=config.prefs["dbuser"],
                                          passwd=config.prefs["dbpasswd"])
        self.cursor = self.connection.cursor()
        self.cache = {}
        self.loaded = {}
        
    def close(self):
        self._spill()
        try:
            self.cursor.close()
        finally:
            self.connection.close()

    def _spill(self):
        import MySQLdb, sys
        update = []
        insert = []
        now = int(time.time())
        for (token, (good, bad, then)) in self.cache.iteritems():
            if self.loaded.has_key(token):
                update.append((good, bad, token, now))
            else:
                insert.append((good, bad, token, now))
        for i in xrange(0, len(insert), 10):
            self.cursor.executemany(
                """insert into token (good, bad, token, last_modified)
                     values (%s, %s, %s, %s)""",
                insert[i:i+10])
        for i in xrange(0, len(insert), 10):
            self.cursor.executemany(
                """update token set good=%s, bad=%s, last_modified=%s
                     where token=%s""",
                update[i:i+10])
        self.cache = {}
        self.loaded = {}
        
    def _save(self, token, val):
        self.cache[token] = val
        if len(self.cache) > 1000:
            self._spill()

    def _load(self, token):
        rv = self.cache.get(token)
        if rv is not None:
            return rv
        if self.cursor.execute("""select good, bad, last_modified from token
                                    where token=%s""", (token,)):
            rv = self.cursor.fetchone()
            self.cache[token] = rv
            self.loaded[token] = 1
            return rv
        return None

    def _track(self, msg_id, value):
        try:
            self.cursor.execute("""insert into message (message_id, status)
                                     values (%s, %s)""", (msg_id, value))
        except:
            self.cursor.execute("""update message set status=%s
                                     where message_id=%s""", (value, msg_id))

    def _get_status(self, msg_id):
        if self.cursor.execute("""select status from message
                                    where message_id=%s""", (msg_id,)):
            return self.cursor.fetchone()[0]
        return None

    def _forget_status(self, msg_id):
        self.cursor.execute("delete from message where message_id=%s",
                            (msg_id,))

        
