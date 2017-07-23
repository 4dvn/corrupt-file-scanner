import os
import zipfile

from PIL import Image
from docx import Document
from xlrd import open_workbook, XLRDError
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError, PdfReadWarning


class FileCorruptBaseException(Exception):
    pass


class NotSupportedFormat(FileCorruptBaseException):
    pass


def register_handler(name, formats):
    def decorator(func):
        for fmt in formats:
            FileCorruptChecker.handlers[fmt.lower()] = {'func': func, 'name': name}
        return func
    return decorator


class FileCorruptChecker(object):
    handlers = {}

    def __init__(self, filepath):
        ext = os.path.splitext(filepath)[-1].lstrip('.').lower()
        if ext not in self.handlers:
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
        return self.handlers[self.format]['name']

    def is_valid(self, **kwargs):
        check_handler = self.handlers[self.format]['func']
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


@register_handler(name='pdf', formats=['pdf'])
def pdf_check(filepath, **kwargs):
    try:
        with open(filepath, 'rb') as f:
            PdfFileReader(f)
    except (PdfReadError, TypeError):
        return False
    except PdfReadWarning:
        # TODO print the file path for this warning
        print("PdfReadWarning: \n" + filepath)
        return False
    return True


@register_handler(name='image', formats=['jpg', 'bmp', 'gif', 'jpeg', 'png', 'ico'])
def image_check(filepath, **kwargs):
    try:
        with Image.open(filepath) as im:
            im.verify()
    except (IOError, SyntaxError):
        return False
    return True

@register_handler(name='zip', formats=['zip'])
def zip_check(filepath, **kwargs):
    try:
        with zipfile.ZipFile(filepath) as z:
            z.testzip()
    except (IOError, SyntaxError):
        return False
    # TODO exception zipfile.BadZipFile
    return True