## -*- coding: utf-8 -*-
from __future__ import division
from zipfile import ZipFile
import fnmatch
import os
import time
import xml.etree.ElementTree as ET
import re

#compares files to see if they are exact clones or almost exact clones (without name changes)
""" removes initialisation when checking patterns, which allows it to finish """
""" does not recalculate the Jaccard Index """

##################################################


def parse(filename):
    """ parse the xml file """
    root = ET.parse(filename).getroot()
    return root


def get_filenames(bum_files, pathl, root1):
    """ returns dictionary of filenames """
    filenames = {}
    for i, files in enumerate(bum_files):
        filename = files[pathl+1:len(files)-4]
        filenames[root1[i]] = filename
    return filenames


def get_roots(bum_files):  
    """ gets the roots of all the files """    
    files_root = [parse(files) for files in bum_files]
    # files_root = map(parse, bum_files)
    return files_root


##################################################


def find_events(root, name, maclevel):
    """ return a dictionary which has the machine name,event name,all the actions and guards of each event 
        invariant is a boolean (maclevel) so it can be easily included if you need to"""
    namespace = 'org.eventb.core'
    mapping = {
        namespace + '.invariant': '.predicate',
        namespace + '.guard': '.predicate',
        namespace + '.action': '.assignment'
    }
    tags = [namespace + '.action', namespace + '.guard']
    dct = {'macname': name}
    if (maclevel):
        tags.append(namespace + '.invariant')
        for event in root.findall(namespace + '.event'):
            evtname = event.attrib[namespace + '.label']
            if evtname != 'INITIALISATION':
                for child in event:
                    if child.tag in tags:
                        x = '{}_{}'.format(evtname, child.attrib[namespace + '.label'])
                        y = child.attrib[namespace + mapping[child.tag]]
                        z = (x, y)
                        dct.setdefault(name, []).append(z)
    else:
        for event in root.findall(namespace + '.event'):
            evtname = event.attrib[namespace + '.label']
            dct.setdefault('eventnames', []).append(evtname)
            dct.setdefault(evtname, [])
            for child in event:
                if child.tag in tags:
                    x = child.attrib[namespace + '.label']
                    y = child.attrib[namespace + mapping[child.tag]]
                    z = (x, y)
                    dct.setdefault(evtname, []).append(z)

    return dct
    return dct


def check_event(dct1, dct2):
    """ checks events and subsets """
    results = check_subsets(dct1, dct2)
    num = sum(map(sum, results))
    print '{} and {}:'.format(dct1['macname'], dct2['macname']),
    mac1, mac2 = dct1['eventnames'], dct2['eventnames']
    if num == 0.0:      
        print ' No similarities'
    elif (len(mac1) == len(mac2)) and (num == len(mac1)):
        """ so they are the same, but may have different event names and machines names """
        print ' Are the exact same'
    else:
        """ prints everything the even columns with just 0.0 """
        print ""
        ls1 = max(map(len, mac1))
        ls2 = max(map(len, mac2))
        longstr = str((max(ls1, ls2)) + 1)
        form = "{:^" + longstr + "}"
        row_format = form * (len(mac1) + 1)
        print row_format.format("", *mac1)
        zipped = zip(mac2, results)
        '''c=0'''
        for event, row in zipped:
            """ only prints out machines that have some similarities for the second machine
            this makes it a bit easier to read, in my opinion """
            '''if sum(zipped[c][1]) != 0:
                print row_format.format(event, *row)
            c+=1'''
            print row_format.format(event, *row)

########################################################################


def jaccard_index(a, b):
    """" card (a intersection b) / card(a) + card(b) - card (a intersection b) """
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        #return 2
        return 0.0
    else: 
        sa = set(a)
        iab = len(sa.intersection(b))
        return ((iab) / (la + lb - iab))

    
def check_subsets(dct1, dct2):
    """ not looking at event names just if guards and actions are the same """
    mac1, mac2 = dct1['eventnames'], dct2['eventnames']
    li = [[] for x in xrange(len(mac2))]
    for c, event2 in enumerate(mac2):
        for event1 in mac1:
            tji = jaccard_index(dct1[event1], dct2[event2]) 
            """if tji == 2 and not(event1=='INITIALISATION' and event2=='INITIALISATION') and event1==event2:
                tji = 1
            elif tji == 2:
                tji = 0"""
            li[c].append(tji)            
    return li


