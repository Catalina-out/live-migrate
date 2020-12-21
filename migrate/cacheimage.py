# coding=utf-8
# /usr/bin/env python
import os
import hashlib
from oslo_concurrency import processutils
from oslo_utils import imageutils
# /os_instance/_base directory is existence
path_base = "/os_instance/_base/"


def is_base(path_base):
    re_path = os.path.exists(path_base)
    if re_path is False:
        try:
            os.mkdir(path_base)
        except Exception as exp:
            print("create directory err: %s" % exp)
        else:
            cmd = 'chown nova:nova /os_instance/_base'
            os.system(cmd)


# copy instance disk to destination path
def copy_instance_file(vip, instance_path, dest_path):
    is_base()

    pass


# qemu-img info the image
def qemu_img_info(path, image_id):
    try:
        cmd = ('env', 'LC_ALL=C', 'LANG=C', 'qemu-img', 'info', path, image_id)
        out, err = processutils.execute(cmd)
    except processutils.ProcessExecutionError as exp:
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
    is_base()
    image_path = '/os_gluster_glance/glance/images/'
    cmd = ('sshpass', '-p', 'virtmig', 'scp', 'virtmig@', cluster_vip, image_path, image_id, path_base)
    try:
        os.system(cmd)
    except Exception as exp:
        print("the transfer is failed:%s" % exp)
    # hashlib the qcow2
    base_image_name = hashlib.sha1(image_id.encode('utf-8')).hexdigest()
    os.chdir(path_base)
    os.rename(image_id, base_image_name)
    cmd = ('qemu-img', 'convert', '-f', 'qcow2', '-O', 'raw',  image_id, base_image_name)
    try:
        processutils.execute(cmd)
    except processutils.ProcessExecutionError as exp:
        msg = (("Unable to convert image to %(format)s: %(exp)s") %{'format': image_id, 'exp': exp})
        print(msg)
    data = qemu_img_info(path_base, base_image_name)
    if data.file_format != "raw":
        raise (("Converted to raw, but format is now %s") %data.file_format)