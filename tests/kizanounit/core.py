

import unittest

class TestCore(unittest.TestCase):
  def setUp(self):
    pass

  def testLog(self):
    import kizano
    log = kizano.getLogger(__name__, 10)
    log.error('ERROR')
    log.warn('WARNING')
    log.info('INFO')
    log.debug('DEBUG')
    log.info('__REALLY_LONG_MESSAGE__' * 2849)

  def tearDown(self):
    pass
