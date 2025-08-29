import subprocess

def connect_to_vpn(path: str) -> None:
    """Connect to VPN"""
    subprocess.Popen([path, "-f", "NL"])
    return

def disconnect_and_kill_vpn(path: str) -> None:
    """Disconnect and kill VPN process"""
    # subprocess.run([path, "-disconnect"])
    subprocess.run(["taskkill", "/IM", "ProtonVPN.exe", "/F"])
    return

__all__ = ["connect_to_vpn", "disconnect_and_kill_vpn"]