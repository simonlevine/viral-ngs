#!/usr/bin/env python

# * Preamble

"""
Utilities for dealing with files.
"""

__author__ = "tomkinsc@broadinstitute.org"
__commands__ = []

import argparse
import logging
import os
import collections

import util.cmd
import util.file
import util.misc

log = logging.getLogger(__name__)

# * merge_tarballs

# ==============================
# ***  merge_tarballs   ***
# ==============================

def merge_tarballs(out_tarball, in_tarballs, threads=None, extract_to_disk_path=None, pipe_hint_in=None, pipe_hint_out=None):
    ''' Merges separate tarballs into one tarball
        data can be piped in and/or out
    '''
    util.file.repack_tarballs(out_tarball, in_tarballs, threads=threads, extract_to_disk_path=extract_to_disk_path, pipe_hint_in=pipe_hint_in, pipe_hint_out=pipe_hint_out)
    return 0
def parser_merge_tarballs(parser=argparse.ArgumentParser()):
    parser.add_argument(
        'out_tarball', 
        help='''output tarball (*.tar.gz|*.tar.lz4|*.tar.bz2|-);
                compression is inferred by the file extension.
        Note: if "-" is used, output will be written to stdout and
         --pipeOutHint must be provided to indicate compression type
         when compression type is not gzip (gzip is used by default).
        ''')
    parser.add_argument(
        'in_tarballs', nargs='+',
        help=('input tarballs (*.tar.gz|*.tar.lz4|*.tar.bz2)')
    )
    parser.add_argument('--extractToDiskPath',
                        dest="extract_to_disk_path",
                        help='If specified, the tar contents will also be extracted to a local directory.')
    parser.add_argument('--pipeInHint',
                        dest="pipe_hint_in",
                        default="gz",
                        help='If specified, the compression type used is used for piped input.')
    parser.add_argument('--pipeOutHint',
                        dest="pipe_hint_out",
                        default="gz",
                        help='If specified, the compression type used is used for piped output.')
    util.cmd.common_args(parser, (('threads', None), ('loglevel', None), ('version', None), ('tmp_dir', None)))
    util.cmd.attach_main(parser, merge_tarballs, split_args=True)
    return parser
__commands__.append(('merge_tarballs', parser_merge_tarballs))

# =======================

# * json_to_org

def _json_to_org(val, org_file, depth=1, heading='root'):
    """Transform a parsed json structure to an Org mode outliner file (see https://orgmode.org/ ).
    """
    with open(org_file, 'w') as out:
        def _recurse(val, heading, depth):
            def _header(s): out.write('*'*depth + ' ' + str(s) + '\n')
            def _line(s): out.write(' '*depth + str(s) + '\n')
            out.write('*'*depth + ' ' + heading)
            if isinstance(val, list):
                out.write(' - list of ' + str(len(val)) + '\n')
                if len(val):
                    for i, v in enumerate(val):
                        _recurse(v, heading=str(i), depth=depth+2)
            elif util.misc.maps(val, '$git_link'):
                rel_path = val['$git_link']
                out.write(' - [[file:{}][{}]]\n'.format(rel_path, os.path.basename(rel_path)))
            elif util.misc.is_str(val) and os.path.isabs(val) and os.path.isdir(val):
                out.write(' - [[file+emacs:{}][{}]]\n'.format(val, os.path.basename(val)))
            elif isinstance(val, collections.Mapping):
                out.write(' - map of ' + str(len(val)) + '\n')
                if len(val):
                    for k, v in val.items():
                        _recurse(v, heading='_'+k+'_', depth=depth+2)
            else:
                out.write(' - ' + str(val) + '\n')
        _recurse(val=val, heading=heading, depth=depth)
# end: def _json_to_org(val, org_file, depth=1, heading='root')

def json_to_org(json_fname, org_fname=None):
    """Transform a parsed json structure to an Org mode outliner file (see https://orgmode.org/ ).
    """
    org_fname = org_fname or util.file.replace_ext(json_fname, '.org')
    _json_to_org(val=util.misc.json_loadf(json_fname), org_file=org_fname)

def parser_json_to_org(parser=argparse.ArgumentParser()):
    parser.add_argument('json_fname', help='json file to import')
    parser.add_argument('org_fname', help='org file to output; if omitted, defaults to json_fname with .json replaced by .org',
                        nargs='?')
    util.cmd.attach_main(parser, json_to_org, split_args=True)
    return parser

__commands__.append(('json_to_org', parser_json_to_org))

# =======================

def full_parser():
    return util.cmd.make_parser(__commands__, __doc__)


if __name__ == '__main__':
    util.cmd.main_argparse(__commands__, __doc__)
