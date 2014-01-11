import os, os.path, re, getopt, fcntl

def find(dir, pattern):
    list = map(lambda x: os.path.join(dir, x), os.listdir(dir))
    dirs = filter(os.path.isdir, list)
    files = filter(lambda x: pattern.search(os.path.basename(x)),
                   filter(os.path.isfile, list))
    for d in dirs:
        files += find(d, pattern)
    
    return files

class Options(dict):
    def getopt(self, argv, options, long_options=[]):
        opt_pattern = re.compile(r"[a-zA-Z]:?")

        # set up a dict that maps all the possible options to a boolean value
        # True if the option has an arg, False otherwise
        has_arg = {}
        for x in opt_pattern.findall(options):
            has_arg[x[0]] = len(x) > 1
        for x in long_options:
            has_arg[x.rstrip("=")] = x.endswith("=")

        # set the option defaults
        for key in has_arg:
            if not self.has_key(key):
                self.__setitem__(key, None)
        
        # parse the options
        (opts, self.args) = getopt.getopt(argv, options, long_options)

        # set the state of the options
        for (key, val) in opts:
            key = key.lstrip("-")
            if has_arg[key]:
                self.__setitem__(key, val)
            else:
                self.__setitem__(key, 1)

class LockFile:
    def __init__(self, lock_file):
        self.lock_file = lock_file

    def lock(self):
        self.lock = open(self.lock_file, "w")
        fcntl.lockf(self.lock, fcntl.LOCK_EX)

    def unlock(self):
        self.lock.close()
        
