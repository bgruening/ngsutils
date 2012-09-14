'''
Support package for processing a dbSNP tabix dump from UCSC.
'''

import pysam
import collections
import sys


class SNPRecord(collections.namedtuple('SNPRecord', '''bin
chrom
chromStart
chromEnd
name
score
strand
refNCBI
refUCSC
observed
molType
clazz
valid
avHet
avHetSE
func
locType
weight
exceptions
submitterCount
submitters
alleleFreqCount
alleles
alleleNs
alleleFreqs
bitfields
''')):
    __slots__ = ()

    @property
    def alleles(self):
        alts = []
        for alt in self.observed.split('/'):
            if alt != '-' and self.strand == '-':
                alt = _revcomp(alt)

            alts.append(alt)

        return alts

    @property
    def var_length(self):
        return int(self.chromEnd) - int(self.chromStart)


class DBSNP(object):
    def __init__(self, fname):
        self.dbsnp = pysam.Tabixfile(fname)
        self.asTup = pysam.asTuple()

    def fetch(self, chrom, pos):
        'Note: pos is 0-based'

        # Note: tabix the command uses 1-based positions, but
        #       pysam.Tabixfile uses 0-based positions

        for tup in self.dbsnp.fetch(chrom, pos, pos + 1, parser=self.asTup):
            snp = SNPRecord._make(tup)
            if int(snp.chromStart) == pos:
                yield snp

    def close(self):
        self.dbsnp.close()

    def dump(self, chrom, op, pos, base, snp, exit=True):
        print
        print ' ->', op, chrom, pos, base
        print snp
        print snp.alleles
        if exit:
            sys.exit(1)

    def is_valid_variation(self, chrom, op, pos, seq, verbose=False):
        for snp in self.fetch(chrom, pos):
            if not '/' in snp.observed or snp.clazz not in ['single', 'mixed', 'in-del', 'insertion', 'deletion']:
                # these are odd variations that we can't deal with... (microsatellites, tooLongToDisplay members, etc)
                continue

            if op == 0:
                if snp.clazz in ['single', 'mixed'] and seq in snp.alleles:
                    return True
                elif verbose:
                    for alt in snp.alleles:
                        if len(alt) > 1:
                            self.dump(chrom, op, pos, seq, snp, False)

            elif op == 1:
                if snp.clazz in ['insertion', 'mixed', 'in-del']:
                    if seq in snp.alleles:
                        return True

                    if verbose:
                        if len(seq) > 1:
                            self.dump(chrom, op, pos, seq, snp, False)
                        else:
                            for alt in snp.alleles:
                                if len(alt) > 1:
                                    self.dump(chrom, op, pos, seq, snp, False)

            elif op == 2:
                if snp.clazz in ['deletion', 'mixed', 'in-del']:
                    if '-' in snp.alleles and seq in snp.alleles:
                        return True

        return False


__revcomp_mapping = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}


def _revcomp(seq):
    if len(seq) == 1:
        if seq.upper() in __revcomp_mapping:
            return __revcomp_mapping[seq.upper()]
        return seq

    ret = []
    for base in seq.upper()[::-1]:
        if base in __revcomp_mapping:
            ret.append(__revcomp_mapping[base])
        else:
            ret.append(base)
    return ''.join(ret)
