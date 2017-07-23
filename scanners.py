import argparse
import fnmatch
import os
import re

import sys
import traceback

from corrupt_checker import FileCorruptChecker, NotSupportedFormat

verbose = True
def print_v(*args, **kwargs):
    force = kwargs.pop('force', False)
    file = kwargs.get('file')
    if not verbose and not force and not file:
        return
    print(*args, **kwargs, flush=True)


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


def scan(args):
    total_scan = 0
    files_status = {}
    unknown_scan = 0
    invalid_files = {}
    total_invalid = 0
    exclude_list = []
    if args.exclude_file:
        if not os.path.exists(args.exclude_file):
            print_f('Not exists exclude file: [{}]'.format(args.exclude_file))
            sys.exit(1)
        with open(args.exclude_file, 'r') as xf:
            exclude_list = [l.strip() for l in xf.readlines() if l.strip()]
    for directory in args.dirpath:
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
                continue
            total_scan += 1
            if total_scan % 1000 == 0:
                print_f(80 * '=')
                print_f('# total_scan: {}, total_invalid: {}, not_supported: {}'.format(total_scan, total_invalid,
                                                                                        unknown_scan))
                print_f(80 * '=')
            print_v('+++ Scanning [{}] ==> '.format(f), end='')
            try:
                fc = FileCorruptChecker(f)
            except NotSupportedFormat:
                print_v('[NOT SUPPORTED]')
                unknown_scan += 1
                continue
            fs = files_status.setdefault(fc.name, [0, 0])
            if fc.is_valid():
                fs[0] += 1
                print_v('[VALID]')
            else:
                fs[1] += 1
                total_invalid += 1
                print_v('[INVALID]')
                invalid_files.setdefault(fc.name, []).append(f)
    print_f('##########################################################')
    print_f('#                      Finished!                         #')
    print_f('##########################################################')
    print_f('====================== Summary: ==========================')
    print_f('-- Total files scanned: {}'.format(total_scan))
    print_f('-- Total not supported files: {}'.format(unknown_scan))
    print_f('-- Total invalid files: {}'.format(total_invalid))
    for n, fs in files_status.items():
        print_f('---- {} ==> VALID: {}, INVALID: {}'.format(n, fs[0], fs[1]))
    print_f('==========================================================')
    output_file = args.outpath
    if output_file:
        output_file = open(output_file, 'w')
    invalid_files_count = sum(len(f) for f in invalid_files.values())
    if len(invalid_files) > 0:
        print_v('.... List of invalid files: ({} files) ....'.format(invalid_files_count), file=output_file)
        for n, files in invalid_files.items():
            for f in files:
                print_v(f, file=output_file)
    output_file and output_file.close()


def main():
    global verbose
    parser = argparse.ArgumentParser(description='Twitterypt CLI.')
    parser.add_argument('dirpath', type=str, nargs='+', help='directory path to scan')
    parser.add_argument('-x', '--exclude-file', dest='exclude_file', action='store',
                        help='file contains list of exclude files pattern')
    parser.add_argument('-o', '--out', dest='outpath', action='store', help='directory path to save invalid files path')
    parser.add_argument('--noverbose', dest='no_verbose', action='store_true', help='verbose the steps')

    args = parser.parse_args()
    if args.no_verbose:
        verbose = False

    scan(args)


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
