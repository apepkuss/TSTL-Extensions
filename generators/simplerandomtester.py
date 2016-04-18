
import os
import sys

# Appending current working directory to sys.path
# So that user running randomtester from the directory where sut.py is located
current_working_dir = os.getcwd()
sys.path.append(current_working_dir)

from basetester import BaseTester
import sut as SUT
import random
import time
import traceback


class simplerRandomTester(BaseTester):
    def __init__(self, sysargs):
        self.sysargs = sysargs

        self.config = None
        self.sut = None

        self.failCloud = None
        self.allClouds = None

    def handle_failure(self, test, msg, checkFail, newCov=False):

        sys.stdout.flush()

        if not newCov:
            self.failCount += 1
            print msg
            f = self.sut.failure()
            print "ERROR:", f
            print "TRACEBACK:"
            traceback.print_tb(f[2])
        else:
            print "Handling new coverage for quick testing"
            snew = self.sut.newCurrStatements()
            for s in snew:
                print "NEW STATEMENT", s
            bnew = self.sut.newCurrBranches()
            for b in bnew:
                print "NEW BRANCH", b
            trep = self.sut.replay(test)
            sremove = []
            scov = self.sut.currStatements()
            for s in snew:
                if s not in scov:
                    print "REMOVING", s
                    sremove.append(s)
            for s in sremove:
                snew.remove(s)
            bremove = []
            bcov = self.sut.currBranches()
            for b in bnew:
                if b not in bcov:
                    print "REMOVING", b
                    bremove.append(b)
            for b in bremove:
                bnew.remove(b)
            beforeReduceS = set(self.sut.allStatements())
            beforeReduceB = set(self.sut.allBranches())
        print "Original test has", len(test), "steps"
        cloudMatch = False
        if not self.config.full:
            if not checkFail:
                failProp = self.sut.fails
            else:
                failProp = self.sut.failsCheck
            if newCov:
                failProp = self.sut.coversAll(snew, bnew)
            print "REDUCING..."
            startReduce = time.time()
            original = test
            test = self.sut.reduce(test, failProp, True, self.config.keep)
            print "Reduced test has", len(test), "steps"
            print "REDUCED IN", time.time() - startReduce, "SECONDS"
            self.sut.prettyPrintTest(test)
            if self.config.essentials:
                print "FINDING ESSENTIAL ELEMENTS OF REDUCED TEST"
                (canRemove, cannotRemove) = self.sut.reduceEssentials(test, original, failProp, True, self.config.keep)
                print len(canRemove), len(cannotRemove)
                for (c, reducec) in canRemove:
                    print "CAN BE REMOVED:", map(lambda x: x[0], c)
                    i = 0
                    self.sut.prettyPrintTest(reducec)
            sys.stdout.flush()
            if self.config.normalize:
                startSimplify = time.time()
                print "NORMALIZING..."
                test = self.sut.normalize(test, failProp, True, self.config.keep, verbose=True, speed=self.config.speed,
                                          noReassigns=self.config.noreassign)
                print "Normalized test has", len(test), "steps"
                print "NORMALIZED IN", time.time() - startSimplify, "SECONDS"
            if (self.config.gendepth != None) and (test not in map(lambda x: x[0], self.failures)) and (
                        test not in self.cloudFailures):
                startCheckCloud = time.time()
                print "GENERATING GENERALIZATION CLOUD"
                (cloudFound, matchTest, thisCloud) = self.sut.generalize(test, failProp, silent=True,
                                                                         returnCollect=True,
                                                                         depth=self.config.gendepth,
                                                                         targets=self.allClouds)
                print "CLOUD GENERATED IN", time.time() - startCheckCloud, "SECONDS"
                print "CLOUD LENGTH =", len(thisCloud)
                if cloudFound:
                    print "CLOUD MATCH",
                    faili = 0
                    for (cfailbase, err) in self.failures:
                        cfail = self.sut.captureReplay(cfailbase)
                        if matchTest in self.failCloud[cfail]:
                            print "THIS TEST CAN BE CONVERTED TO:"
                            self.sut.prettyPrintTest(matchTest)
                            print "MATCHING FAILURE", faili
                            break
                        faili += 1
                    cloudMatch = True
                    self.cloudFailures.append(test)
            if self.config.generalize and (test not in map(lambda x: x[0], self.failures)):
                startGeneralize = time.time()
                print "GENERALIZING..."
                self.sut.generalize(test, failProp, verbose=True)
                print "GENERALIZED IN", time.time() - startGeneralize, "SECONDS"
            self.reduceTime += time.time() - startReduce

        i = 0
        outf = None
        if ((self.config.output != None) and (test not in map(lambda x: x[0], self.failures))) or (
        self.config.quickTests):
            outname = self.config.output
            if (outname != None) and self.config.multiple and not newCov:
                outname += ("." + str(self.failCount))
            if self.config.quickTests and newCov:
                for s in self.sut.allStatements():
                    if s not in beforeReduceS:
                        print "NEW STATEMENT FROM REDUCTION", s
                for b in self.sut.allBranches():
                    if b not in beforeReduceB:
                        print "NEW BRANCH FROM REDUCTION", b
                outname = "quicktest." + str(self.quickCount)
                self.quickCount += 1
            if outname != None:
                outf = open(outname, 'w')
        if self.config.failedLogging != None:
            self.sut.setLog(self.config.failedLogging)
        print
        print "FINAL VERSION OF TEST, WITH LOGGED REPLAY:"
        i = 0
        for s in test:
            steps = "# STEP " + str(i)
            print self.sut.prettyName(s[0]).ljust(80 - len(steps), ' '), steps
            self.sut.safely(s)
            i += 1
            if outf != None:
                outf.write(self.sut.serializable(s) + "\n")
        if not newCov:
            f = self.sut.failure()
            print "ERROR:", f
            print "TRACEBACK:"
            traceback.print_tb(f[2])
        sys.stdout.flush()
        if outf != None:
            outf.close()
        if self.config.multiple:
            if (test in map(lambda x: x[0], self.failures)) or (test in self.cloudFailures) or cloudMatch:
                print "NEW FAILURE IS IDENTICAL TO PREVIOUSLY FOUND FAILURE, NOT STORING"
                self.repeatCount += 1
            else:
                self.failures.append((test, self.sut.failure()))
                if self.config.gendepth != None:
                    self.failCloud[self.sut.captureReplay(test)] = thisCloud
                    for c in thisCloud:
                        self.allClouds[c] = True
                print "FAILURE IS NEW, STORING; NOW", len(self.failures), "DISTINCT FAILURES"

    def prepare(self):
        # parse args
        args = BaseTester.parse_args(self.sysargs)

        # make config
        self.config = BaseTester.make_config(args)

        # update config with sut settings
        self.config.ignoreprops = self.sut.getCheckProperties()
        self.config.timeout = self.sut.getTimeout()
        self.config.uncaught = self.sut.getUncaughtFailures()

        print('Random testing using config={}'.format(self.config))

    def run(self, sut):
        if sut is None:
            print "Please specify a sut before running test."
            return
        self.sut = sut

        # parse args and make config
        self.prepare()

        # test sut
        R = random.Random(self.config.seed)

        start = time.time()
        elapsed = time.time() - start

        failCount = 0
        quickCount = 0
        repeatCount = 0
        failures = []
        cloudFailures = []

        if self.config.gendepth:
            self.failCloud = {}
            self.allClouds = {}

        if self.config.logging:
            self.sut.setLog(self.config.logging)

        tacts = self.sut.actions()
        a = None
        sawNew = False

        nops = 0
        ntests = 0
        reduceTime = 0.0
        opTime = 0.0
        checkTime = 0.0
        guardTime = 0.0
        restartTime = 0.0

        checkResult = True

        if self.config.total:
            fulltest = open("fulltest.txt", 'w')

        if self.config.verbose:
            print "ABOUT TO START TESTING"
            sys.stdout.flush()

        while (self.config.maxtests == -1) or (ntests < self.config.maxtests):
            if self.config.verbose:
                print "STARTING TEST", ntests
                sys.stdout.flush()
            ntests += 1

            startRestart = time.time()
            self.sut.restart()
            restartTime += time.time() - startRestart
            test = []

            if self.config.total:
                fulltest.write("<<RESTART>>\n")

            if self.config.replayable:
                currtest = open("currtest.txt", 'w')

            for s in xrange(0, self.config.depth):
                if self.config.verbose:
                    print "GENERATING STEP", s

                startGuard = time.time()
                acts = tacts
                while True:
                    elapsed = time.time() - start

                    if elapsed > self.config.timeout:
                        break

                    tryStutter = (a != None)
                    if tryStutter:
                        if (self.config.stutter == None) and (not self.config.greedyStutter):
                            tryStutter = False
                    if tryStutter:
                        if (self.config.stutter == None) or (R.random() > self.config.stutter):
                            tryStutter = False
                        if (self.config.greedyStutter) and sawNew:
                            print "TRYING TO STUTTER DUE TO COVERAGE GAIN"
                            tryStutter = True
                    if not tryStutter:
                        if len(acts) == 1:
                            p = 0
                        else:
                            p = R.randint(0, len(acts) - 1)
                        a = acts[p]
                    if a[1]():
                        break
                    else:
                        a = None
                    acts = acts[:p] + acts[p + 1:]
                guardTime += time.time() - startGuard
                elapsed = time.time() - start
                if elapsed > self.config.timeout:
                    print "STOPPING TEST DUE TO TIMEOUT, TERMINATED AT LENGTH", len(test)
                    break

                if tryStutter:
                    print "STUTTERING WITH", a[0]
                test.append(a)
                nops += 1

                if self.config.replayable:
                    currtest.write(a[0] + "\n")
                    currtest.flush()

                if self.config.total:
                    fulltest.write(a[0] + "\n")
                    fulltest.flush()

                if self.config.verbose:
                    print "ACTION:", self.sut.prettyName(a[0])

                startOp = time.time()
                stepOk = self.sut.safely(a)
                if self.sut.warning() != None:
                    print "SUT WARNING:", self.sut.warning()
                opTime += (time.time() - startOp)
                if tryStutter:
                    print "DONE STUTTERING"
                if (not self.config.uncaught) and (not stepOk):
                    self.handle_failure(test, "UNCAUGHT EXCEPTION", False)
                    if not self.config.multiple:
                        print "STOPPING TESTING DUE TO FAILED TEST"
                    break

                startCheck = time.time()
                if not self.config.ignoreprops:
                    checkResult = self.sut.check()
                    checkTime += time.time() - startCheck
                if not checkResult:
                    self.handle_failure(test, "PROPERLY VIOLATION", True)
                    if not self.config.multiple:
                        print "STOPPING TESTING DUE TO FAILED TEST"
                    break

                elapsed = time.time() - start
                if self.config.running:
                    if self.sut.newBranches() != set([]):
                        print "ACTION:", a[0], tryStutter
                        for b in self.sut.newBranches():
                            print elapsed, len(self.sut.allBranches()), "New branch", b
                        sawNew = True
                    else:
                        sawNew = False
                    if self.sut.newStatements() != set([]):
                        print "ACTION:", a[0], tryStutter
                        for s in self.sut.newStatements():
                            print elapsed, len(self.sut.allStatements()), "New statement", s
                        sawNew = True
                    else:
                        sawNew = False

                if elapsed > self.config.timeout:
                    print "STOPPING TEST DUE TO TIMEOUT, TERMINATED AT LENGTH", len(test)
                    break

            if self.config.replayable:
                currtest.close()
            if self.config.quickTests:
                if (self.sut.newCurrBranches() != set([])) or (self.sut.newCurrStatements() != set([])):
                    self.handle_failure(test, "NEW COVERAGE", False, newCov=True)
            if (not self.config.multiple) and (failCount > 0):
                break
            if elapsed > self.config.timeout:
                print "STOPPING TESTING DUE TO TIMEOUT"
                break

        if self.config.total:
            fulltest.close()

        if not self.config.nocover:
            self.sut.restart()
            print self.sut.report(self.config.coverfile), "PERCENT COVERED"

            if self.config.internal:
                self.sut.internalReport()

            if self.config.html:
                self.sut.htmlReport(self.config.html)

        print time.time() - start, "TOTAL RUNTIME"
        print ntests, "EXECUTED"
        print nops, "TOTAL TEST OPERATIONS"
        print opTime, "TIME SPENT EXECUTING TEST OPERATIONS"
        print guardTime, "TIME SPENT EVALUATING GUARDS AND CHOOSING ACTIONS"
        if not self.config.ignoreprops:
            print checkTime, "TIME SPENT CHECKING PROPERTIES"
            print (opTime + checkTime), "TOTAL TIME SPENT RUNNING SUT"
        print restartTime, "TIME SPENT RESTARTING"
        print reduceTime, "TIME SPENT REDUCING TEST CASES"
        if self.config.multiple:
            print failCount, "FAILED"
            print repeatCount, "REPEATS OF FAILURES"
            print len(failures), "ACTUAL DISTINCT FAILURES"
            print
            n = 0
            for (test, err) in failures:
                print "FAILURE", n
                self.sut.prettyPrintTest(test)
                n += 1
                if err != None:
                    print "ERROR:", err
                    print "TRACEBACK:"
                    traceback.print_tb(err[2])
            i = -1
            if False:  # Comparison feature normally not useful, just for researching normalization
                for test1 in failures:
                    i += 1
                    j = -1
                    for test2 in failures:
                        j += 1
                        if (j > i):
                            print "COMPARING FAILURE", i, "AND FAILURE", j
                            for k in xrange(0, max(len(test1), len(test2))):
                                if k >= len(test1):
                                    print "STEP", k, "-->", test2[k][0]
                                elif k >= len(test2):
                                    print "STEP", k, test1[k][0], "-->"
                                elif test1[k] != test2[k]:
                                    print "STEP", k, test1[k][0], "-->", test2[k][0]

        if not self.config.nocover:
            print len(self.sut.allBranches()), "BRANCHES COVERED"
            print len(self.sut.allStatements()), "STATEMENTS COVERED"


def main():
    mytester = simplerRandomTester(sys.argv[1:])

    mysut = SUT.sut()
    mysut.setUncaughtFailures(uncaught=True)
    mysut.setCheckProperties(ignoreprops=True)
    mysut.setTimeout(timeout=100)
    mysut.testWith(mytester)


if __name__ == '__main__':
    main()
