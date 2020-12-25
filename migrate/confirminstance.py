
import os
import sys
from oslo_concurrency import processutils


def replace_n_r(msg):
    return msg.replace('\n', '').replace('\r', '')


############################
PRE_CHECK = "pre_check"
POST_CHECK = "post_check"
QUEUED = "queued"
PRE_BUILT = "pre_built"  # 3001(scp) 3002 (neutron)
POST_BUILT = "post_built"
MIG_START = "mig_start"  # 2004()
MIG_RUNNING = "mig_running"  # 2005 2006 2007 2008
MIG_COMPLETED = "mig_compeleted"
PRE_ROLLBACK = "pre_rollback"
POST_ROLLBACK = "post_rollback"
PRE_CONFIRM = "pre_confirm"
POST_CONFIRM = "post_confirm"
PRE_CLEAN = "pre_clean"
POST_CLEAN = "post_clean"

ABORT_STATUS = [PRE_CHECK, POST_CHECK, PRE_BUILT, POST_BUILT, MIG_START, MIG_RUNNING, MIG_COMPLETED]
ERROR_STATUS = [MIG_START, MIG_RUNNING, MIG_COMPLETED]
#########PRE_BUILT#########
PRE_BUILT_DISK = "pre_built_disk"  # 3003
PRE_BUILT_INJECT = "pre_built_inject"  # 3004
PRE_BUILT_VOLUME = "pre_built_volume"  # 3005(create volume), 3006(connection)
PRE_BUILT_NIC = "pre_built_nic"  # 3007

#########PRE_ROLLBACK#########
PRE_ROLLBACK_VM_CHECK = "pre_rollback_vm_check"
PRE_ROLLBACK_DISK = "pre_rollback_disk"  # 3009
PRE_ROLLBACK_VOLUME = "pre_rollback_volume"  # 3010
PRE_ROLLBACK_NIC = "pre_rollback_nic"  # 3011

#########PRE_CLEAN#########
PRE_CLEAN_VOLUME = "pre_clean_volume"  # 2009
PRE_CLEAN_NIC = "pre_clean_nic"  # 2010
PRE_CLEAN_DISK = "pre_clean_disk"  # 2011
PRE_CLEAN_RESOURCE = "pre_clean_resource"
PRE_CLEAN_VM = "pre_clean_vm"

#########PRE_CONFIRM#########
PRE_CONFIRM_VM = "pre_confirm_vm"  # 3012
PRE_CONFIRM_CONFIG = "pre_confirm_config"  # 3014
PRE_CONFIRM_META = "pre_confirm_meta"
PRE_CONFIRM_NET = "pre_confirm_net"  # 3014
PRE_CONFIRM_NIC = "pre_confirm_nic"  # 3015
PRE_CONFIRM_FLOW = "pre_confirm_flow"  # 3016

#########migration result#########
ABORT = 'abort'
ERROR = 'error'
COMPLETED = 'completed'


def migration_info_recode(context, migration, status, code='ok', skip=True):
    migration_info = MigrationInfo(context=context.elevated())
    migration_info['migration_id'] = migration['id']
    migration_info['status'] = status
    migration_info['error_code'] = code
    migration_info.create()
    if not skip:
        raise Exception("%s error" % status)


def migration_info(status, code="0000", skip=True, vm_error=False):
    def out_wrapper(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            result = None
            wrapped_func = safe_utils.get_wrapped_function(function)
            keyed_args = inspect.getcallargs(wrapped_func, *args, **kwargs)

            if keyed_args.has_key('context') == False:
                context = keyed_args['self'].context
            else:
                context = keyed_args['context']

            if keyed_args.has_key('instance') == False:
                instance = keyed_args['self'].instance
            else:
                instance = keyed_args['instance']

            if keyed_args.has_key('migration') == False:
                migration = keyed_args['self'].migration
            else:
                migration = keyed_args['migration']

            try:
                result = function(*args, **kwargs)
            except Exception as e:
                migration_info = MigrationInfo(context=context.elevated())
                migration_info['migration_id'] = migration['id']
                migration_info['status'] = status
                migration_info['error_code'] = code
                migration_info.create()
                if vm_error and not result:
                    instance.vm_state = vm_states.ERROR
                    instance.save(admin_state_reset=True)
                if not skip:
                    raise Exception("%s error" % status)
            return result

        return wrapper

    return out_wrapper


def pre_confirm_vm(instance_id):
    cmd = "echo `virsh dominfo %s|grep Name|awk -F ':' '{print $2}'`" % instance_id
    out, err = processutils.trycmd(cmd, shell=True)
    if replace_n_r(out).find("no domain with matching name") > -1:
        raise Exception(err)
    cmd = "ps aux|grep %s|grep -v 'grep'|awk -F ' ' '{print $8}'" % replace_n_r(out)
    out, err = processutils.trycmd(cmd, shell=True)
    if replace_n_r(out).find("D") > -1 or replace_n_r(out).find("Z") > -1:
        raise Exception(err)
    return True


def pre_confirm_nic(tap_name, qbr_name, qvb_name, qvo_name):
    nics = (tap_name, qbr_name, qvb_name, qvo_name)
    nic_check_cmd = "ifconfig -a |grep %s"
    for nic in nics:
        cmd = nic_check_cmd % nic
        out, err = processutils.trycmd(cmd, shell=True)
        if replace_n_r(out).find(nic) < 0 or (nic == qvo_name and replace_n_r(
                processutils.trycmd("ovs-ofctl show br-int|grep %s" % nic, shell=True)[0]).find(nic) < 0):
            return False
        raise Exception(err)


def pre_confirm_flow(vlan):
    internal = "ovs-ofctl dump-flows br-int|grep 'dl_vlan=%s'" % vlan
    external = "ovs-ofctl dump-flows br-bond1|grep 'actions=mod_vlan_vid:%s'" % vlan
    if replace_n_r(processutils.trycmd(internal, shell=True)[0]).find("dl_vlan=%s" % vlan) < 0 or replace_n_r(
            processutils.trycmd(external, shell=True)[0]).find("actions=mod_vlan_vid:%s" % vlan) < 0:
        return False
        raise Exception("not found vlan:%s" % vlan)
