import os
import re
import sys
import xxhash
import fnmatch
import argparse
import traceback
from tinydb import TinyDB

from corrupt_checker import FileCorruptChecker, NotSupportedFormat

db = None
verbose = True
tracking = True
default_db_path = 'tracking.json'


def print_v(*args, **kwargs):
    force = kwargs.pop('force', False)
    file = kwargs.get('file')
    if not verbose and not force and not file:
        return
    print(*args, **kwargs, flush=True)


def track(data):
    # expects a dict
    if db is not None:
        db.insert(data)


def print_f(*args, **kwargs):
    kwargs['force'] = True
    return print_v(*args, **kwargs)


def dir_walker(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            yield os.path.join(root, name)


def is_exclude(filepath, exclude_list):
    for pattern in (exclude_list or []):
        pattern = re.compile(fnmatch.translate(pattern))
        if pattern.match(filepath):
            return True
    return False


def scan(dirpath, exclude_file=None, output_file=None, no_verbose=False, db_path=None, no_tracking=False,
         get_hash=False):
    global db
    global verbose
    global tracking
    verbose = not no_verbose
    tracking = not no_tracking
    total_scan = 0
    files_status = {}
    unknown_scan = 0
    invalid_files = {}
    total_invalid = 0
    exclude_list = []
    if tracking:
        # lets track files
        db_path = db_path or default_db_path
        db = TinyDB(db_path)
    if exclude_file:
        if not os.path.exists(exclude_file):
            print_f('Not exists exclude file: [{}]'.format(exclude_file))
            sys.exit(1)
        with open(exclude_file, 'r') as xf:
            exclude_list = [l.strip() for l in xf.readlines() if l.strip()]
    for directory in dirpath:
        directory = os.path.abspath(directory)
        if not os.path.exists(directory):
            print_f('Not exists path: [{}]'.format(directory))
            sys.exit(1)
        if os.path.isfile(directory):
            files = [directory]
        else:
            files = dir_walker(directory)
        for f in files:
            if is_exclude(f, exclude_list):
                print_v('!!! excluded file: [{}]'.format(f))
                track({'file': f, 'status': 'exclude', 'xxhash': xxh})
                continue
            total_scan += 1
            if total_scan % 1000 == 0:
                print_f(80 * '=')
                print_f('# total_scan: {}, total_invalid: {}, not_supported: {}'.format(total_scan, total_invalid,
                                                                                        unknown_scan))
                print_f(80 * '=')
            print_v('+++ Scanning [{}] ==> '.format(f), end='')
            if get_hash:
                with open(f, 'rb') as gh:
                    xxh = xxhash.xxh64(gh.read(4096 * 1024)).hexdigest()
            else:
                xxh = None
            try:
                fc = FileCorruptChecker(f)
            except NotSupportedFormat:
                print_v('[NOT SUPPORTED]')
                unknown_scan += 1
                track({'file': f, 'status': 'not_supported', 'xxhash': xxh})
                continue
            fs = files_status.setdefault(fc.name, [0, 0])
            is_valid = False
            try:
                is_valid = fc.is_valid()
                track({'file': f, 'status': 'valid' if is_valid else 'invalid', 'xxhash': xxh})
                print_v('[VALID]' if is_valid else '[INVALID]')
            except Exception as e:
                print_v('[INVALID] !!! Unexpected exception in validity check! [{}]'.format(e))
                track({'file': f, 'status': 'invalid'})
            if is_valid:
                fs[0] += 1
            else:
                fs[1] += 1
                total_invalid += 1
                invalid_files.setdefault(fc.name, []).append(f)

    print_v('##########################################################')
    print_v('#                      Finished!                         #')
    print_v('##########################################################')
    print_f('====================== Summary: ==========================')
    print_f('-- Total files scanned: {}'.format(total_scan))
    print_f('-- Total not supported files: {}'.format(unknown_scan))
    print_f('-- Total invalid files: {}'.format(total_invalid))
    for n, fs in files_status.items():
        print_f('---- {} ==> VALID: {}, INVALID: {}'.format(n, fs[0], fs[1]))
    print_f('==========================================================')
    if output_file:
        output_file = open(output_file, 'w')
    invalid_files_count = sum(len(f) for f in invalid_files.values())
    if len(invalid_files) > 0:
        print_f('.... List of invalid files: ({} files) ....'.format(invalid_files_count), file=output_file)
        for n, files in invalid_files.items():
            for f in files:
                print_f(f, file=output_file)
    output_file and output_file.close()


def main():
    global verbose
    parser = argparse.ArgumentParser(description='Corrupt file scanner')
    parser.add_argument('dirpath', type=str, nargs='+', help='directory path to scan')
    parser.add_argument('-x', '--exclude-file', dest='exclude_file', action='store',
                        help='file contains list of exclude files pattern')
    parser.add_argument('-o', '--out', dest='outpath', action='store', help='directory path to save invalid files path')
    parser.add_argument('--noverbose', dest='no_verbose', action='store_true', help='verbose the steps')
    parser.add_argument('--notracking', dest='no_tracking', action='store_true', help='no track the files status in db')
    parser.add_argument('--use-hashing', dest='use_hashing', action='store_true',
                        help='a flag to use hashing in calculate file status')
    parser.add_argument('--tracking-db', dest='tracking_db', action='store', help='db path to save the tracking status')

    args = parser.parse_args()
    scan(args.dirpath, exclude_file=args.exclude_file, output_file=args.outpath, no_verbose=args.no_verbose,
         no_tracking=args.no_tracking, get_hash=args.use_hashing, db_path=args.tracking_db)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_f('Canceled!')
        sys.exit(2)
    except Exception as e:
        print_f('Unexpected Exception:')
        traceback.print_exc()
        sys.exit(3)
