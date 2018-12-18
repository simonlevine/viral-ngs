'''
    Tool wrapper for accessing the Google Cloud
'''

# * imports

import logging
import collections
import os
import os.path
import subprocess
import shutil
import random
import shlex
import tempfile
import pipes
import time
import binascii

import uritools
from google.cloud import storage

import tools
import util.file
import util.misc

TOOL_NAME = 'google-cloud-storage'
TOOL_VERSION = '1.12.0'

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

# * class GCloudTool
class GCloudTool(tools.Tool):

    '''Tool wrapper for accessing the Google Cloud.
    '''

    def __init__(self, install_methods=None):
        if install_methods is None:
            install_methods = [tools.CondaPackage(TOOL_NAME, version=TOOL_VERSION, channel='conda-forge',
                                                  require_executability=False)]
        tools.Tool.__init__(self, install_methods=install_methods)
        try:
            self.storage_client = storage.Client()
        except Exception:
            self.storage_client = None
        self.bucket_name_to_bucket = {}

    def version(self):
        return TOOL_VERSION

    def get_storage_client(self):
        if self.storage_client is None:
            return storage.Client.create_anonymous_client()
        return self.storage_client

    def get_bucket(self, bucket_name):
        """Return the bucket object for given bucket name"""
        if bucket_name not in self.bucket_name_to_bucket:
            self.bucket_name_to_bucket[bucket_name] = self.get_storage_client().bucket(bucket_name)
        util.misc.chk(self.bucket_name_to_bucket[bucket_name])
        return self.bucket_name_to_bucket[bucket_name]

    def get_blob(self, gs_uri):
        """Return the blob object for given gs:// uri"""
        gs_uri_parts = uritools.urisplit(gs_uri)
        util.misc.chk(gs_uri_parts.scheme == 'gs' and gs_uri_parts.path.startswith('/') and \
                      gs_uri_parts.query is None and gs_uri_parts.fragment is None)
        bucket = self.get_bucket(gs_uri_parts.authority)
        blob = bucket.get_blob(gs_uri_parts.path[1:])
        util.misc.chk(blob)
        return blob

    def get_metadata_for_objects(self, gs_uris):
        """Get metadata for objects stored in Google Cloud Storage.

        TODO:
          - use batch request google.cloud.storage.batch.Batch
          - use 'fields' to get partial response with just the fields we want
          - parallelize
        """
        
        uri2attrs = {}
        for gs_uri in gs_uris:
            blob = self.get_blob(gs_uri)
            uri2attrs[gs_uri] = collections.OrderedDict([('md5', binascii.hexlify(blob.md5_hash.decode('base64')).upper()),
                                                         ('size', blob.size)])
        return uri2attrs

# end: class GCloudTool
