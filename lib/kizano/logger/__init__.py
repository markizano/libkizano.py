
import os
import sys
import socket
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
                super().emit(record)
                mesg = mesg[maxlen:]
        else:
            super().emit(record)

def getLogger(name, log_level=None, log_format='standard'):
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
    logFormats = {
      'standard': '%(asctime)s %(name)s.%(funcName)s(PID=%(process)d %(levelname)-8s) %(message)s',
      'json': '{ "time": "%(asctime)s", "function": "%(name)s.%(funcName)s", "pid": "%(process)d", "level": "%(levelname)s", "message", "%(message)s" }',
      'csv': '%(asctime)s,%(name)s.%(funcName)s,%(levelname)s,%(message)s',
    }
    format_str = logFormats.get(log_format, 'standard')
    logging.basicConfig(format=format_str, datefmt='%F %T')
    root = logging.getLogger()
    # AVoid duplicate log messages by removing root logger handlers.
    for h in root.handlers:
        root.removeHandler(h)

    formatter = logging.Formatter(format_str)
    if os.path.exists('/dev/log'):
        syslog_handler = LocalSyslogHandler(address=('/dev/log'), facility=SysLogHandler.LOG_DAEMON, socktype=socket.SOCK_STREAM)
    elif os.path.exists('/var/run/syslog'):
        syslog_handler = LocalSyslogHandler(address='/var/run/syslog', facility=SysLogHandler.LOG_DAEMON, socktype=socket.SOCK_STREAM)
    else: # Use UDP if we can't find a local syslog socket
        syslog_handler = LocalSyslogHandler(address=('localhost', 514), facility=SysLogHandler.LOG_DAEMON, socktype=socket.SOCK_DGRAM)
    syslog_handler.setLevel(log_level)
    syslog_handler.setFormatter(formatter)

    print_handler = logging.StreamHandler(sys.stderr)
    print_handler.setLevel(log_level)
    print_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(syslog_handler)
    if sys.stderr.isatty():
        logger.addHandler(print_handler)

    return logger
