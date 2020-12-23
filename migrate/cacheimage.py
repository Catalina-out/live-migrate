# coding=utf-8
# /usr/bin/env python
import os
import hashlib
import sys
from oslo_concurrency import processutils
from oslo_utils import imageutils

path_base = "/os_instance/_base/"


# /os_instance/_base directory is existence
def is_base(path):
    re_path = os.path.exists(path)
    if re_path is False:
        try:
            os.mkdir(path)
        except Exception as exp:
            print("create directory err: %s" % exp)
        else:
            cmd = ['chown', 'nova:nova', path]
	    processutils.execute(*cmd)


# scp the source instance file to destination compute
def copy_instance_file(source_ip, instance_id ):
    instance_file = ['console.log', 'disk.config', 'disk.info']
    path = '/os_instance/%s/' % instance_id
    path_list = list()
    path_list.append(path)
    uuid = list()
    uuid.append(str(path))
    scp_path='virtmig@%s:%s'%(source_ip,path )
    re_path = os.path.exists(path)
    if re_path is False:
        try:
            os.mkdir(path)
        except Exception as exp:
            print("create directory err: %s" % exp)
        cmd = ['chown', 'nova:nova'] + path_list
        processutils.execute(*cmd)
    for i in instance_file:
        cmd = ['sshpass', '-p', 'virtmig', 'scp', scp_path+i,] + uuid
        try:
            processutils.execute(*cmd)
        except Exception as exp:
            print("scp error %s" % exp)


# copy instance disk to destination path
def create_cow_image(instance_id, image_id, dest_path="/os_instance/_base/", size=None):
    base_image_name = hashlib.sha1(image_id.encode('utf-8')).hexdigest()
    base_cmd = ['qemu-img', 'create', '-f', 'qcow2']
    path = "/os_instance/%s/disk" % instance_id 
    cow_opts = []
    backing_file = dest_path + base_image_name
    cow_opts += ['backing_file=%s' % backing_file]
    base_details = qemu_img_info(dest_path, base_image_name)
    if base_details and base_details.cluster_size is not None:
        cow_opts += ['cluster_size=%s' % base_details.cluster_size]
    if size is not None:
        cow_opts += ['size=%s' % size]
    if cow_opts:
        # Format as a comma separated list
        csv_opts = ",".join(cow_opts)
        cow_opts = ['-o', csv_opts]
    cmd = base_cmd + cow_opts + [path]
    print cmd
    processutils.execute(*cmd)


# qemu-img info the image
def qemu_img_info(path, image_id):
    try:
        cmd = ('env', 'LC_ALL=C', 'LANG=C', 'qemu-img', 'info', path+ image_id)
        out, err = processutils.execute(*cmd)
    except Exception as exp:
        # this means we hit prlimits, make the exception more specific
        if exp.exit_code == -9:
            msg = (("qemu-img aborted by prlimits when inspecting "
                    "%(path)s : %(exp)s") % {'path': path, 'exp': exp})
        else:
            msg = (("qemu-img failed to execute on %(path)s : %(exp)s") %
                   {'path': path, 'exp': exp})
        raise msg

    if not out:
        msg = (("Failed to run qemu-img info on %(path)s : %(error)s") %
               {'path': path, 'error': err})
        raise msg

    return imageutils.QemuImgInfo(out)


# convert qcow2 to raw
def fetch_to_raw(cluster_vip, image_id):
    global path_base
    is_base(path_base)
    image_tmp = '/os_gluster_glance/glance/images/%s'%image_id
    scp_path='virtmig@%s:%s'%(cluster_vip,image_tmp)
    cmd = ['sshpass', '-p', 'virtmig', 'scp', scp_path, path_base] 
    try:
	processutils.execute(*cmd)
    except Exception as exp:
        print("the transfer is failed:%s" % exp)
    # hashlib the qcow2
    base_image_name = hashlib.sha1(image_id.encode('utf-8')).hexdigest()
    #os.rename(path_base+image_id, path_base+image_name)
    cmd = ('qemu-img', 'convert', '-f', 'qcow2', '-O', 'raw', path_base+image_id, path_base+base_image_name)
    try:
        processutils.execute(*cmd)
    except processutils.ProcessExecutionError as exp:
        msg = (("Unable to convert image to %(format)s: %(exp)s") % {'format': image_id, 'exp': exp})
        print(msg)
    data = qemu_img_info(path_base, base_image_name)
    if data.file_format != "raw":
        raise (("Converted to raw, but format is now %s") % data.file_format)


def main(argv):
    #copy_instance_file(argv[1],argv[2])
    #fetch_to_raw(argv[3], argv[4])
    create_cow_image(argv[2], argv[4])



if __name__ == '__main__':
    main(sys.argv)
