# Hypervisor-Coordinator
This project is essentially a fabric that coordinates the provisioning of compute resources by negotiating with a set of Hypervisors running across physical servers in the datacenter.

A REST API Server is provided which can be consumed by a variety of clients to deal with the virtual infrastructure.

## Setup
```cd ./bin```
```bash install.sh```
Running install.sh will install all the required packages and at the end triggers script.py present in src directory. Scipt.py takes as arguments, 3 files described as follows:

- pm_file : Contains a list of IP addresses separated by newline. These addresses are of the Physical machines to be used for hosting VMs. A unique ID will be assigned to each of these addresses by the code.
- image_file : Contains a list of Images(full path) to be used for spawning VMs. The name of the image will be extracted from the path itself. A unique ID will be assigned to each of these VMs by the code.
- flavor_file : Contains a dictionary of flavors which can be evaluated. For example the dictionary could contain
"types": [{
"cpu": 1,
"ram": 512,
"disk": 1
},
{
"cpu": 2,
"ram": 1024,"disk": 2
},
]

## Features

- Resource Discovery 
  - Resources like total memory, available memory, total cpus, available cpus etc of the target machine have to be found.
  - Commands like "ssh username@machine_ip:port free -m" return total and available memory in megabytes. This command line argument is run via python by using the module "subprocess". 
  - In this way, resources of the target machine are gathered and returned.

- Resource Allocation 
  - The requests are handled in FIFO manner. Before addressing the request, it is first verified. 
  - In case of a create request, we verify if a particulat target machine(physical machine) can satisfy the needs of the virtual machine. The resource discovery helps us in this process. 
  - The algorithm used to decide which resource to allocate is loosely coupled with the implementation.
  - Here, verified request is allocated resource from the last used machine and with least load. A FIFO Queue is used for this purpose.
  
Both the above features can be used by making the following API calls.

## Making API calls

Once the script.py is triggered, the REST server will be up. The following are the list of APIs provided:

### VM APIs:
- VM_Creation:
  - Argument: name, instance_type.
  - Return: vmid(+ if successfully created, 0 if failed)
{
vmid:38201
}
  - URL: http://server/vm/create?name=test_vm&instance_type=type&image_id=id
- VM_Query
  - Argument: vmid
  - Return: instance_type, name, id, pmid (0 if invalid vmid or otherwise)
{
"vmid":38201,
"name":"test_vm",
"instance_type":3,
"pmid": 2
}
  - URL: http://server/vm/query?vmid=vmid
- VM_Destroy
  - Argument: vmid
  - Return: 1 for success and 0 for failure.
{
“status”:1
}
  - URL: http://server/vm/destroy?vmid=vmid
- VM_Type
  - Argument: NA
  - Return: tid, cpu, ram, disk
{
"types": [
{
"tid": 1,
"cpu": 1,
"ram": 512,
"disk": 1
},
{
"tid": 2,
"cpu": 2,
"ram": 1024,
"disk": 2
},
{
"tid": 3,
"cpu": 4,
"ram": 2048,
"disk": 3}
]
}
  - URL: http://server/vm/types
### Resource Service APIs:
- List_PMs
  - Argument: NA
  - Return: pmids
{
“pmids”: [1,2,3]
}
  - URL: http://server/pm/list
- List_VMs
  - Argument: pmid
  - Return: vmids (0 if invalid)
{
“vmids”: [38201, 38203, 38205]
}
  - URL: http://server/pm/listvms?pmid=id
- PM_Query
  - Argument: pmid
  - Return: pmid, capacity, free, no. of VMs running(0 if invalid pmid
or otherwise)
{
“pmid”: 1,
“capacity”:{
“cpu”: 4,
“ram”: 4096,
“disk”: 160
},
“free”:{
“cpu”: 2,
“ram”: 2048,
“disk”: 157
},
“vms”: 1
}
  - URL: http://server/pm/query?pmid=id
### Image Service APIs:
- List_Images
  - Argument: NA
  - Return: id, name
{
“images”:[
{
“id”: 100,
“name”: “Ubuntu­12.04­amd64”
},
{
“id”:101,
“name”: “Fedora­17­x86_64”
}
]
}
URL: http://server/image/list

For all the other Restful calls return 0(that is the call is invalid)

## Implememtation Details

- Flask Restfull server
- Libvirt
  - Libvirt.open(address) API is used to ssh into other machines.
  - The address has to be of the form "qemu+ssh://username@machine_ip:port/system?no_tty=1"
- Openssh-server
- Openssh-client



