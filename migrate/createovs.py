# coding=utf-8
# /usr/bin/env python
import os
from oslo_concurrency import processutils
from oslo_utils import imageutils


# exists devices
def device_exists(device):
    return os.path.exists('/sys/class/net/%s' % device)


# prepare the ovs create command
def create_ovs_vif_cmd(bridge, dev, iface_id, mac,
                       instance_id, interface_type=None):
    cmd = ['--', '--if-exists', 'del-port', dev, '--',
           'add-port', bridge, dev,
           '--', 'set', 'Interface', dev,
           'external-ids:iface-id=%s' % iface_id,
           'external-ids:iface-status=active',
           'external-ids:attached-mac=%s' % mac,
           'external-ids:vm-uuid=%s' % instance_id]
    if interface_type:
        cmd += ['type=%s' % interface_type]
    return cmd


# set the device mtu
def set_device_mtu(dev, mtu=1500):
    """Set the device MTU."""
    if mtu:
        processutils.execute('ip', 'link', 'set', dev, 'mtu',
                             mtu, run_as_root=True,
                             check_exit_code=[0, 2, 254])


# create qbrxxx qvoxxx
def create_veth_pair(dev1_name, dev2_name, mtu=1500):
    if not device_exists(dev1_name) and not device_exists(dev2_name):
        processutils.execute('ip', 'link', 'add', dev1_name, 'type', 'veth', 'peer',
                             'name', dev2_name, run_as_root=True)
        for dev in [dev1_name, dev2_name]:
            processutils.execute('ip', 'link', 'set', dev, 'up', run_as_root=True)
            processutils.execute('ip', 'link', 'set', dev, 'promisc', 'on',
                                 run_as_root=True)
            set_device_mtu(dev, mtu)


# create bridge on ovs
def create_bridge(bridge, qvb_name, qvo_name, mtu=1500):
    mul_snooping = '/sys/class/net/%s/bridge/multicast_snooping' % bridge
    disable_ipv6 = '/proc/sys/net/ipv6/conf/%s/disable_ipv6' % bridge
    if not device_exists(bridge):
        try:
            processutils.execute('brctl', 'addbr', bridge, run_as_root=True)
        except Exception as exp:
            print "create bridge failed"
        else:
            processutils.execute('brctl', 'setfd', bridge, str(0), run_as_root=True)
            processutils.execute('brctl', 'stp', bridge, 'off', run_as_root=True)
            processutils.execute('echo', str(0), '>', mul_snooping, run_as_root=True)
            processutils.execute('echo', str(1), '>', disable_ipv6, run_as_root=True)
            create_veth_pair(qvb_name, qvo_name, mtu=1500)
            processutils.execute('ip', 'link', 'set', bridge, 'up', run_as_root=True)
            processutils.execute('brctl', 'addif', bridge, qvb_name,
                                 check_exit_code=False, run_as_root=True)


def ovs_vsctl(args):
    full_args = ['ovs-vsctl'] + args
    try:
        processutils.execute(*full_args, run_as_root=True)
    except Exception as e:
        print e


def create_ovs_vif_port(bridge, qvb_name, qvo_name, iface_id, mac, instance_id,
                        mtu=1500, interface_type=None):
    create_bridge(bridge, qvb_name, qvo_name, mtu=1500)
    ovs_vsctl(create_ovs_vif_cmd(bridge, qvo_name, iface_id,
                                 mac, instance_id,
                                 interface_type))

