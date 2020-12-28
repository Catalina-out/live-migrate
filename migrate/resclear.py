import sys
import shutil
from oslo_concurrency import processutils


# clear the qbr qvb qvo
def clear_ovs(qbr_name, qvb_name, qvo_name):
    out1, err1 = processutils.execute('ovs-vsctl', 'del-port', qvo_name)
    out2, err2 = processutils.execute('ip', 'link', 'del', qvb_name)
    out3, err3 = processutils.execute('ip', 'link', 'set', qbr_name, 'down')
    out4, err4 = processutils.execute('brctl', 'delbr', qbr_name)
    if err1 != '' or err2 != '' or err3 != '' or err4 != '':
        raise Exception(err1, err2, err3, err4)


# clear the volume
def clear_volume(volume_id):
    lvm = 'vg_os/volume-%s' % volume_id
    out, err = processutils.execute('lvremove', lvm)
    raise Exception(out, err)


# clear the instance file
def clear_instance(instance_id):
    cmd = '/os_instance/%s' % instance_id
    try:
        shutil.rmtree(cmd)
    except Exception as exp:
        raise Exception(exp)


def main(argv):
    # clear_ovs(argv[1], argv[2], argv[3])
    # clear_volume(argv[4])
    clear_instance(argv[5])


if __name__ == '__main__':
    main(sys.argv)
