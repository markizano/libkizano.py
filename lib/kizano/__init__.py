
import os
from kizano.logger import getLogger
import kizano.utils as utils
log = getLogger(__name__)

class Config(object):
    '''
    Configuration object that tracks config in /etc/${APP_NAME}/config.yml and
    in ~/.config/${APP_NAME}/config.yml

    Returns a cached version of the config if we've asked the filesystem for it before for
    faster IO in subsequent reads.

    Reads system config in `/etc`, then overlays user config on top of that.
    Arrays are appended when encountered.
    '''

    APP_NAME = 'kizano'
    __CONFIGCACHE = {}

    @staticmethod
    def getConfig():
        """
        Static method for getting configuration for this app, be it cron, client or server.
        """
        if Config.__CONFIGCACHE:
            log.debug('Cache-HIT: Returning config from cache')
            return Config.__CONFIGCACHE
        cfgfiles = [
          os.path.join(os.path.sep, 'etc', Config.APP_NAME, 'config.yml'),
          os.path.join(os.environ['HOME'], '.config', Config.APP_NAME, 'config.yml')
        ]
        for cfgfile in cfgfiles:
            try:
                cfg = utils.read_yaml(cfgfile)
                log.info(f'Found and loaded {cfgfile}')
                Config.__CONFIGCACHE = utils.dictmerge(Config.__CONFIGCACHE, cfg)
            except Exception as e:
                log.info(f'Did not load {cfgfile}, reason={e}')
                continue
        log.debug(f'Cache-Miss: Config loaded - {Config.__CONFIGCACHE}')
        return Config.__CONFIGCACHE

getConfig = Config.getConfig
