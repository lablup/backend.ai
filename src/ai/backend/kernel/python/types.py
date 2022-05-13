from namedlist import namedtuple, FACTORY


InputRequest = namedtuple('InputRequest', [
    ('is_password', False),
])

ControlRecord = namedtuple('ControlRecord', [
    ('event', None),
])

CompletionRecord = namedtuple('CompletionRecord', [
    ('matches', FACTORY(list)),
])

ConsoleRecord = namedtuple('ConsoleRecord', [
    ('target', 'stdout'),  # or 'stderr'
    ('data', ''),
])

MediaRecord = namedtuple('MediaRecord', [
    ('type', None),  # mime-type
    ('data', None),
])

HTMLRecord = namedtuple('HTMLRecord', [
    ('html', None),  # raw HTML string
])
