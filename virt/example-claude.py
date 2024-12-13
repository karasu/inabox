#!/usr/bin/env python3

import libvirt
import sys
import os

from xml.etree import ElementTree as ET

def create_and_run_vm(name, memory_mb, vcpus, disk_path, iso_path):
    """
    Create and start a new VM using libvirt
    
    Args:
        name (str): Name of the VM
        memory_mb (int): Memory in MB
        vcpus (int): Number of virtual CPUs
        disk_path (str): Path to disk image
        iso_path (str): Path to installation ISO
    """
    try:
        # Connect to local QEMU hypervisor
        conn = libvirt.open('qemu:///system')
        if conn == None:
            raise Exception('Failed to connect to QEMU/KVM')

        # Create domain XML
        domain_xml = f"""
        <domain type='kvm'>
            <name>{name}</name>
            <memory unit='MiB'>{memory_mb}</memory>
            <vcpu>{vcpus}</vcpu>
            <os>
                <type arch='x86_64' machine='pc-q35-6.2'>hvm</type>
                <boot dev='cdrom'/>
                <boot dev='hd'/>
            </os>
            <features>
                <acpi/>
                <apic/>
            </features>
            <devices>
                <disk type='file' device='disk'>
                    <driver name='qemu' type='qcow2'/>
                    <source file='{disk_path}'/>
                    <target dev='vda' bus='virtio'/>
                </disk>
                <disk type='file' device='cdrom'>
                    <driver name='qemu' type='raw'/>
                    <source file='{iso_path}'/>
                    <target dev='sda' bus='sata'/>
                    <readonly/>
                </disk>
                <interface type='network'>
                    <source network='default'/>
                    <model type='virtio'/>
                </interface>
                <console type='pty'/>
                <graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'>
                    <listen type='address' address='127.0.0.1'/>
                </graphics>
            </devices>
        </domain>
        """

        # Create the domain
        dom = conn.defineXMLFlags(domain_xml, 0)
        if dom == None:
            raise Exception(f'Failed to define domain {name} from XML')
        
        print(f'Domain {name} defined successfully')

        # Start the domain
        if dom.create() < 0:
            raise Exception(f'Failed to start domain {name}')
        
        print(f'Domain {name} started successfully')

        # Get domain info
        state, maxmem, mem, vcpus_num, cputime = dom.info()
        print(f'Domain state: {state}')
        print(f'Max memory: {maxmem}')
        print(f'Memory: {mem}')
        print(f'Number of vCPUs: {vcpus_num}')
        print(f'CPU time: {cputime}')

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        if 'conn' in locals():
            conn.close()
        sys.exit(1)

    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    # Example usage
    VM_NAME = 'test-vm'
    MEMORY_MB = 2048  # 2GB RAM
    VCPUS = 2
    DISK_PATH = '/var/lib/libvirt/images/test-vm.qcow2'
    ISO_PATH = '/path/to/your/install.iso'

    # Make sure the disk image exists (you need to create it beforehand)
    # You can create it using: 
    # qemu-img create -f qcow2 /var/lib/libvirt/images/test-vm.qcow2 20G

    create_and_run_vm(VM_NAME, MEMORY_MB, VCPUS, DISK_PATH, ISO_PATH)

