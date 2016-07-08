from __future__ import division
import fnmatch
import os
import time
import xml.etree.ElementTree as ET

#compares files to see if they are exact clones or almost exact clones (without name changes)

##################################################


def parse(filename):        
    """parse the xml file"""
    root = ET.parse(filename).getroot()
    return root


def get_filenames(bum_files, pathl, root1):
    """returns dictionary of filenames"""
    filenames = {}
    for i, files in enumerate(bum_files):
        filename = files[pathl+1:len(files)-4]
        filenames[root1[i]] = filename
    return filenames


def get_roots(bum_files):  
    """gets the roots of all the files"""    
    files_root = [parse(files) for files in bum_files]
    # files_root = map(parse, bum_files)
    return files_root

##################################################


def find_events(root, name):  
    """return a dictionary which has the machine name,event name,all the actions and guards of each event"""
    namespace = 'org.eventb.core'
    mapping = {
        namespace + '.guard': '.predicate',
        namespace + '.action': '.assignment'
    }

    dct = {'macname': name}
    for event in root.findall(namespace + '.event'):
        evtname = event.attrib[namespace + '.label'].encode('utf-8')
        dct.setdefault('eventnames', []).append(evtname)
        dct.setdefault(evtname, [])
        for child in event:
            if child.tag == (namespace + '.action') or child.tag == (namespace + '.guard'):
                x = child.attrib[namespace + '.label'].encode('utf-8')
                y = child.attrib[namespace + mapping[child.tag]].encode('utf-8')
                z = (x, y)
                dct.setdefault(evtname, []).append(z)
    return dct


def check_event(dct1, dct2):  
    """checks events and subsets"""
    results = check_subsets(dct1, dct2)
    num = sum(map(sum, results))
    print '{} and {}:'.format(dct1['macname'], dct2['macname']),
    if num == 0.0:      
        print ' No similarities'
    else:
        print ""
        mac1, mac2 = dct1['eventnames'], dct2['eventnames']
        ls1 = max(map(len, mac1))
        ls2 = max(map(len, mac2))
        longstr = str((max(ls1, ls2)) + 1)
        form = "{:^" + longstr + "}"
        row_format = form * (len(mac1) + 1)
        print row_format.format("", *mac1)
        for event, row in zip(mac2, results): 
            print row_format.format(event, *row)
########################################################################


def jaccard_index(a, b): 
    """"card (a intersection b) / card(a) + card(b) - card (a intersection b)"""
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    else: 
        sa = set(a)
        iab = len(sa.intersection(b))
        return ((iab) / (la + lb - iab))

    
def check_subsets(dct1, dct2):  
    """"not looking at event names just if guards and actions are the same"""
    mac1, mac2 = dct1['eventnames'], dct2['eventnames']
    #ji = {}
    li = [[] for x in xrange(len(mac2))]
    for c, event2 in enumerate(mac2):
        for event1 in mac1:
            tji = jaccard_index(dct1[event1], dct2[event2]) 
            '''if tji == 2 and not(event1=='INITIALISATION' and event2=='INITIALISATION') and event1==event2:
                tji = 1
            elif tji == 2:
                tji = 0'''
            #ji[(event1,event2)] = tji
            li[c].append(tji)
            
    return li

#############################################################

        
def compare_machines(bum_files_roots, filenames_dict):
    for i, r1 in enumerate(bum_files_roots[:-1]):
        for rnext in bum_files_roots[i+1:]:
            check_machines(r1, rnext, filenames_dict)


def check_machines(r1, r2, filename_dict):
    l1 = find_events(r1, filename_dict[r1])
    l2 = find_events(r2, filename_dict[r2])
    check_event(l1, l2)

###############################################################

if __name__ == "__main__":
    ####
    start_time = time.time()
    ####

    path = raw_input('Please give a file path:')
    #path = '/home/ct215005/SPUR/attempts/tests/Show subsets'
    bum_files = []
    for root, dirs, files in os.walk(path):
        for filename in fnmatch.filter(files, '*.bum'):
            bum_files.append(os.path.join(root, filename))

    print 'NO. OF FILES = {num_files}'.format(num_files=len(bum_files))
    print("--- %s seconds ---" % (time.time() - start_time))
    roots = get_roots(bum_files)

    filenames = get_filenames(bum_files, len(path), roots)

    compare_machines(roots, filenames)
    #####
    print("--- %s seconds ---" % (time.time() - start_time))
    #####
