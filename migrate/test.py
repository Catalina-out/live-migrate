# coding=utf-8
# /usr/bin/env python
import hashlib
image_id='3168e8d4-d154-4d34-beca-865c15fadbb9'
base_image_name = hashlib.sha1(image_id.encode('utf-8')).hexdigest()
print base_image_name