# Cisco Packet Tracer Simulation Guide

Step-by-step instructions to recreate the Multi-Tier Enterprise Campus LAN in **Cisco Packet Tracer**.

---

## 1. Required Devices in Packet Tracer

| Role | Device Type in Packet Tracer | Quantity | Recommended Icon/Model |
| :--- | :--- | :---: | :--- |
| **Core Switches** | Multilayer Switch 3650-24PS or 3560-24PS | 2 | `CORE-01`, `CORE-02` |
| **Distribution Switches** | Multilayer Switch 3650-24PS or 3560-24PS | 2 | `DIST-01`, `DIST-02` |
| **Access Switches** | Switch 2960-24TT | 2 | `ACC-01`, `ACC-02` |
| **Edge Router** | Router 2911 or 4331 | 1 | `EDGE-ROUTER` |
| **Endpoint PCs** | Generic PC / Laptop | 6+ | HR-PC, IT-PC, Fin-PC, Exec-PC, Guest-PC |

> **Note for 3650 Switches in Packet Tracer:** If using the 3650 model, drag the AC power supply from the module shelf into the empty power bay on the switch rear panel to power it on before connecting cables.

---

## 2. Step-by-Step Wiring & Setup

1. **Core Interconnect:**
   - Connect `CORE-01 Gi1/0/23` to `CORE-02 Gi1/0/23` (Copper Straight-Through or Cross-Over).
   - Connect `CORE-01 Gi1/0/24` to `CORE-02 Gi1/0/24`.
2. **Core to Distribution Routed Links:**
   - `CORE-01 Gi1/0/1` <-> `DIST-01 Gi1/0/1`
   - `CORE-01 Gi1/0/2` <-> `DIST-02 Gi1/0/1`
   - `CORE-02 Gi1/0/1` <-> `DIST-01 Gi1/0/2`
   - `CORE-02 Gi1/0/2` <-> `DIST-02 Gi1/0/2`
3. **Core to Edge Router:**
   - `CORE-01 Gi1/0/10` <-> `EDGE-ROUTER Gi0/0/0`
4. **Distribution Interconnect & Trunks:**
   - `DIST-01 Gi1/0/23` <-> `DIST-02 Gi1/0/23` (Po2)
   - `DIST-01 Gi1/0/24` <-> `DIST-02 Gi1/0/24` (Po2)
5. **Distribution to Access Layer:**
   - `DIST-01 Gi1/0/11` <-> `ACC-01 Gi0/1` (Po11)
   - `DIST-01 Gi1/0/12` <-> `ACC-01 Gi0/2` (Po11)
   - `DIST-02 Gi1/0/11` <-> `ACC-01 Gi0/3` (Po12)
   - `DIST-02 Gi1/0/12` <-> `ACC-01 Gi0/4` (Po12)
   - `DIST-01 Gi1/0/13` <-> `ACC-02 Gi0/1` (Po21)
   - `DIST-01 Gi1/0/14` <-> `ACC-02 Gi0/2` (Po21)
   - `DIST-02 Gi1/0/13` <-> `ACC-02 Gi0/3` (Po22)
   - `DIST-02 Gi1/0/14` <-> `ACC-02 Gi0/4` (Po22)
6. **Endpoints to Access Switches:**
   - HR-PC: Connect to `ACC-01 Fa0/1` (VLAN 20) -> Set IP `10.10.20.101/24`, Gateway `10.10.20.1`
   - IT-PC: Connect to `ACC-01 Fa0/6` (VLAN 30) -> Set IP `10.10.30.101/24`, Gateway `10.10.30.1`
   - FIN-PC: Connect to `ACC-01 Fa0/11` (VLAN 40) -> Set IP `10.10.40.101/24`, Gateway `10.10.40.1`
   - EXEC-PC: Connect to `ACC-02 Fa0/16` (VLAN 50) -> Set IP `10.10.50.101/24`, Gateway `10.10.50.1`
   - GUEST-PC: Connect to `ACC-02 Fa0/21` (VLAN 60) -> Set IP `172.16.60.101/24`, Gateway `172.16.60.1`

---

## 3. Applying Configurations

Open the **CLI tab** for each device and paste the corresponding file from `configs/`:
- `configs/core-01.ios.cfg` -> `CORE-01`
- `configs/core-02.ios.cfg` -> `CORE-02`
- `configs/dist-01.ios.cfg` -> `DIST-01`
- `configs/dist-02.ios.cfg` -> `DIST-02`
- `configs/access-01.ios.cfg` -> `ACC-01`
- `configs/access-02.ios.cfg` -> `ACC-02`
- `configs/edge-router.ios.cfg` -> `EDGE-ROUTER`

---

## 4. GNS3 / EVE-NG Tips

If simulating in **GNS3** or **EVE-NG**:
- Use `Cisco vIOS-L2` for Access and Distribution switches.
- Use `Cisco vIOS-L3` or `IOU-L3` for Core switches and Edge Router.
- Interface naming in vIOS is typically `GigabitEthernet0/0`, `GigabitEthernet0/1`, etc. Substitute the port identifiers accordingly.
