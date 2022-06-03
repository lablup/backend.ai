from contextlib import closing
from io import StringIO
import logging
from logging.handlers import QueueHandler


class LogQHandler(QueueHandler):
    def enqueue(self, record):
        with closing(StringIO()) as buf:
            print(self.formatter.format(record), file=buf)
            if record.exc_info is not None:
                print(self.formatter.formatException(record.exc_info), file=buf)
            self.queue.put_nowait((
                b'stderr',
                buf.getvalue().encode('utf8'),
            ))


class BraceMessage:

    __slots__ = ('fmt', 'args')

    def __init__(self, fmt, args):
        self.fmt = fmt
        self.args = args

    def __str__(self):
        return self.fmt.format(*self.args)


class BraceStyleAdapter(logging.LoggerAdapter):

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra)

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger._log(level, BraceMessage(msg, args), (), **kwargs)


def setup_logger(log_queue, log_prefix, debug):
    # configure logging to publish logs via outsock as well
    loghandlers = [logging.StreamHandler()]
    if not debug:
        loghandlers.append(LogQHandler(log_queue))
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format=log_prefix + ': {message}',
        style='{',
        handlers=loghandlers,
    )
