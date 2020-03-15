#!/usr/bin/env python

import math
import os
import re
import subprocess
import sys
#import urllib2
import urllib.request as urllib2

def generate_ovpn():
    results = fetch_ip_data()

    upscript_header = """\
#!/bin/sh
"""
    downscript_header = """\
#!/bin/sh
"""

    upfile = open('/etc/luci-uploads/vpn-up.sh', 'w')
    downfile = open('/etc/luci-uploads/vpn-down.sh', 'w')

    upfile.write(upscript_header)
    downfile.write(downscript_header)
    
    route_counts = 0
    for ip, _, mask in results:
        upfile.write('route add -net %s/%s dev pppoe-wan metric 10\n' % (ip, mask))
#        upfile.write('route add -net %s/%s gateway ${OLDGW} metric 10\n' % (ip, mask))
        downfile.write('route del -net %s/%s\n' % (ip, mask))
        route_counts +=1

    print("Total CN Route Counts = ", route_counts )
    upfile.write("echo add %s routes done.\n" % route_counts)
    downfile.write("echo del %s routes done.\n" % route_counts)

    upfile.close()
    downfile.close()

    os.chmod('/etc/config/vpn-up.sh', 0o0755)
    os.chmod('/etc/config/vpn-down.sh', 0o0755)

def fetch_ip_data():
    url = 'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest'
    try:
        data = subprocess.check_output(['wget', url, '-O-'])
    except (OSError, AttributeError):
        print >> sys.stderr, "Fetching data from apnic.net, "\
                             "it might take a few minutes, please wait..."
        data = urllib2.urlopen(url).read()

    cnregex = re.compile(r'^apnic\|cn\|ipv4\|[\d\.]+\|\d+\|\d+\|a\w*$',
                         re.I | re.M)
    cndata = cnregex.findall(data.decode('utf-8'))

    results = []

    for item in cndata:
        unit_items = item.split('|')
        starting_ip = unit_items[3]
        num_ip = int(unit_items[4])

        imask = 0xffffffff ^ (num_ip - 1)
        imask = hex(imask)[2:]

        mask = [imask[i:i + 2] for i in range(0, 8, 2)]
        mask = '.'.join([str(int(i, 16)) for i in mask])

        cidr = 32 - int(math.log(num_ip, 2))

        results.append((starting_ip, mask, cidr))
#        print "%s/%s(%s)-%s"%(starting_ip,cidr,mask,unit_items[1])

    return results

def main():
    generate_ovpn()

if __name__ == '__main__':
    main()