#############################################################

        
def compare_machines(bum_files_roots, filenames_dict, funct):
    """ compares both machines """
    for i, r1 in enumerate(bum_files_roots[:-1]):
        for rnext in bum_files_roots[i+1:]:
            funct(r1, rnext, filenames_dict)


def check_machines(r1, r2, filename_dict):
    """ this checks if machines are the same, and returns the Jaccard Index tables """
    l1 = find_events(r1, filename_dict[r1], False)
    l2 = find_events(r2, filename_dict[r2], False)
    check_event(l1, l2)


def check_pattern_mac(r1, r2, filename_dict):
    """ This checks the pattern by machine """
    l1 = find_events(r1, filename_dict[r1], True)
    l2 = find_events(r2, filename_dict[r2], True)
    macn1, macn2 = l1['macname'], l2['macname']
    mac1, mac2 = l1[macn1], l2[macn2]
    print '###################################'
    print "{} and {}".format(macn1, macn2)
    print '###################################'
    nl = pattern_votes(mac1, mac2)
    if nl != 0 and len(nl)>0:
        if len(nl)>1:
            check =[]
            for val in nl:
                check.append(Matching(val[0], val[1], val[2]))
            #matrixCompare(check)
            print 'Best matching:'
            (m,v) = findBestMatching([], 0, check)
            #print m[0].matches 
            print '\n'.join(map(str,m))
            print 'Total votes =', v
    elif nl == 0:
        """ The have the same action and guards, but the event names and mac names may be different """
        print " The machines events are the same"
    #elif len(nl) == 0:
        """ A lot of machines can have no similarities and it doesnt add new information """
        #print " The machines events have no similarities"
    

def check_pattern_event(r1, r2, filename_dict):
    """ goes through and gets list of patterns and votes for the action/guard """
    l1 = find_events(r1, filename_dict[r1], False)
    l2 = find_events(r2, filename_dict[r2], False)
    mac1, mac2 = l1['eventnames'], l2['eventnames']
    print '***********************************'
    print "{} : {}".format(l1['macname'], mac1)
    print "{} : {}".format(l2['macname'], mac2)
    print '***********************************'
    matches = []
    ln = []
    for event1 in mac1:
        if not(event1 == 'INITIALISATION'):
            for event2 in mac2:
                if not(event2 == 'INITIALISATION'):
                    nl = pattern_votes(l1[event1], l2[event2])
                    print "{} and {} :".format(event1, event2),

                    if nl != 0 and len(nl)>0:
                        """ if it has only one match then that is the best match
                            and it gets printed out in a list and the algorithm is not run """
                        ln.append(nl)
                        print " {}".format(nl)
                        if len(nl)>1:
                            check =[]
                            for val in nl:
                                check.append(Matching(val[0], val[1], val[2]))
                            #matrixCompare(check)
                            print 'Best matching:'
                            (m,v) = findBestMatching([], 0, check)
                            print '\n'.join(map(str,m))
                            print 'Total votes =', v
                    elif nl == 0:
                        """ The have the same action and guards, but the event names and mac names may be different """
                        print " The machines events are the same"
                    #elif len(nl) == 0:
                        #print " The machines events have no similarities"


###############################################################


pattern = re.compile('\w+', re.UNICODE)
def get_pattern(s1):
    """ changes varibale names and return new string and ordered list of var """
    s1 = re.sub(r"\s+", "", s1, flags=re.UNICODE)
    it = pattern.finditer(s1)
    orderlist = []
    varorder = []
    snew = s1
    for i,match in enumerate(it):
        sp = match.span()
        sp1, sp2 = sp[0], sp[1]
        old = s1[sp1:sp2]
        var = 'v{}v'.format(str(i))
        varorder.append(var)
        if not(str(old) in orderlist):
            orderlist.append(str(old))
        snew = snew.replace(old, var)
    return snew, orderlist, varorder


def pattern_votes(event1, event2):
    """ goes through each event and compares the new renaming and returns the votes and var """
    votelist = {}
    listtocheck = []
    keylist = []
    ji = jaccard_index(event1, event2)
    if ji == 1.0:
        return 0
    else:
        for a1 in event1:
            check1, o1, v1 = get_pattern(a1[1])
            for a2 in event2:
                check2, o2, v2 = get_pattern(a2[1])
                check = (check1 == check2)
                key = [o1, o2]
                if check and not(key in keylist):
                    keylist.append(key)
                    i = keylist.index(key)
                    votelist[i] = 1
                elif check: 
                    i = keylist.index(key)
                    votelist[i] += +1
        for i, item in enumerate(keylist):
            item.append(votelist[i])
            listtocheck.append(item)
        return listtocheck


