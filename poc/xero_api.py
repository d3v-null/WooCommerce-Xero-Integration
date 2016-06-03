import os
import sys
import yaml
from xero import Xero
from xero.auth import PrivateCredentials
from pprint import pprint

dir_parent = os.path.dirname(os.path.dirname(sys.argv[0]))
if dir_parent:
    os.chdir(dir_parent)
dir_conf = 'conf'
path_conf_xero = os.path.join(dir_conf, 'xero_api.yaml')
with open(path_conf_xero) as file_conf_xero:
    conf_xero = yaml.load(file_conf_xero)
    for key in ['consumer_key', 'consumer_secret', 'key_file']:
        assert key in conf_xero, key

with open(conf_xero.get('key_file')) as file_key:
    rsa_key = file_key.read()

credentials = PrivateCredentials(conf_xero.get('consumer_key'), rsa_key)
xero_obj = Xero(credentials)

print (xero_obj.items.all())

# aprons = xero_obj.items.filter(Name='Apron - Cotton Chinese Peony')
# if aprons:
#     apron = aprons[0]
#     pprint(apron)
#     pprint(xero_obj.items.get_attachments(apron['ItemID']))
