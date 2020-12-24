# coding=utf-8
# /usr/bin/env python
import os
import sys
from oslo_concurrency import processutils


# exists devices
def device_exists(device):
    return os.path.exists('/sys/class/net/%s' % device)


# prepare the ovs create command
def create_ovs_vif_cmd(dev, port_id, mac,
                       instance_id, bridge="br-int", interface_type=None):
    cmd = ['--', '--if-exists', 'del-port', dev, 
           '--', 'add-port', bridge, dev, 
           '--', 'set', 'Interface', dev,
           'external-ids:iface-id=%s' % port_id,
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
        try:
            processutils.execute('ip', 'link', 'set', dev, 'mtu',
                                 mtu, run_as_root=True,
                                 check_exit_code=[0, 2, 254])
        except Exception as exp:
            print exp


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
def create_bridge(qbrname, qvb_name, qvo_name):
    mul_snooping = '/sys/class/net/%s/bridge/multicast_snooping' % qbrname
    disable_ipv6 = '/proc/sys/net/ipv6/conf/%s/disable_ipv6' % qbrname
    if not device_exists(qbrname):
        try:
            processutils.execute('brctl', 'addbr', qbrname, run_as_root=True)
        except Exception as exp:
            print "create qbr failed"
        else:
            processutils.execute('brctl', 'setfd', qbrname, str(0), run_as_root=True)
            processutils.execute('brctl', 'stp', qbrname, 'off', run_as_root=True)
            processutils.execute('echo', str(0), '>', mul_snooping, run_as_root=True)
            processutils.execute('echo', str(1), '>', disable_ipv6, run_as_root=True)
            create_veth_pair(qvb_name, qvo_name, mtu=1500)
            processutils.execute('ip', 'link', 'set', qbrname, 'up', run_as_root=True)
            processutils.execute('brctl', 'addif', qbrname, qvb_name,
                                 check_exit_code=False, run_as_root=True)


def ovs_vsctl(args):
    full_args = ['ovs-vsctl'] + args
    try:
        processutils.execute(*full_args, run_as_root=True)
    except Exception as e:
        print e


def create_ovs_vif_port(qbrname, qvb_name, qvo_name, port_id, mac, instance_id,
                        interface_type=None):
    create_bridge(qbrname, qvb_name, qvo_name)
    ovs_vsctl(create_ovs_vif_cmd(qvo_name, port_id,
                                 mac, instance_id, bridge="br-int", 
                                 interface_type=None))


def main(argv):
    create_ovs_vif_port(argv[1], argv[2], argv[3], argv[4], argv[5], argv[6])


if __name__ == '__main__':
    main(sys.argv)
