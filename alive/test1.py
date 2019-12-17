import multiprocessing
from time import sleep
from random import randint, seed
from mpclass import mp
import logging
import logger_setup
mod_name = 'ATIC'
logger = logging.getLogger(mod_name)

seed(2)
def worker(num):
    """thread worker function"""
    sl_time = randint(0,5)
    sleep(sl_time)
    print ('Worker:', num, ' sleep was ', sl_time)
    return

if __name__ == '__main__':
    jobs = []
    manager = multiprocessing.Manager()
    d = manager.dict()
    # for i in range(5):
    #     p = multiprocessing.Process(target=worker, args=(i,))
    #     jobs.append(p)

    # for p in jobs:
    #     p.start()

    jobs = []
    nodes = [ ('ATIC-005', 'WCM'), ('QA-001', 'SMM') ]
    a = mp(d)
    for i in nodes:
        p = multiprocessing.Process(target=a.connect, args=(i))
        jobs.append(p)
        p.start()
        sleep(2)
        print ("\n\nStatus1:", a.printStatus())


    # for p in jobs:
    #     print ("starting",p)
    #     p.start()

    # for p in jobs:
    #     print('terminating', p)
    #     p.terminate()

    for p in jobs:
        print('joining', p)
        p.join()

    print ("\n\nStatus:", a.printStatus())
    print ('d', d)