################################################################

""" James' best_matching.py """

class Matching :
    """ A Matching is two (equal-length) variable lists and a vote total """
    def __init__(self, varList1, varList2, votes) :
        assert len(varList1) == len(varList2), "Substs must match up"
        assert votes > 0, "Votes must be positive"
        self.varList1 = varList1
        self.varList2 = varList2
        self.matches = dict(zip(varList1,varList2))
        self.votes = votes
    def isCompatibleWithAll(self, otherList) :
        return reduce(lambda r,m: r and self.isCompatibleWith(m),
                      otherList, True)
    def isCompatibleWith(self, other):
        return self.findFirstIncompatability(other) is None
    def findFirstIncompatability(self, other):
        for (v1,v2) in self.matches.iteritems():
            if other.matches.get(v1, v2) != v2 :
                return v1  # Incompatibility on this variable
        return None # No incompatibility
    def __str__(self) :
        s = ''
        for (v1,v2) in self.matches.iteritems():
            s += '(%s,%s) ' % (v1,v2)
        s += '[%d]' % self.votes
        return s


def matrixCompare(matchList) :
    """ Compare each matching in the given list with all the others """
    print 'Matchings:'
    for (i,m) in enumerate(matchList):
        print '%5d: %s' % (i,m)
    print 'Incompatibilities:'
    for i in range(len(matchList)) :
        print '%5d: ' % i,
        for j in range(len(matchList)) :
            iVar = matchList[i].findFirstIncompatability(matchList[j]) 
            if not iVar : iVar = "-"
            print '%5s ' % iVar,
        print ''


def findBestMatching(doneList, doneVotes, todoList) :
    """ Find the sublist of todoList that has the higest total votes,
        and all of whose matchings are compatible.  (Recursive search).
        Return that sublist and its total votes. 
    """
    if len(todoList) == 0 :
        return (doneList, doneVotes)
    (nextItem, restList) = (todoList[0], todoList[1:])
    # See what's the best if nextItem is omitted:
    (newList, newVotes) = findBestMatching(doneList, doneVotes, restList)
    # See what's the best if nextItem is kept
    if nextItem.isCompatibleWithAll(doneList) :
        (altList, altVotes) = findBestMatching(doneList+[nextItem],
                                               doneVotes+nextItem.votes,
                                               restList)
        if altVotes > newVotes :
            (newList, newVotes) = (altList, altVotes)
    return (newList, newVotes)


################################################################


if __name__ == "__main__":
    ####
    start_time = time.time()
    ####

    path = raw_input('Please give a file path:')
    #path = '/home/ct215005/SPUR/attempts/tests/Show subsets'
    bum_files_zip = []
    bum_files = []
    roots = []
    bum_files_zip = []
    roots_zip = []
    for root, dirs, files in os.walk(path):
        for filename in (fnmatch.filter(files, '*.zip')):
            filezip = ZipFile(os.path.join(root, filename))
            for f in fnmatch.filter(ZipFile.namelist(filezip), '*.bum'):
                fpath = os.path.join(root, f)
                fileopen = filezip.open(f)
                froot = parse(fileopen)
                bum_files_zip.append(fpath)
                roots_zip.append(froot)
        for filename in fnmatch.filter(files, '*.bum'):
            bum_files.append(os.path.join(root, filename))

    print("--- %s seconds ---" % (time.time() - start_time))
    roots = get_roots(bum_files)
    roots += roots_zip
    bum_files += bum_files_zip
    print 'NO. OF FILES = {num_files}'.format(num_files=len(bum_files))

    filenames = get_filenames(bum_files, len(path), roots)

    compare_machines(roots, filenames, check_machines)

    #####
    print("--- %s seconds ---" % (time.time() - start_time))
    #####

    print "RENAMED CLONES"
    compare_machines(roots, filenames, check_pattern_event)

    #####
    print("--- %s seconds ---" % (time.time() - start_time))
    #####
    
    print "*##* Check pattern by machine *##*"
    compare_machines(roots, filenames, check_pattern_mac)

    #####
    print("--- %s seconds ---" % (time.time() - start_time))
    #####
