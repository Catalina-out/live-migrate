# coding=utf-8
# /usr/bin/env python

import os
import sys
from oslo_concurrency import processutils

def create_volume(volume_id, size_str):
    vg_name = 'vg_os'
    volume_name = 'volume-%s' % volume_id
    cmd = ['lvcreate', '-n', volume_name, vg_name, '-L', size_str]
    try:
        processutils.execute(*cmd, run_as_root=True)
    except Exception as exp:
        print  exp


def initialize_connection(volume_id, auth_user, auth_pass):
    volume_iqn = 'iqn.2010-10.org.openstack'
    volume_iqn = volume_iqn + ":" + 'volume-%s' % volume_id
    name = os.popen("cat /etc/iscsi/initiatorname.iscsi |awk -F'=' '{print $2}'")
    target_name = name.read()
    name.close()
    try:
        processutils.execute('cinder-rtstool', 'add-initiator',
                             volume_iqn,
                             auth_user,
                             auth_pass,
                             target_name,
                             run_as_root=True)
    except Exception as exp:
        print exp

def main(argv):
    lis = list()
    lis.append(argv[1])
    pass

if __name__ == '__main__':
    main(sys.argv)

