import operator

class Bayes:
    """
    An implemenation of a naive bayesian filter.
    """
    def __init__(self, datastore):
        self.datastore = datastore
            
    def get_token_counts(self, tokens):
        """
        return a list of tuples of the form:
          (token, good_count, bad_count)
        """
        
        (bmc, gmc, lm) = self.datastore.get_message_counts()
        gmc = float(max(1, gmc))
        bmc = float(max(1, bmc))
        
        rv = []
        for t in tokens:
            (gc, bc, lm) = self.datastore.get(t)
            rv.append((t, gc, gc/gmc, bc, bc/bmc))
        return rv
    
    def get_token_probabilities(self, tokens):
        """
        given a list of tokens, return a sorted list of tuples of the
        form:
        
          (probability, token)

        the list contains the 15 tokens whose probability is the farthest
        away from 0.5.
        """
        probs = []

        (good_count, bad_count, lm) = self.datastore.get_message_counts()
        good_count = float(max(1,good_count))
        bad_count = float(max(1,bad_count))
        
        for token in tokens:
            (gc, bc, lm) = self.datastore.get(token)
                
            gc *= 2

            if gc + bc >= 5:
                bp = min(1.0, bc / bad_count)
                gp = min(1.0, gc / good_count)

                mn = gp > 0.01 and 0.0001 or 0.01
                mx = bp > 0.01 and 0.9999 or 0.99
                
                p = max(mn, min(mx, bp / (bp + gp)))
            else:
                # this is a token that we "don't know"
                p = 0.4

            probs.append((abs(p - 0.5), p, token))
        
        probs.sort()

        probs = probs[-15:]

        probs = [(y,z) for (x,y,z) in probs]
        probs.sort()
        
        return probs
    
    def filter(self, tokens):
        """
        compute the probabilities of each of the tokens and then compute
        the aggregate probability of the top 15 tokens.

        return a tuple of the form:
          (aggregate_probability, [(probability, token), ...])
        """
        probs = self.get_token_probabilities(tokens)

        prod = reduce(operator.mul, [x for (x,y) in probs], 1)
        inv_prod = reduce(operator.mul, [1-x for (x,y) in probs], 1)
        try:
            return (prod / (prod + inv_prod), probs)
        except ZeroDivisionError:
            print probs
            print prod, inv_prod
            return (0, probs)
        

    def dump(self):
        def display_map_sorted(prefix, map):
            sorted = [(int(v),k) for k,v in map.iteritems()]
            sorted.sort()
            for v,k in sorted:
                print "%s: %5d %s" % (prefix, v, k)
        
        display_map_sorted("spam", self.bad)
        display_map_sorted("ham", self.good)
        
