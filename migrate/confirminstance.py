import sys
from oslo_concurrency import processutils


def replace_n_r(msg):
    return msg.replace('\n', '').replace('\r', '')


def pre_confirm_vm(instance_id):
    cmd = "echo `virsh dominfo %s|grep Name|awk -F ':' '{print $2}'`" % instance_id
    out, err = processutils.trycmd(cmd, shell=True)
    if replace_n_r(out).find("no domain with matching name") > -1:
        raise Exception(err)
    cmd = "ps aux|grep %s|grep -v 'grep'|awk -F ' ' '{print $8}'" % replace_n_r(out)
    out, err = processutils.trycmd(cmd, shell=True)
    if replace_n_r(out).find("D") > -1 or replace_n_r(out).find("Z") > -1:
        raise Exception(err)


def pre_confirm_nic(tap_name, qbr_name, qvb_name, qvo_name):
    nics = (tap_name, qbr_name, qvb_name, qvo_name)
    nic_check_cmd = "ifconfig -a |grep %s"
    for nic in nics:
        cmd = nic_check_cmd % nic
        out, err = processutils.trycmd(cmd, shell=True)
        if replace_n_r(out).find(nic) < 0 or (nic == qvo_name and replace_n_r(
                processutils.trycmd("ovs-ofctl show br-int|grep %s" % nic, shell=True)[0]).find(nic) < 0):
            raise Exception(err)


def pre_confirm_flow(vlan):
    internal = "ovs-ofctl dump-flows br-int|grep 'dl_vlan=%s'" % vlan
    external = "ovs-ofctl dump-flows br-bond1|grep 'actions=mod_vlan_vid:%s'" % vlan
    if replace_n_r(processutils.trycmd(internal, shell=True)[0]).find("dl_vlan=%s" % vlan) < 0 or replace_n_r(
            processutils.trycmd(external, shell=True)[0]).find("actions=mod_vlan_vid:%s" % vlan) < 0:
        raise Exception("not found vlan:%s" % vlan)


def main(argv):
    pre_confirm_vm(argv[1])
    pre_confirm_nic(argv[2], argv[3], argv[4], argv[5])
    pre_confirm_flow(argv[6])


if __name__ == '__main__':
    main(sys.argv)
