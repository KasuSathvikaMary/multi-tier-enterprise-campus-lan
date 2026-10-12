# Network Testing, Verification, and Failover Runbook

This document provides a systematic verification checklist and operational runbook to validate Layer 2 segmentation, SVI routing, OSPF adjacency convergence, HSRPv2 failover, and link aggregation.

---

## 1. Layer 2 & EtherChannel Verification

### 1.1 Verify LACP EtherChannel Status
Run on all switches (`DIST-01`, `DIST-02`, `ACC-01`, `ACC-02`):
```cisco
show etherchannel summary
```
**Expected Output Check:**
- Flags should indicate `(SU)` for Layer 2 port-channels (`S` = Layer 2, `U` = in use).
- Member ports should display `(P)` (`P` = bundled in port-channel).
- Example:
  ```
  Group  Port-channel  Protocol    Ports
  ------+-------------+-----------+-----------------------------------------------
  2      Po2(SU)         LACP      Gi1/0/23(P)   Gi1/0/24(P)
  11     Po11(SU)        LACP      Gi1/0/11(P)   Gi1/0/12(P)
  ```

### 1.2 Verify 802.1Q Trunk Links & Native VLAN
```cisco
show interfaces trunk
```
**Expected Output Check:**
- Mode must be `on` or `desirable/active`.
- Encapsulation must be `802.1q`.
- Native VLAN must be `99` on all inter-switch trunks.
- Allowed VLANs must include `10,20,30,40,50,60`.

### 1.3 Verify Spanning Tree Topology & Root Placement
On `DIST-01`:
```cisco
show spanning-tree vlan 20
```
- Should report: `This bridge is the root` for VLANs 10, 20, 30.

On `DIST-02`:
```cisco
show spanning-tree vlan 40
```
- Should report: `This bridge is the root` for VLANs 40, 50, 60.

---

## 2. Layer 3 SVI & Inter-VLAN Routing Verification

### 2.1 Verify Switch Virtual Interfaces (SVIs)
On `DIST-01` and `DIST-02`:
```cisco
show ip interface brief | include Vlan
```
**Expected Output:**
```
Vlan10                 10.10.10.2      YES manual up                    up
Vlan20                 10.10.20.2      YES manual up                    up
Vlan30                 10.10.30.2      YES manual up                    up
Vlan40                 10.10.40.2      YES manual up                    up
Vlan50                 10.10.50.2      YES manual up                    up
Vlan60                 172.16.60.2     YES manual up                    up
```

### 2.2 Verify Inter-VLAN Ping from Endpoint Workstation
From an HR workstation (`10.10.20.101`):
```bash
# Ping Default Gateway
ping 10.10.20.1

# Ping IT Workstation across VLAN boundary
ping 10.10.30.101

# Ping Finance Workstation across VLAN boundary
ping 10.10.40.101
```

---

## 3. High Availability (HSRPv2) Verification

### 3.1 Check HSRP State & Roles
On `DIST-01`:
```cisco
show standby brief
```
**Expected Output:**
```
                     P indicates configured to preempt.
                     |
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Vl10        10   110 P Active  local           10.10.10.3      10.10.10.1
Vl20        20   110 P Active  local           10.10.20.3      10.10.20.1
Vl30        30   110 P Active  local           10.10.30.3      10.10.30.1
Vl40        40   100 P Standby 10.10.40.3      local           10.10.40.1
Vl50        50   100 P Standby 10.10.50.3      local           10.10.50.1
Vl60        60   100 P Standby 172.16.60.3     local           172.16.60.1
```

On `DIST-02`:
```cisco
show standby brief
```
- VLANs 10, 20, 30 must show `Standby`.
- VLANs 40, 50, 60 must show `Active`.

### 3.2 HSRP Failover Drill
1. Start a continuous ping from HR PC (`10.10.20.101`) to Core loopback `10.254.0.1`:
   ```bash
   ping -t 10.254.0.1
   ```
2. On `DIST-01`, simulate a catastrophic failure by shutting down the VLAN 20 interface or tracking uplink:
   ```cisco
   DIST-01(config)# interface Vlan 20
   DIST-01(config-if)# shutdown
   ```
3. Observe syslog on `DIST-02`:
   ```
   %HSRP-5-STATECHANGE: Vlan20 Grp 20 state Standby -> Active
   ```
4. Verify packet loss: Minimal to zero packet loss (1 echo packet lost maximum).
5. Recover interface on `DIST-01`:
   ```cisco
   DIST-01(config)# interface Vlan 20
   DIST-01(config-if)# no shutdown
   ```
6. Observe preemption delay timer: After 30 seconds, `DIST-01` gracefully re-assumes Active forwarder role.

---

## 4. OSPFv2 Dynamic Routing Verification

### 4.1 Verify OSPF Adjacency States
On `CORE-01`:
```cisco
show ip ospf neighbor
```
**Expected Output:**
All neighbors on transit interfaces should reach state `FULL/-` or `FULL/DR` / `FULL/BDR`:
```
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.254.0.2        1   FULL/  -        00:00:34    10.255.0.2      Port-channel1
10.254.0.11       1   FULL/  -        00:00:32    10.255.0.6      GigabitEthernet1/0/1
10.254.0.12       1   FULL/  -        00:00:38    10.255.0.14     GigabitEthernet1/0/2
10.254.0.254      1   FULL/  -        00:00:31    10.255.255.1    GigabitEthernet1/0/10
```

### 4.2 Verify Routing Table Propagation
On `CORE-01`:
```cisco
show ip route ospf
```
Should learn all endpoint VLAN subnets via Equal-Cost Multi-Path (ECMP) through `DIST-01` and `DIST-02`:
```
O        10.10.10.0/24 [110/2] via 10.255.0.6, GigabitEthernet1/0/1
                       [110/2] via 10.255.0.14, GigabitEthernet1/0/2
O        10.10.20.0/24 [110/2] via 10.255.0.6, GigabitEthernet1/0/1
                       [110/2] via 10.255.0.14, GigabitEthernet1/0/2
O        10.10.40.0/24 [110/2] via 10.255.0.6, GigabitEthernet1/0/1
                       [110/2] via 10.255.0.14, GigabitEthernet1/0/2
```

---

## 5. Security & Guest Isolation Verification

From a Guest PC on VLAN 60 (`172.16.60.101`):
1. Test Gateway reachability:
   ```bash
   ping 172.16.60.1       # SUCCESS
   ```
2. Test Isolation from Corporate HR Network:
   ```bash
   ping 10.10.20.101      # DESTINATION HOST UNREACHABLE (Blocked by ACL)
   ```
3. Test Isolation from Management:
   ```bash
   ping 10.10.10.2        # DESTINATION HOST UNREACHABLE (Blocked by ACL)
   ```
4. Test WAN / External Reachability:
   ```bash
   ping 10.254.0.254      # SUCCESS (Simulated Internet / Border Router)
   ```
