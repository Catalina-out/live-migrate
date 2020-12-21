# coding=utf-8
# /usr/bin/env python
import os
import hashlib

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
    cmd = ('env', 'LC_ALL=C', 'LANG=C', 'qemu-img', 'info', path, image_id)
    os.system(cmd)


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
        os.system(cmd)
    except Exception as exp:
        print("convert image is failed:%s"%exp)
    qemu_img_info(path_base, base_image_name)