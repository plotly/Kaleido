#!/usr/bin/env python
from __future__ import print_function
import time
import datetime
import sys

def main():
    # All this to get a POSIX timestamp integer
    print(int(time.mktime(datetime.datetime.now().timetuple())))
    return 0

if __name__ == '__main__':
  sys.exit(main())
