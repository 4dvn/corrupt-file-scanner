import os
from docx import Document
from xlrd import open_workbook, XLRDError


class FileCorruptBaseException(Exception):
    pass


class NotSupportedFormat(FileCorruptBaseException):
    pass


def register_handler(name, formats):
    def decorator(func):
        FileCorruptChecker.handlers[name] = func
        for fmt in formats:
            FileCorruptChecker.formats_map[fmt.lower()] = name
        return func
    return decorator


class FileCorruptChecker(object):
    handlers = {}
    formats_map = {}

    def __init__(self, filepath):
        ext = os.path.splitext(filepath)[-1].lstrip('.').lower()
        if ext not in self.formats_map:
            raise NotSupportedFormat('not supported [{}] format'.format(ext))
        self._filepath = filepath
        self._format = ext

    @property
    def filepath(self):
        return self._filepath

    @property
    def format(self):
        return self._format

    @property
    def name(self):
        return self.formats_map[self.format]

    def is_valid(self, **kwargs):
        check_handler = self.handlers[self.name]
        return check_handler(self.filepath, **kwargs)

    def __str__(self):
        return 'FileCorruptChecker<"{}">'.format(self.name)


@register_handler(name='excel', formats=['xls', 'xlsx'])
def excel_check(filepath, **kwargs):
    try:
        open_workbook(filepath)
    except XLRDError:
        return False
    return True


@register_handler(name='word', formats=['docx'])
def word_check(filepath, **kwargs):
    try:
        Document(filepath)
    except ValueError:
        return False
    return True