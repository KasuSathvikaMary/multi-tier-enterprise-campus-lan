# Multi-Tier Enterprise Campus LAN with SVI Routing

[![Network Architecture](https://img.shields.io/badge/Architecture-3--Tier%20Hierarchical-blue.svg)](#)
[![Protocols](https://img.shields.io/badge/Protocols-OSPF%20%7C%20HSRPv2%20%7C%20LACP%20%7C%20802.1Q-green.svg)](#)
[![Simulation](https://img.shields.io/badge/Simulators-Cisco%20Packet%20Tracer%20%7C%20GNS3%20%7C%20EVE--NG-orange.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An enterprise-grade, high-availability corporate campus local area network (LAN) architecture simulated in **Cisco Packet Tracer** and **GNS3 / EVE-NG**. 

The design implements a structured **Core-Distribution-Access** 3-tier hierarchy, hardware-accelerated **Switch Virtual Interface (SVI)** inter-VLAN routing, **HSRPv2** first-hop redundancy with active/standby load balancing, **LACP (802.3ad)** link aggregation, and **OSPFv2 Area 0** dynamic routing.

---

## 🏛️ Architecture Overview

```
                      +-----------------------------+
                      |      Edge / WAN Router      |
                      +-----------------------------+
                                     | (10.255.255.0/30)
                    ===================================
                    |       CORE LAYER (Layer 3)      |
                    ===================================
                         +---------+       +---------+
                         | CORE-01 |=======| CORE-02 |
                         +---------+  Po1  +---------+
                              \   \         /   /
                               \   \_______/   /
                                \   _______   /
                                 \ /       \ /
                    ===================================
                    |    DISTRIBUTION LAYER (L2/L3)   |
                    ===================================
                         +---------+  Po2  +---------+
                         | DIST-01 |=======| DIST-02 |
                         +---------+       +---------+
                        (HSRP Act:          (HSRP Act:
                         VLAN 10,20,30)      VLAN 40,50,60)
                             ||   \\       //   ||
                             ||    \\_____//    ||
                             ||     _______     ||
                             ||    /       \    ||
                    ===================================
                    |       ACCESS LAYER (Layer 2)    |
                    ===================================
                         +---------+       +---------+
                         | ACC-01  |       | ACC-02  |
                         +---------+       +---------+
                         /    |    \       /    |    \
                        /     |     \     /     |     \
                     [HR]   [IT]   [FIN] [EXEC] [GUEST] [MGMT]
```

### Key Design Pillars

| Layer | Primary Role | Technologies & Protocols |
| :--- | :--- | :--- |
| **Core Layer** | Ultra-high-speed packet switching backbone, zero ACL packet filtering, routed links. | Routed Interfaces, OSPFv2 (Area 0), LACP Port-Channels, BFD |
| **Distribution Layer** | Inter-VLAN routing boundary, policy enforcement, First Hop Redundancy, QoS. | Switch Virtual Interfaces (SVIs), HSRPv2 with Preemption & Tracking, OSPFv2 Area 0, Rapid PVST+ Root |
| **Access Layer** | Secure endpoint attachment, traffic classification, Layer 2 loop avoidance. | 802.1Q Trunks, EtherChannel (LACP), PortFast, BPDU Guard, DHCP Snooping, Dynamic ARP Inspection (DAI) |

---

## 🏷️ VLAN & IP Subnet Plan (IPAM)

The campus utilizes the RFC 1918 private address block `10.10.0.0/16` for endpoint access subnets and `10.255.0.0/24` for routed transit interconnects.

### Endpoint VLANs (SVI Gateways)

| VLAN ID | Name | Subnet | Gateway (HSRP VIP) | DIST-01 (IP / Priority) | DIST-02 (IP / Priority) | Primary Root |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **10** | `MGMT` | `10.10.10.0/24` | `10.10.10.1` | `10.10.10.2` (P: 110) | `10.10.10.3` (P: 100) | DIST-01 |
| **20** | `HR` | `10.10.20.0/24` | `10.10.20.1` | `10.10.20.2` (P: 110) | `10.10.20.3` (P: 100) | DIST-01 |
| **30** | `IT_ENG` | `10.10.30.0/24` | `10.10.30.1` | `10.10.30.2` (P: 110) | `10.10.30.3` (P: 100) | DIST-01 |
| **40** | `FINANCE` | `10.10.40.0/24` | `10.10.40.1` | `10.10.40.2` (P: 100) | `10.10.40.3` (P: 110) | DIST-02 |
| **50** | `EXECUTIVES` | `10.10.50.0/24` | `10.10.50.1` | `10.10.50.2` (P: 100) | `10.10.50.3` (P: 110) | DIST-02 |
| **60** | `GUEST` | `172.16.60.0/24` | `172.16.60.1` | `172.16.60.2` (P: 100) | `172.16.60.3` (P: 110) | DIST-02 |
| **99** | `NATIVE_PARK` | N/A (Unused) | N/A | Trunk Native Only | Trunk Native Only | N/A |

### Point-to-Point Routed Transit Links (Core <-> Distribution)

| Link | Subnet | Subnet Mask | Interface Endpoint 1 | Interface Endpoint 2 |
| :--- | :--- | :--- | :--- | :--- |
| **CORE-01 <-> CORE-02** | `10.255.0.0/30` | `255.255.255.252` | CORE-01 (Po1 - 10.255.0.1) | CORE-02 (Po1 - 10.255.0.2) |
| **DIST-01 <-> CORE-01** | `10.255.0.4/30` | `255.255.255.252` | DIST-01 (Gi1/0/1 - 10.255.0.6) | CORE-01 (Gi1/0/1 - 10.255.0.5) |
| **DIST-01 <-> CORE-02** | `10.255.0.8/30` | `255.255.255.252` | DIST-01 (Gi1/0/2 - 10.255.0.10) | CORE-02 (Gi1/0/1 - 10.255.0.9) |
| **DIST-02 <-> CORE-01** | `10.255.0.12/30`| `255.255.255.252` | DIST-02 (Gi1/0/1 - 10.255.0.14) | CORE-01 (Gi1/0/2 - 10.255.0.13) |
| **DIST-02 <-> CORE-02** | `10.255.0.16/30`| `255.255.255.252` | DIST-02 (Gi1/0/2 - 10.255.0.18) | CORE-02 (Gi1/0/2 - 10.255.0.17) |
| **CORE-01 <-> WAN_EDGE** | `10.255.255.0/30`| `255.255.255.252` | CORE-01 (Gi1/0/24 - 10.255.255.2)| EDGE-ROUTER (Gi0/0 - 10.255.255.1) |

---

## ⚡ High-Availability & Redundancy Mechanics

### 1. Active-Active HSRPv2 Gateway Load Sharing
- **Odd/Even VLAN Distribution:** 
  - `DIST-01` is Primary Active Gateway (Priority 110) for VLANs 10, 20, 30.
  - `DIST-02` is Primary Active Gateway (Priority 110) for VLANs 40, 50, 60.
- **Preemption & Delay:** Configured with `standby <vlan> preempt delay minimum 30` to avoid gateway flapping during switch boot-up.
- **Uplink Tracking:** Object tracking monitors core-facing interfaces. If uplinks to Core fail, priority drops by 20, safely triggering failover to the standby peer.

### 2. Spanning Tree Alignment (Rapid PVST+)
- To eliminate suboptimal Layer 2 traffic paths and STP blocked uplink bottlenecks:
  - `DIST-01` is configured as `spanning-tree vlan 10,20,30 priority 4096` (Root) and `vlan 40,50,60 priority 8192` (Secondary).
  - `DIST-02` is configured as `spanning-tree vlan 40,50,60 priority 4096` (Root) and `vlan 10,20,30 priority 8192` (Secondary).
- HSRP active forwarder matches the STP Root bridge for every VLAN, preventing unnecessary inter-switch trunk traversals.

### 3. Dynamic Routing: OSPF Area 0 Backbone
- Core switches and Distribution switches participate in single-area OSPF (`Process ID 1`, `Area 0`).
- Point-to-point network type (`ip ospf network point-to-point`) configured on all routed interconnects to minimize hello timer latency and eliminate DR/BDR election overhead.
- User-facing SVIs are designated as `passive-interface` under `router ospf 1` to advertise endpoint subnets into the backbone while blocking OSPF hello packets and adjacency formation on access segments.

---

## 🔒 Campus Security & Hardening

1. **Access Port Hardening:**
   - `spanning-tree portfast` and `spanning-tree bpduguard enable` enabled on all host-facing ports.
   - Unused ports assigned to dummy blackhole VLAN 99 and administratively shut down.
2. **Guest Network Isolation (Access Control List):**
   - Access-list `ACL-GUEST-RESTRICTION` applied inbound on `interface Vlan60` blocking RFC 1918 internal corporate destinations while permitting DNS, DHCP, and Internet egress.
3. **Control Plane Security:**
   - Dedicated management VLAN (VLAN 10) for SSHv2 access, AAA, and Syslog logging.

---

## 📂 Repository Layout

```
├── README.md                      # Comprehensive project summary & architecture
├── LICENSE                        # Open-source MIT license
├── configs/                       # Ready-to-deploy Cisco IOS configurations
│   ├── core-01.ios.cfg            # Core Switch 1 configuration
│   ├── core-02.ios.cfg            # Core Switch 2 configuration
│   ├── dist-01.ios.cfg            # Distribution Multilayer Switch 1
│   ├── dist-02.ios.cfg            # Distribution Multilayer Switch 2
│   ├── access-01.ios.cfg          # Access Layer Switch 1
│   ├── access-02.ios.cfg          # Access Layer Switch 2
│   └── edge-router.ios.cfg        # WAN / Edge Gateway Router
├── docs/                          # Detailed engineering documentation
│   ├── ARCHITECTURE.md            # In-depth architectural design specification
│   ├── TOPOLOGY.md                # Port-to-port interconnect & cabling mapping
│   └── TESTING_AND_VERIFICATION.md# Complete test plan, show commands & failover drills
├── scripts/                       # Automation & validation scripts
│   └── verify_configs.py          # Python configuration linter & IP validation tool
└── simulations/                   # Simulator setup and deployment guides
    └── PACKET_TRACER_GUIDE.md     # Cisco Packet Tracer step-by-step setup guide
```

---

## 🚀 Quick Start: Deployment in Cisco Packet Tracer

1. Open Cisco Packet Tracer (v8.x recommended).
2. Deploy the hardware models:
   - **Core Layer:** 2x Cisco Catalyst 3650-24PS or 3560-24PS (Multilayer switches)
   - **Distribution Layer:** 2x Cisco Catalyst 3650-24PS or 3560-24PS (Multilayer switches)
   - **Access Layer:** 2x Cisco Catalyst 2960-24TT (Layer 2 switches)
   - **Edge Router:** 1x Cisco 2911 or 4331 Integrated Services Router (ISR)
3. Connect the interfaces following [docs/TOPOLOGY.md](docs/TOPOLOGY.md).
4. Paste the configuration files from the [`configs/`](configs/) directory into the CLI of each respective device.
5. Execute the validation steps in [docs/TESTING_AND_VERIFICATION.md](docs/TESTING_AND_VERIFICATION.md).

---

## 🧪 Validation Script

Run the automated Python configuration verification script to check for subnet overlaps, HSRP VIP alignment, and syntax integrity:

```bash
python3 scripts/verify_configs.py
```

---

## 👤 Author & Maintainer

- **Author:** Kasu Sathvika Mary
- **GitHub:** [@KasuSathvikaMary](https://github.com/KasuSathvikaMary)
- **Email:** kasusathvika@gmail.com
