
import os
import sys
import logging
from logging.handlers import SysLogHandler

class LocalSyslogHandler(SysLogHandler):
    def emit(self, record):
        '''
        Takes a log message and breaks it out into multiple messages if it exceeds 64k for syslogger.
        Overload function since the original will throw an error if message is over the limit.
        '''
        maxlen = 2015 if sys.platform == 'darwin' else 65502
        mesg = record.getMessage()
        if len(mesg) > maxlen:
            while len(mesg) > maxlen:
                record.msg = mesg[0:maxlen]
                SysLogHandler.emit(self, record)
                mesg = mesg[maxlen:]
        else:
            SysLogHandler.emit(self, record)

def getLogger(name, log_level=None):
    '''
    Get a logger by the name provided. Set the log_level if you provide the second argument.
    If not, ask the environment for $LOG_LEVEL. If not, default to DEBUG.
    Also attaches a syslog handler that will handle large strings and stream the message
    to the syslog endpoint.
    @param log_level {enum:string} One of the logger levels.
    @return {@logging.getLogger()}
    '''
    log_levels = ['DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL']
    log_level_map = dict([ (_ll, getattr(logging, _ll)) for _ll in log_levels ])
    if not log_level:
        #@throws KeyError if $LOG_LEVEL is set to invalid log level as described
        # by above array $log_level_map
        log_level = log_level_map[ os.getenv('LOG_LEVEL', 'DEBUG').upper() ]
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(PID=%(process)d, %(levelname)s) %(message)s')

    syslog_handler = LocalSyslogHandler()
    syslog_handler.setLevel(log_level)
    logger.addHandler(syslog_handler)

    return logger
