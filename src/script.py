from flask import Flask
from flask import request
from flask.ext import restful
from lxml import etree
import libvirt
from libvirt import libvirtError
import uuid
import subprocess
import Queue
import sys

#SSH verify

app = Flask(__name__)
api = restful.Api(app)

f = open(sys.argv[3], 'r')	#flavor_file
content = f.read()
new = '{' + content + '}'
some = eval(new)
types = some['types']
#Assuming Ip in types array will be of the form username@ipaddress:portno

f = open(sys.argv[1], 'r')	#pms_file
content = f.read()
new = '{' + content + '}'
some = eval(new)
pms = some['pms']

f = open(sys.argv[2], 'r')   #image_file
content = f.read()
content = '{' + content + '}'
c = eval(content)
imgs = c['images']

q = Queue.Queue()
for ip in pms:
	q.put(ip)

dic = dict()
count = 0
maping = dict()			#vmid map to pmid

@app.route('/')
def hello_world():
    return 'Hello World!'

class create(restful.Resource):
	def get(self):		#Disk and image id not yet implemented
		name = request.args["name"]
		instance_type = request.args["instance_type"]
		instance_type = int(instance_type)
		image_id = request.args["image_id"]	

		flag = 0
		turn = 0

		while turn<len(pms) :	#disk not taken care
			ip = q.get() 
			
			Command = "free -m | grep Mem: | awk '{print $4}'"
			ssh = subprocess.Popen(["ssh", "%s" % ip, Command],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
			free_mem = ssh.stdout.readlines()
			
			proc = subprocess.Popen(['nproc'], stdout= subprocess.PIPE, shell = True)
			(free_cpu, err) = proc.communicate()

			p1 = subprocess.Popen(['df', '-h', '--total'], stdout = subprocess.PIPE)
			p2 = subprocess.Popen(['grep', 'total'], stdin = p1.stdout, stdout = subprocess.PIPE)
			p1.stdout.close()
			output, err = p2.communicate()
			free_disk = output.split(' ')[29]

			turn += 1
			q.put(ip)
			if free_disk[-1:] == 'T':
				ant = free_disk[0: -1]
				disk_int = float(ant)
				disk_int = disk_int*1024
			elif free_disk[-1:] == 'M':
				ant = free_disk[0: -1]
				disk_int = float(ant)
			elif free_disk[-1:] == 'K':
				ant = free_disk[0: -1]
				disk_int = float(ant)
				disk_int = disk_int/1024

			if types[instance_type].get('ram') < (int(free_mem[0]) * 1024) and types[instance_type].get('cpu') <= int(free_cpu) and types[instance_type].get('disk') <= disk_int: 
				flag = 1
				global maping
				global count
				index = 0
				for value in pms:
					if value != ip:
						index += 1
					else:
						maping[count] = index
						break

		if flag == 1 : 
			uid = str(uuid.uuid1())
			xmlstr = """<domain type='qemu'><name>%s</name><memory>%s</memory> <currentMemory>%s</currentMemory> <vcpu>%s</vcpu> <os> <type arch='i686' machine='pc-1.0'>hvm</type> <boot dev='hd'/> </os> <features> <acpi/> <apic/> <pae/> </features> <clock offset='utc'/> <on_poweroff>destroy</on_poweroff> <on_reboot>restart</on_reboot> <on_crash>restart</on_crash> <devices> <emulator>/usr/bin/qemu-system-i386</emulator> <disk type='file' device='disk'> <driver name='qemu' type='qcow2'/> <source file='%s' /> <target dev='hda' bus='ide'/> <alias name='ide0-0-0'/> <address type='drive' controller='0' bus='0' unit='0'/> </disk> <controller type='ide' index='0'> <alias name='ide0'/> <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/> </controller> <interface type='network'> <mac address='52:54:00:82:f7:43'/> <source network='default'/> <target dev='vnet0'/> <alias name='net0'/> <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/> </interface> <serial type='pty'> <source path='/dev/pts/2'/> <target port='0'/> <alias name='serial0'/> </serial> <console type='pty' tty='/dev/pts/2'> <source path='/dev/pts/2'/> <target type='serial' port='0'/> <alias name='serial0'/> </console> <input type='mouse' bus='ps2'/> <graphics type='vnc' port='5900' autoport='yes'/> <sound model='ich6'> <alias name='sound0'/> <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/> </sound> <video> <model type='cirrus' vram='9216' heads='1'/> <alias name='video0'/> <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/> </video> <memballoon model='virtio'> <alias name='balloon0'/> <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/> </memballoon> </devices> <seclabel type='dynamic' model='apparmor' relabel='yes'> <label>libvirt-10a963ef-9458-c30d-eca3-891efd2d5817</label> <imagelabel>libvirt-10a963ef-9458-c30d-eca3-891efd2d5817</imagelabel> </seclabel></domain>""" % (name, str(types[instance_type].get('ram')), str(types[instance_type].get('ram')), str(types[instance_type].get('cpu')), imgs[int(image_id)])
			if ip == 'localhost':
				conn = libvirt.open('qemu:///system')
			else:
				conn = libvirt.open('qemu+ssh://' + ip + '/system?no_tty=1')
			try:
				global dic
				dic[count] = [name, instance_type, uid]
				count += 1
				domain = conn.createXML(xmlstr )
			except libvirtError, e:
				print e.message 
			return count
		else:
			return 0

class vm_query(restful.Resource):
	def get(self):
		vmid = int(request.args["vmid"])
		result = {}
		result["vmid"] = vmid
		result["name"] = dic[vmid][0]
		result["instance_type"] = dic[vmid][1]
		result["pmid"] = maping[vmid]
		return result

class vm_type(restful.Resource):
	def get(self):
		return types

class destroy(restful.Resource):
	def get(self):
		print dic
		vmid = int(request.args["vmid"])
		try:
			pmid = maping[vmid]
			ip = pms[pmid]
			if ip == 'localhost':
				conn = libvirt.open('qemu:///system')
			else:
				conn = libvirt.open('qemu+ssh://' + ip + '/system?no_tty=1')
			try:
				domain  = conn.lookupByName(str(dic[vmid][0]))
				domain.destroy()
				return 1
			except libvirtError:
				return "Domain Not Found"
		except KeyError:
			return 0

class list_pms(restful.Resource):
	def get(self):
		return pms

class list_vms(restful.Resource):
	def get(self):
		pmid = int(request.args["pmid"])
		result = []
		for key in maping :
			if maping[key] == pmid: 
				result.append(key)
		return result

class pm_query(restful.Resource):
	def get(self):
		pmid = int(request.args["pmid"])
		ip = pms[pmid]
		result = {}
		result["pmid"] = pmid

		Command = "free -m | grep Mem: | awk '{print $2}'"
		ssh = subprocess.Popen(["ssh", "%s" % ip, Command],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
		total_mem = ssh.stdout.readlines()

		Command = "free -m | grep Mem: | awk '{print $4}'"
		ssh = subprocess.Popen(["ssh", "%s" % ip, Command],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
		free_mem = ssh.stdout.readlines()

		proc1 = subprocess.Popen(['lscpu'], stdout= subprocess.PIPE)
		proc2 = subprocess.Popen(['grep', 'CPU(s):'], stdin = proc1.stdout, stdout = subprocess.PIPE)
		proc1.stdout.close()
		output, err = proc2.communicate()
		total_cpu = output[23]

		proc = subprocess.Popen(['nproc'], stdout= subprocess.PIPE, shell = True)
		(free_cpu, err) = proc.communicate()

		p1 = subprocess.Popen(['df', '-h', '--total'], stdout = subprocess.PIPE)
		p2 = subprocess.Popen(['grep', 'total'], stdin = p1.stdout, stdout = subprocess.PIPE)
		p1.stdout.close()
		output, err = p2.communicate()
		total_disk = output.split(' ')[24]
		free_disk = output.split(' ')[29]

		result["capacity"] = {}
		result["capacity"]["cpu"] = int(total_cpu)
		result["capacity"]["ram"] = int(total_mem[0])
		result["capacity"]["disk"] =  total_disk

		result["free"] = {}
		result["free"]["cpu"] = int(free_cpu)
		result["free"]["ram"] = int(free_mem[0])
		result["free"]["disk"] =  free_disk

		if ip=='localhost':
			conn = libvirt.open('qemu:///system')
		else:
			conn = libvirt.open('qemu+ssh://' + ip + '/system?no_tty=1')
		names = conn.listDefinedDomains()
		result["vms"] = len(names)

		return result

class list_images(restful.Resource):
	def get(self):
		result = {}
		result["images"] = []
		for index, image in enumerate(imgs):
			temp = {}
			l = image.split('/')
			length = len(l)
			temp["name"] = l[length - 1][0:-4]
			temp["id"] = index
			result["images"].append(temp)
		return result

api.add_resource(create, '/vm/create')
api.add_resource(vm_query,'/vm/query')
api.add_resource(vm_type, '/vm/types')
api.add_resource(destroy, '/vm/destroy')
api.add_resource(list_pms, '/pm/list')
api.add_resource(list_vms, '/pm/listvms')
api.add_resource(pm_query, '/pm/query')
api.add_resource(list_images, '/image/list')

if __name__ == '__main__':
        app.run(host='0.0.0.0', debug=True, threaded = True)


