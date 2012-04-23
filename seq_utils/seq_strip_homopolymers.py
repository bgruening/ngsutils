#!/usr/bin/env python
'''
Removes runs of homopolymers in a FASTA file

This will remove all runs of repeated nucleotides in a FASTA file. This can be
used to help map Ion Torrent or 454 reads, which are succeptible to errant
homopolymer calls.

This produces two files:
    1) a new FASTA file with the homopolymers removed
    2) an index file that allows for converting the new coordinates to the
       original genomic positions

The index is currently a gzipped text file in the format: (subject to change)
>reference
pos\trepeat_count\ttotal_offset
pos\trepeat_count\ttotal_offset
'''

import os
import sys
import gzip

from support.eta import ETA


class FASTAWriter(object):
    def __init__(self, fileobj=sys.stdout, wrap=50):
        self.fileobj = fileobj
        self.wrap = wrap

        self._line_count = 0
        self._first = True

    def write_ref(self, ref):
        if not self._first:
            self.fileobj.write('\n')

        self.fileobj.write('>%s\n' % ref)
        self._first = False
        self._line_count = 0

    def write(self, seq):
        for s in seq:
            self.fileobj.write(s)
            self._line_count += 1
            if self._line_count >= self.wrap:
                self.fileobj.write('\n')
                self._line_count = 0

    def close(self):
        self.write('\n')
        if self.fileobj != sys.stdout:
            self.fileobj.close()


class HPSIndex(object):
    'Class for reading the homopolymer stripped index file - format subject to change'
    def __init__(self, fname, mode='r'):
        self.fname = fname
        self.mode = mode

        if mode == 'r':
            self.fileobj = gzip.open(fname)
        elif mode == 'w':
            self.fileobj = gzip.open(fname, 'w')

        self._cur_ref = None

    def __iter__(self):
        if self.mode != 'r':
            raise IndexError

        self.fileobj.seek(0)
        self._cur_ref = None
        return self

    def next(self):
        for line in self.fileobj:
            line = line.strip()
            if line[0] == '>':
                self._cur_ref = line[1:]
            else:
                cols = [int(x) for x in line.split('\t')]
                return (self._cur_ref, cols[0], cols[1], cols[2])
        raise StopIteration

    def write_ref(self, ref):
        if self.mode != 'w':
            raise ValueError
        self.fileobj.write('>%s\n' % (ref))

    def write(self, pos, count, offset):
        if self.mode != 'w':
            raise ValueError
        self.fileobj.write('%s\t%s\t%s\n' % (pos, count, offset))

    def close(self):
        if self.fileobj:
            self.fileobj.close()


def read_fasta_bases(fname):
    if fname[-3:] == '.gz':
        fobj = gzip.open(fname)
    else:
        fobj = open(fname)

    eta = ETA(os.stat(fname).st_size, fileobj=fobj)

    ref = None
    for line in fobj:
        eta.print_status(extra=ref)
        line = line.strip()
        if line[0] == '>':
            ref = line[1:]
        else:
            for base in line:
                yield (ref, base.upper())

    fobj.close()
    eta.done()


def seq_strip_homopolymer(fname, outname, suffix=None):
    outwriter = FASTAWriter(open('%s.fa' % outname, 'w'))
    outidx = HPSIndex('%s.idx' % outname, 'w')

    lastref = None
    lastbase = None

    strip_pos = 0
    genomic_pos = 0
    repeat_count = 0

    for ref, base in read_fasta_bases(fname):
        if ref != lastref:
            if suffix:
                outwriter.write_ref('%s%s' % (ref, suffix))
            else:
                outwriter.write_ref(ref)

            outidx.write_ref(ref)
            lastref = ref
            lastbase = None

            strip_pos = 0
            genomic_pos = 0
            repeat_count = 0

        if base == lastbase:
            repeat_count += 1
        else:
            lastbase = base
            if repeat_count > 0:
                outidx.write(strip_pos, repeat_count, (genomic_pos - strip_pos))
            strip_pos += 1
            repeat_count = 0
            outwriter.write(base)
        genomic_pos += 1

    # if this ends in a repeat...
    if repeat_count > 0:
        outidx.write(strip_pos, repeat_count, (genomic_pos - strip_pos))

    outwriter.close()
    outidx.close()


def usage():
    print __doc__
    print """Usage: sequtils strip_homopolymer {opts} infile.fa outfile_template

Options:
    -suf val   Suffix for reference names (include space for comment)
"""
    sys.exit(1)


if __name__ == '__main__':
    fname = None
    outname = None
    suffix = None
    last = None
    for arg in sys.argv[1:]:
        if last == '-suf':
            suffix = arg
            last = None
        elif arg in ['-suf']:
            last = arg
        elif not fname:
            if not os.path.exists(arg):
                print "Missing file: %s" % arg
                usage()
            fname = arg
        elif not outname:
            outname = arg

    if not fname or not outname:
        usage()

    seq_strip_homopolymer(fname, outname, suffix)
