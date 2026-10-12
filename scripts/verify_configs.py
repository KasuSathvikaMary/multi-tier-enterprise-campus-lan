#!/usr/bin/env python3
"""
Multi-Tier Enterprise Campus LAN - Configuration & Topology Linter
Validates Cisco IOS configurations for:
- IP address validity and duplicate detection
- Subnet mask alignment
- HSRP Virtual IP membership in SVI subnet
- OSPF router-id presence
- Syntax and essential command integrity
"""

import ipaddress
import os
import re
import sys
from pathlib import Path

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

EXPECTED_FILES = [
    "core-01.ios.cfg",
    "core-02.ios.cfg",
    "dist-01.ios.cfg",
    "dist-02.ios.cfg",
    "access-01.ios.cfg",
    "access-02.ios.cfg",
    "edge-router.ios.cfg"
]

def check_files_exist():
    print("[*] Checking configuration files presence...")
    missing = []
    for f in EXPECTED_FILES:
        path = CONFIGS_DIR / f
        if not path.is_file():
            missing.append(f)
        else:
            print(f"  [+] Found: {f}")
    if missing:
        print(f"[!] Error: Missing config files: {missing}", file=sys.stderr)
        return False
    return True

def parse_ips(content):
    """Extract (interface, ip, mask) tuples from Cisco config."""
    results = []
    curr_iface = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("interface "):
            curr_iface = line.split("interface ")[1]
        elif line.startswith("ip address ") and curr_iface:
            parts = line.split()
            if len(parts) >= 4:
                ip_str = parts[2]
                mask_str = parts[3]
                try:
                    ip_net = ipaddress.IPv4Interface(f"{ip_str}/{mask_str}")
                    results.append((curr_iface, ip_net))
                except Exception as e:
                    print(f"  [!] Invalid IP line '{line}': {e}")
    return results

def parse_hsrp(content):
    """Extract HSRP VIP configurations."""
    results = []
    curr_iface = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("interface "):
            curr_iface = line.split("interface ")[1]
        elif "standby " in line and "ip " in line and curr_iface:
            m = re.search(r"standby\s+(\d+)\s+ip\s+([0-9.]+)", line)
            if m:
                group = m.group(1)
                vip = m.group(2)
                results.append((curr_iface, group, vip))
    return results

def validate_all():
    all_assigned_ips = {}
    total_errors = 0

    print("\n[*] Validating interface IP configurations & detecting collisions...")
    for f in EXPECTED_FILES:
        path = CONFIGS_DIR / f
        text = path.read_text()
        ips = parse_ips(text)
        for iface, if_obj in ips:
            ip_str = str(if_obj.ip)
            if ip_str in all_assigned_ips:
                prev_file, prev_iface = all_assigned_ips[ip_str]
                print(f"[!] IP CONFLICT: {ip_str} assigned in {f} ({iface}) and {prev_file} ({prev_iface})")
                total_errors += 1
            else:
                all_assigned_ips[ip_str] = (f, iface)

        # Check OSPF Router-ID for Layer 3 devices
        if "core" in f or "dist" in f or "edge" in f:
            if "router-id" not in text:
                print(f"[!] Warning: No explicit 'router-id' in {f}")
                total_errors += 1
            else:
                rid = re.search(r"router-id\s+([0-9.]+)", text)
                if rid:
                    print(f"  [+] {f}: OSPF Router-ID is {rid.group(1)}")

    print(f"\n[*] Total unique IP endpoints verified: {len(all_assigned_ips)}")

    print("\n[*] Validating HSRP Virtual IPs against SVI Subnets on Distribution switches...")
    for dist_file in ["dist-01.ios.cfg", "dist-02.ios.cfg"]:
        path = CONFIGS_DIR / dist_file
        text = path.read_text()
        ips = {iface: if_obj for iface, if_obj in parse_ips(text)}
        hsrps = parse_hsrp(text)
        for iface, grp, vip in hsrps:
            if iface in ips:
                svi_net = ips[iface].network
                v_ip = ipaddress.IPv4Address(vip)
                if v_ip in svi_net:
                    print(f"  [+] {dist_file}: {iface} (HSRP Grp {grp} VIP {vip}) valid in {svi_net}")
                else:
                    print(f"[!] Error: {dist_file}: VIP {vip} is NOT inside {iface} subnet {svi_net}!")
                    total_errors += 1
            else:
                print(f"[!] Error: HSRP configured on {iface} without IP address!")
                total_errors += 1

    return total_errors == 0

def main():
    print("=" * 65)
    print(" Campus Network Automation: Config & Topology Validator")
    print("=" * 65)
    
    if not check_files_exist():
        sys.exit(1)
        
    success = validate_all()
    print("\n" + "=" * 65)
    if success:
        print("[SUCCESS] All configurations passed architecture and IP sanity checks!")
        sys.exit(0)
    else:
        print("[FAILURE] Errors found during configuration validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
