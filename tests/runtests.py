#!/usr/bin/env python3

import os

global UNIT_TESTING
UNIT_TESTING = 1

# Core: Logging, config and utils
import kizano
from kizanounit.core import TestCore

if __name__ == '__main__':
    import nose
    nose.main()

