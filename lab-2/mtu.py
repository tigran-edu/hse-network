import click
import logging
import subprocess
import socket
import platform


class MTU:
    def __init__(self):
        self.min_size = 1
        self.max_size = 1024
        self.system = platform.system().lower()
        self.header_size = 28

    def get_command(self, host, packet_size):
        if self.system == "linux":
            return f"ping {host} -c 1 -M do -s {packet_size}"
        if self.system == "darwin":
            return f"ping {host} -D -s {packet_size} -c 1"
        if self.system == "windows":
            return f"ping {host} -n 1 -M do -s {packet_size}"
        raise Exception(f"Unknow System {self.system}")

    def is_icmp_enabled(self):
        logging.info("Check ICMP")
        if self.system == "Linux":
            try:
                f = open("/proc/sys/net/ipv4/icmp_echo_ignore_all", "r")
                return f.readline()[0] == "0"
            except Exception:
                logging.info("Can't open file with ICMP data")
                return False
        return True

    def is_host_available(self, host):
        logging.info(f"\nPING HOST {host}")
        command = f"ping {host} -c 1"
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
        )
        p.communicate()
        return p.returncode == 0

    def ping(self, host, size):
        logging.info(f"\nPING HOST {host} with packet size {size}")
        command = self.get_command(host, size)
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
        )
        stdout_data = p.communicate()[0].decode("utf-8")
        logging.info(stdout_data + "\n")
        return p.returncode == 0

    def find_max(self, host, min, max):
        while min < max:
            package_size = (min + max + 1) // 2
            if not self.ping(host, package_size):
                max = package_size - 1
            else:
                min = package_size
        return min

    def find_mtu(self, host):
        if not self.is_host_available(host):
            print("\033[91m" + f"Host {host} is unreacheable.")
            exit(1)
        if not self.is_icmp_enabled():
            print("\033[91m" + f"ICMP is not supported.")
            exit(1)

        mtu = self.max_size
        while mtu == self.max_size:
            self.max_size *= 2
            mtu = self.find_max(host, self.min_size, self.max_size)
        mtu += self.header_size
        return mtu


@click.command()
@click.option("--host", required=True, help="Host address.")
def FindMTU(host):
    try:
        socket.gethostbyname(host)
    except:
        print("\033[91m" + f"Invalid host argument {host}")
        exit(1)

    mtu = MTU().find_mtu(host)
    if mtu > 0:
        print("\033[92m" + f"MTU: {mtu} bytes", flush=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    FindMTU()
