import sys
import subprocess
from winreg import *
import re

class SystemInfo:
    def __init__(self):
        self.required_modules = ["psutil", "platform", "datetime", "tabulate"]

    def install_missing_modules(self):
        missing_modules = []
        for module in self.required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            print("Some required modules are missing. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_modules])
                print("Required modules installed successfully.")
            except subprocess.CalledProcessError:
                print("Failed to install required modules.")
                sys.exit(1)

    def print_section_header(self, section_name):
        print("\n" + "=" * 40, section_name, "=" * 40)

    def print_system_info(self):
        import platform
        uname = platform.uname()
        print(f"System: {uname.system}")
        print(f"Node Name: {uname.node}")
        print(f"Release: {uname.release}")
        print(f"Version: {uname.version}")
        print(f"Machine: {uname.machine}")
        print(f"Processor: {uname.processor}")

############################################################################################################

# Boot Time
    def print_boot_time(self):
        import psutil
        import datetime
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
        print(f"Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}")

############################################################################################################

# CPU Information
    def print_cpu_info(self):
        import psutil
        cpufreq = psutil.cpu_freq()
        print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
        print(f"Min Frequency: {cpufreq.min:.2f}Mhz")
        print(f"Current Frequency: {cpufreq.current:.2f}Mhz")
        print("CPU Usage Per Core:")
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            print(f"Core {i}: {percentage}%")
        print(f"Total CPU Usage: {psutil.cpu_percent()}%")

############################################################################################################

# Memory Information
    def print_memory_info(self):
        import psutil
        svmem = psutil.virtual_memory()
        print(f"Total: {self.get_size(svmem.total)}")
        print(f"Available: {self.get_size(svmem.available)}")
        print(f"Used: {self.get_size(svmem.used)}")
        print(f"Percentage: {svmem.percent}%")
        print("=" * 20, "SWAP", "=" * 20)
        swap = psutil.swap_memory()
        print(f"Total: {self.get_size(swap.total)}")
        print(f"Free: {self.get_size(swap.free)}")
        print(f"Used: {self.get_size(swap.used)}")
        print(f"Percentage: {swap.percent}%")

############################################################################################################

# Disk Information
    def print_disk_info(self):
        import psutil
        partitions = psutil.disk_partitions()
        for partition in partitions:
            print(f"=== Device: {partition.device} ===")
            print(f"  Mountpoint: {partition.mountpoint}")
            print(f"  File system type: {partition.fstype}")

            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue

            print(f"  Total Size: {self.get_size(partition_usage.total)}")
            print(f"  Used: {self.get_size(partition_usage.used)}")
            print(f"  Free: {self.get_size(partition_usage.free)}")
            print(f"  Percentage: {partition_usage.percent}%")

        disk_io = psutil.disk_io_counters()
        print()
        print(f"Total read: {self.get_size(disk_io.read_bytes)}")
        print(f"Total write: {self.get_size(disk_io.write_bytes)}")

############################################################################################################

# Network Information
    def get_network_info_from_ipconfig(self):
        try:
            ipconfig_output = subprocess.check_output("ipconfig /all", shell=True, text=True)
            return ipconfig_output
        except subprocess.CalledProcessError:
            print("Failed to run ipconfig command.")
            return ""

    def parse_ipconfig_output(self, ipconfig_output):
        adapter_sections = re.split(r"\r?\n\r?\n", ipconfig_output)

        for adapter_section in adapter_sections:
            adapter_info = self.extract_adapter_info(adapter_section)
            if adapter_info and self.is_valid_interface(adapter_info):
                self.print_adapter_info(adapter_info)

    def is_valid_interface(self, adapter_info):
        ip_addresses = adapter_info.get("ip_addresses")
        media_state = adapter_info.get("media_state")
        return ip_addresses and any(address != "N/A" for address in ip_addresses) and media_state != "Media disconnected"

    def extract_adapter_info(self, adapter_section):
        adapter_info = {}

        adapter_name_match = re.search(r"Description.*?: (.*?)\r?\n", adapter_section, re.IGNORECASE)
        if adapter_name_match:
            adapter_info["name"] = adapter_name_match.group(1).strip()

        ip_matches = re.findall(r"IPv4 Address.*?:(.*?)\r?\n", adapter_section, re.IGNORECASE)
        adapter_info["ip_addresses"] = [ip.strip() for ip in ip_matches]

        subnet_matches = re.findall(r"Subnet Mask.*?:(.*?)\r?\n", adapter_section, re.IGNORECASE)
        adapter_info["subnet"] = subnet_matches[-1].strip() if subnet_matches else "N/A"

        dns_matches = re.findall(r"DNS Servers.*?:(.*?)\r?\n", adapter_section, re.IGNORECASE)
        adapter_info["dns_servers"] = dns_matches[-1].strip() if dns_matches else "N/A"

        gateway_matches = re.findall(r"Default Gateway.*?:(.*?)\r?\n", adapter_section, re.IGNORECASE)
        adapter_info["gateway"] = gateway_matches[-1].strip() if gateway_matches else "N/A"

        return adapter_info

    def print_adapter_info(self, adapter_info):
        adapter_name = adapter_info.get("name", "Unknown")
        print(f"=== Interface: {adapter_name} ===")
        print(f"  IP Addresses: {', '.join(adapter_info['ip_addresses']) if adapter_info['ip_addresses'] else 'N/A'}")
        print(f"  Subnet: {adapter_info['subnet']}")
        print(f"  DNS Servers: {adapter_info['dns_servers']}")
        print(f"  Default Gateway: {adapter_info['gateway']}")
        print()

    def print_network_info(self):
        import psutil
        ipconfig_output = self.get_network_info_from_ipconfig()
        if ipconfig_output:
            self.parse_ipconfig_output(ipconfig_output)

        net_io = psutil.net_io_counters()
        print(f"Total Bytes Sent: {self.get_size(net_io.bytes_sent)}")
        print(f"Total Bytes Received: {self.get_size(net_io.bytes_recv)}")

############################################################################################################

# GPU Information
    def print_gpu_info(self):
        from tabulate import tabulate

        def get_gpu_details():
            cmd = "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.total,memory.used,memory.free,temperature.gpu --format=csv,noheader"
            try:
                output = subprocess.check_output(cmd, shell=True, encoding="utf-8")
            except subprocess.CalledProcessError:
                return []

            lines = output.strip().split("\n")
            gpu_details = []
            for line in lines:
                values = line.split(",")
                gpu_id = values[0].strip()
                gpu_name = values[1].strip()
                gpu_load = values[2].strip()
                gpu_memory_total = values[3].strip()
                gpu_memory_used = values[4].strip()
                gpu_memory_free = values[5].strip()
                gpu_temperature = values[6].strip()
                gpu_details.append((
                    gpu_id, gpu_name, gpu_load, gpu_memory_total, gpu_memory_used, gpu_memory_free, gpu_temperature
                ))
            return gpu_details

        gpu_details = get_gpu_details()
        if gpu_details:
            headers = ("ID", "Name", "Load", "Total Memory", "Used Memory", "Free Memory", "Temperature")
            print(tabulate(gpu_details, headers=headers))
        else:
            print("No GPUs found or an error occurred while retrieving GPU information.")

    def get_size(self, bytes, suffix="B"):
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    def print_system_details(self):
        self.install_missing_modules()

        self.print_section_header("System Information")
        self.print_system_info()

        self.print_section_header("Boot Time")
        self.print_boot_time()

        self.print_section_header("CPU Info")
        self.print_cpu_info()

        self.print_section_header("GPU Information")
        self.print_gpu_info()

        self.print_section_header("Memory Information")
        self.print_memory_info()

        self.print_section_header("Disk Information")
        self.print_disk_info()

        self.print_section_header("Network Information")
        self.print_network_info()


############################################################################################################

    def print_windows_registry_info(self):
        def get_subkeys(key):
            for i in range(QueryInfoKey(key)[0]):
                name = EnumKey(key, i)
                yield (name, OpenKey(key, name))

        def get_values(key):
            try:
                for i in range(QueryInfoKey(key)[1]):
                    name, value, val_type = EnumValue(key, i)
                    yield (name, value, val_type)
            except OSError:
                for i in range(QueryInfoKey(key)[1]):
                    name, value = EnumValue(key, i)
                    yield (name, value, None)

        self.print_section_header("Windows Registry Information")
        # Retrieve installed programs
        uninstall_loc = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
        with OpenKey(HKEY_LOCAL_MACHINE, uninstall_loc, 0, KEY_READ | KEY_WOW64_64KEY) as uninstall_key:
            print("Installed Programs:")
            print("-------------------")
            for _, subkey in get_subkeys(uninstall_key):
                try:
                    display_name = QueryValueEx(subkey, "DisplayName")[0]
                    publisher = QueryValueEx(subkey, "Publisher")[0]
                    install_location = QueryValueEx(subkey, "InstallLocation")[0]
                    print(f"Name: {display_name}")
                    print(f"Publisher: {publisher}")
                    print(f"Install Location: {install_location}")
                    print("------------------------------------")
                except FileNotFoundError:
                    pass
                finally:
                    subkey.Close()

        # Retrieve CPU information
        cpu_loc = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        with OpenKey(HKEY_LOCAL_MACHINE, cpu_loc, 0, KEY_READ) as cpu_key:
            print()
            print("CPU Information:")
            print("----------------")
            for value_name, value, value_type in get_values(cpu_key):
                if value_type == REG_BINARY:
                    print(f"{value_name}: {value.hex()}")  
                else:
                    print(f"{value_name}: {value}")

        # Retrieve motherboard information
        motherboard_loc = r"HARDWARE\DESCRIPTION\System\BIOS"
        with OpenKey(HKEY_LOCAL_MACHINE, motherboard_loc, 0, KEY_READ) as motherboard_key:
            print("\nMotherboard Information:")
            print("------------------------")
            for value_name, value, value_type in get_values(motherboard_key):
                if value_type == REG_BINARY:
                    print(f"{value_name}: {value.hex()}") 
                else:
                    print(f"{value_name}: {value}")

    def print_system_info_with_registry(self):
        self.print_system_details()
        self.print_windows_registry_info()

############################################################################################################

# Instantiate the SystemInfo class
system_info = SystemInfo()

# Print system details 
system_info.print_system_info_with_registry()
