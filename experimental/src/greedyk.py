import sut as SUT
import random
import time
import sys
import traceback
import argparse
import os
import coverage
from collections import namedtuple

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--depth', type=int, default=100,
                        help='Maximum search depth (100 default).')
    parser.add_argument('-t', '--timeout', type=int, default=3600,
                        help='Timeout in seconds (3600 default).')
    parser.add_argument('-s', '--seed', type=int, default=None,
                        help='Random seed (default = None).')
    parser.add_argument('-m', '--maxtests', type=int, default=-1,
                        help='Maximum #tests to run (-1 = infinite default).')
    parser.add_argument('-u', '--uncaught', type=bool, default=False,
                        help='Test fails on uncaught exception.')
    parser.add_argument('-k', '--k', type=int, default=10,
                        help='How many things to try (default 10).')
    parser.add_argument('-c', '--module', type=str, default="sut.py",
                        help='Module to cover (default sut.py).')  
    parsed_args = parser.parse_args(sys.argv[1:])
    return (parsed_args, parser)

def make_config(pargs, parser):
    """
    Process the raw arguments, returning a namedtuple object holding the
    entire configuration, if everything parses correctly.
    """
    pdict = pargs.__dict__
    # create a namedtuple object for fast attribute lookup
    key_list = pdict.keys()
    arg_list = [pdict[k] for k in key_list]
    Config = namedtuple('Config', key_list)
    nt_config = Config(*arg_list)
    return nt_config   
    
parsed_args, parser = parse_args()
config = make_config(parsed_args, parser)
print('Random testing using config={}'.format(config))

if config.seed != None:
    random.seed(config.seed)

start = time.time()
elapsed = time.time()-start

cov = coverage.coverage(branch=True, source=[config.module])
t = SUT.t()
ntests = 0

branchesHit = set()

while (config.maxtests == -1) or (ntests < config.maxtests):
    ntests += 1

    t.restart()
    test = []

    for s in xrange(0,config.depth):
        possible = t.enabled()
        random.shuffle(possible)
        old = t.state()
        last = min(config.k, len(possible))
        pos = 0

        for a in possible[:config.k]:
            elapsed = time.time()-start
            if elapsed > config.timeout:
                print "EXITING DUE TO TIMEOUT"
                print ntests, "EXECUTED"
                sys.exit(2)
            pos += 1
            test.append(a)
            
            try:
                cov.start()
                a[2]()
            except:
                if config.uncaught:
                    _,_,tb = sys.exc_info()
                    traceback.print_tb(tb)
                    tbInfo = traceback.extract_tb(tb)
                    filename,line,func,text = tbInfo[-1]
                    print "TEST:"
                    for step in test:
                        print step[0]
                    print "EXITING DUE TO FAILED TEST"
                
                    red = t.reduce(test, t.failsCheck, True, True)
                    print "REDUCED:"
                    for step in red:
                        print step[0]
                    sys.exit(1)
            finally:
                cov.stop()

            if not t.check():
                _,_,tb = sys.exc_info()
                traceback.print_tb(tb)
                tbInfo = traceback.extract_tb(tb)
                filename,line,func,text = tbInfo[-1]
                print "TEST:"
                for step in test:
                    print step [0]
                print "EXITING DUE TO FAILED TEST"

                red = t.reduce(test, t.failsCheck, True, True)
                print "REDUCED:"
                for step in red:
                    print step[0]
                sys.exit(1)

            currBranches = cov.collector.get_arc_data()
            newBranch = False
            for src_file, arcs in currBranches.iteritems():
                for arc in arcs:
                    branch = (src_file, arc)
                    if branch not in branchesHit:
                        branchesHit.add(branch)
                        elapsed = time.time()-start
                        print elapsed,len(branchesHit),branch
                        newBranch = True
            if newBranch or (pos == last):
                break
            t.backtrack(old)
            
            elapsed = time.time() - start
            if elapsed > config.timeout:
                print "EXITING DUE TO TIMEOUT"
                print ntests, "EXECUTED"
                sys.exit(2)
                break

print ntests, "EXECUTED"


