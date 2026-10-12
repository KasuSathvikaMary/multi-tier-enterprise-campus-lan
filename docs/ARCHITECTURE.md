# Campus Network Architecture Specification

## 1. Executive Summary

This specification outlines the technical design of a resilient, scalable, multi-tier enterprise campus local area network (LAN). The design adopts the industry standard Cisco 3-Tier Hierarchical model, isolating broadcast domains at the Distribution layer through hardware-accelerated Switch Virtual Interfaces (SVIs) and routing core traffic via dynamic Open Shortest Path First (OSPFv2).

---

## 2. Hierarchical Tier Responsibilities

```
+---------------------------------------------------------------+
|                       CORE LAYER                              |
|  - High-speed routed packet transport                         |
|  - Redundant point-to-point Layer 3 transit links             |
|  - No packet filtering or policy overhead (maximum throughput) |
+---------------------------------------------------------------+
                               |
                               | (L3 Routed Interconnects / OSPF Area 0)
                               v
+---------------------------------------------------------------+
|                   DISTRIBUTION LAYER                          |
|  - Layer 2 / Layer 3 Boundary (Inter-VLAN SVI Routing)        |
|  - First Hop Redundancy Protocol (HSRPv2) Gateway Load-Share  |
|  - Spanning Tree Root Bridge for all Access VLANs             |
|  - Security Policy Enforcement (Access Lists, DHCP Snooping)  |
+---------------------------------------------------------------+
                               |
                               | (L2 802.1Q Trunks / LACP Port-Channels)
                               v
+---------------------------------------------------------------+
|                     ACCESS LAYER                              |
|  - High-density user endpoint and AP connectivity             |
|  - VLAN membership enforcement (HR, IT, Finance, Exec, Guest) |
|  - Layer 2 loop mitigation (STP PortFast, BPDU Guard)         |
|  - Port Security & storm control                              |
+---------------------------------------------------------------+
```

---

## 3. Layer 2 / Layer 3 Segmentation & SVI Routing

### 3.1 Segmentation Strategy
Departmental workloads are segmented into dedicated broadcast domains (VLANs). This prevents broadcast storms, establishes strict administrative security perimeters, and prepares the infrastructure for micro-segmentation.

| VLAN ID | Name | Role & Scope | Subnet | Gateway (HSRP VIP) |
| :---: | :--- | :--- | :--- | :--- |
| **10** | `MGMT` | Network Device Management (SSH/SNMP/Syslog) | `10.10.10.0/24` | `10.10.10.1` |
| **20** | `HR` | Human Resources workstations and servers | `10.10.20.0/24` | `10.10.20.1` |
| **30** | `IT_ENG` | IT operations, DevOps, and Engineering hosts | `10.10.30.0/24` | `10.10.30.1` |
| **40** | `FINANCE` | Accounting, ERP, and payment processing endpoints | `10.10.40.0/24` | `10.10.40.1` |
| **50** | `EXECUTIVES` | Executive leadership workstations | `10.10.50.0/24` | `10.10.50.1` |
| **60** | `GUEST` | Unauthenticated visitor and guest mobile devices | `172.16.60.0/24` | `172.16.60.1` |
| **99** | `NATIVE_PARK` | Native trunk VLAN; no endpoints or SVIs permitted | N/A | N/A |

### 3.2 Hardware-Accelerated SVI Routing
Multilayer Catalyst switches (`DIST-01` and `DIST-02`) perform routing via Application-Specific Integrated Circuits (ASICs) through Switch Virtual Interfaces:
- Ingress packets on an access port in VLAN 20 destined for VLAN 40 are routed at wire speed on the distribution multilayer switch using Cisco Express Forwarding (CEF).
- Access switches operate purely at Layer 2, keeping their cost and complexity low while offloading all routing to the redundant distribution cluster.

---

## 4. High Availability & First Hop Redundancy (HSRPv2)

### 4.1 Multi-Group Gateway Load Balancing
Rather than keeping one distribution switch entirely idle, traffic is balanced on a per-VLAN basis:
- **Group 1 (VLANs 10, 20, 30):** `DIST-01` is **Active** (Priority 110), `DIST-02` is **Standby** (Priority 100).
- **Group 2 (VLANs 40, 50, 60):** `DIST-02` is **Active** (Priority 110), `DIST-01` is **Standby** (Priority 100).

