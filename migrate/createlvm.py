# coding=utf-8
# /usr/bin/env python

import os
from oslo_concurrency import processutils


def create_volume(volume_id, size_str):
    vg_name = 'vg_os'
    volume_name = 'volume-%s' % volume_id
    cmd = ['lvcreate', '-n', volume_name, vg_name, '-L', size_str]
    try:
        processutils.execute(*cmd, run_as_root=True)
    except Exception as exp:
        print  exp


def initialize_connection(volume_id, auth_user="virtmig", auth_pass="virtmig"):
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


def create_iscsi_target(volume_id, ip, userid="virtmig", password="virtmig", port=3260):
    lv_name = '/dev/vg_os/volume-%s' % volume_id
    # name = os.popen("cat /etc/iscsi/initiatorname.iscsi |awk -F'=' '{print $2}'|awk -F':' '{print $1}'")
    # target_name = name.read()
    # name.close()
    target_name = 'iqn.2010-10.org.openstack' + ":" + 'volume-%s' % volume_id
    try:
        optional_args = []
        optional_args.append('-p%s' % port)
        optional_args.append('-a%s' % ip)
        command_args = ['cinder-rtstool',
                        'create',
                        lv_name,
                        target_name,
                        userid,
                        password, ] + optional_args
        processutils.execute(*command_args, run_as_root=True)
    except Exception as err:
        print err


def do_iscsi_discovery(des_ip, port=3260):
    try:
        # NOTE(griff) We're doing the split straight away which should be
        # safe since using '@' in hostname is considered invalid

        processutils.execute('iscsiadm', '-m', 'discovery',
                                    '--type', 'st', '--portal',
                                    des_ip, ':', port,
                                    run_as_root=True)
    except Exception as ex:
        print ex
def run_iscsi(des_ip, volume_id, userid="virtmig", password="virtmig", port=3260):
    target_iqn = 'iqn.2010-10.org.openstack:'+'volume-%s'%volume_id
    iscsi_command1 = ['-o', 'update', '--name', 'node.session.auth.authmethod', '--value=CHAP']
    iscsi_command2 = ['--op', 'update', '--name', 'node.session.auth.username', '--value=virtmig']
    iscsi_command3 = ['-o', 'update', '--name', 'node.session.auth.password', '--value=virtmig']
    iscsi_command4 = ['-l', '-p', ]
    iscsi_command5 = ['-u', '-p']
    try:
        for commands in iscsi_command1, iscsi_command2, iscsi_command3, iscsi_command4, iscsi_command5:
            processutils.execute(commands, run_as_root=True)
    except Exception as err:
        print err
    pass

