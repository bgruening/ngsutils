#!/usr/bin/env python
"""

Common util classes / functions for the NGS project

"""
import sys,os,gzip

def dictify(values,colnames):
    """
    Convert a list of values into a dictionary based upon given column names.
    
    If the column name starts with an '@', the value is assumed to be a comma
    separated list.
    
    If the name starts with a '#', the value is assumed to be an int.
    
    If the name starts with '@#', the value is assumed to  a comma separated
    list of ints.
    
    """
    d = {}
    for i in xrange(len(colnames)):
        key = colnames[i]
        split = False
        num = False

        if key[0] == '@':
            key = key[1:]
            split = True
        if key[0] == '#':
            key = key[1:]
            num = True

        if i < len(values):
            if num and split:
                val = [int(x) for x in values[i].rstrip(',').split(',')]
            elif num:
                val = int(values[i])
            elif split:
                val = values[i].rstrip(',').split(',')
            else:
                val = values[i]

            d[key] = val

        else:
            d[key] = None

    return d
    
    
class gzip_opener:
    '''
    A Python 2.6 class to handle 'with' opening of text files that may
    or may not be gzip compressed.
    '''
    def __init__(self,fname):
        self.fname = fname
    def __enter__(self):
        if self.fname == '-':
            self.f = sys.stdin
        elif self.fname[-3:] == '.gz':
            self.f = gzip.open(os.path.expanduser(self.fname))
        else:
            self.f = open(os.path.expanduser(self.fname))
        return self.f
    def __exit__(self, type, value, traceback):
        if self.f != sys.stdin:
            self.f.close()
        return False

def filenames_to_uniq(names,new_delim='.'):
    '''
    Given a set of file names, produce a list of names consisting of the
    uniq parts of the names. This works from the end of the name.  Chunks of
    the name are split on '.' and '-'.
    
    For example:
        A.foo.bar.txt
        B.foo.bar.txt
        returns: ['A','B']
    
        AA.BB.foo.txt
        CC.foo.txt
        returns: ['AA.BB','CC']
    
    '''
    name_words = []
    maxlen = 0
    for name in names:
        name_words.append(name.replace('.',' ').replace('-',' ').strip().split())
        name_words[-1].reverse()
        if len(name_words[-1]) > maxlen:
            maxlen = len(name_words[-1])

    common = [False,] * maxlen
    for i in xrange(maxlen):
        last = None
        same = True
        for nameword in name_words:
            if i >= len(nameword):
                same = False
                break
            if not last:
                last = nameword[i]
            elif nameword[i] != last:
                same = False
                break
        common[i] = same

    newnames = []
    for nameword in name_words:
        nn = []
        for (i, val) in enumerate(common):
            if not val and i < len(nameword):
                nn.append(nameword[i])
        nn.reverse()
        newnames.append(new_delim.join(nn))
    return newnames

def parse_args(argv,defaults=None):
    opts = {}
    if defaults:
        opts.update(defaults)

    args = []

    i=0
    while i<len(argv):
        if argv[i][0] == '-':
            arg = argv[i].lstrip('-')
            if '=' in arg:
                k,v=arg.split('=',2)
                if k in defaults:
                    if type(defaults[k]) == float:
                        opts[k]=float(v)
                    elif type(defaults[k]) == int:
                        opts[k]=int(v)
                    else:
                        opts[k]=v
            else:
                opts[arg]=True 
        else:
            args.append(argv[i])
        i+=1
    return opts,args        