```
VLAN 10, 20, 30 Traffic ---------------> DIST-01 (Active)
                                            |
                                            | (Failover if DIST-01 fails)
                                            v
                                         DIST-02 (Standby)

VLAN 40, 50, 60 Traffic ---------------> DIST-02 (Active)
                                            |
                                            | (Failover if DIST-02 fails)
                                            v
                                         DIST-01 (Standby)
```

### 4.2 Deterministic Failover Settings
1. **Preemption:** `standby <vlan> preempt delay minimum 30` ensures that a recovering switch waits 30 seconds for OSPF and spanning tree topologies to converge before re-assuming the active gateway role.
2. **Object Tracking:**
   ```cisco
   track 1 interface GigabitEthernet1/0/1 line-protocol
   track 2 interface GigabitEthernet1/0/2 line-protocol
   interface Vlan20
    standby 20 track 1 decrement 20
   ```
   If a core-facing uplink goes down, the HSRP priority automatically decrements below 100, yielding the active state to the redundant distribution switch immediately.

---

## 5. Spanning Tree Protocol (STP) Tuning

The campus runs **Rapid Per-VLAN Spanning Tree Plus (Rapid-PVST+)**.

### 5.1 Root Bridge Alignment
To prevent traffic from traversing the inter-distribution trunk link under normal conditions, the STP Root Bridge is aligned with the active HSRP gateway:
- `DIST-01`: Root Primary (`priority 4096`) for VLANs 10, 20, 30; Root Secondary (`priority 8192`) for VLANs 40, 50, 60.
- `DIST-02`: Root Primary (`priority 4096`) for VLANs 40, 50, 60; Root Secondary (`priority 8192`) for VLANs 10, 20, 30.

### 5.2 Edge Port Protections
On all Access-layer host-facing ports:
- **PortFast:** Immediately transitions access ports to forwarding state, avoiding 30-second DHCP timeout issues.
- **BPDU Guard:** Shuts down the port into `err-disable` if any unauthorized switch or rogue bridge sends BPDUs.

---

## 6. Dynamic Routing: OSPFv2 (Backbone Area 0)

1. **Backbone Topology:** Core and Distribution switches establish single-area OSPF (Area 0) over routed point-to-point links (`/30` subnets).
2. **Deterministic Router IDs:**
   - `CORE-01`: Loopback0 `10.254.0.1`
   - `CORE-02`: Loopback0 `10.254.0.2`
   - `DIST-01`: Loopback0 `10.254.0.11`
   - `DIST-02`: Loopback0 `10.254.0.12`
   - `EDGE-ROUTER`: Loopback0 `10.254.0.254`
3. **Passive Interfaces:**
   - Under `router ospf 1`, `passive-interface default` is applied.
   - `no passive-interface <routed-uplink>` is explicitly enabled on transit links.
   - User SVIs remain passive: advertised into the routing table, but zero OSPF control packets sent to endpoint hosts.

---

## 7. Security Architecture

### 7.1 Guest Isolation ACL
Guest users on VLAN 60 (`172.16.60.0/24`) are blocked from contacting any corporate network (`10.0.0.0/8`):
```cisco
ip access-list extended ACL-GUEST-RESTRICTION
 remark Permit DHCP to local relay / gateway
 permit udp any any eq bootps
 remark Permit DNS queries to public DNS
 permit udp any host 8.8.8.8 eq domain
 permit udp any host 1.1.1.1 eq domain
 remark Deny all RFC 1918 corporate networks
 deny ip 172.16.60.0 0.0.0.255 10.0.0.0 0.255.255.255
 deny ip 172.16.60.0 0.0.0.255 192.168.0.0 0.0.255.255
 remark Permit all public Internet access
 permit ip 172.16.60.0 0.0.0.255 any
```

### 7.2 Layer 2 SVI Mitigation
- **Native VLAN:** Changed from default VLAN 1 to unused VLAN 99 across all 802.1Q trunks to neutralize VLAN-hopping exploits.
- **Unused Ports:** Explicitly placed in access mode, assigned to VLAN 99, and disabled (`shutdown`).
