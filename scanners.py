from xlrd import open_workbook, XLRDError


def test_book(filename):
    try:
        open_workbook(filename)
    except XLRDError:
        return False
    else:
        return True
