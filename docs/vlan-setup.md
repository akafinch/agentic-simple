# VLAN Setup Guide — Akamai Cloud Manager

This guide covers attaching a VLAN to your GPU instances so Ollama traffic stays on a private network.

> **Note:** VLAN setup is optional. The application works with any private IP connectivity between VMs. If your VMs already share a private network (e.g., same data center with private IPs), you can skip this and just update the IPs in `.env`.

## Prerequisites

- Two Akamai/Linode GPU instances in the **same region** (e.g., `us-sea` Seattle)
- Both VMs powered on and accessible via SSH

## Step 1: Create the VLAN

VLANs are created implicitly when you attach them to an instance configuration.

1. Log in to [Linode Cloud Manager](https://cloud.linode.com)
2. Navigate to **Linodes** → select **VM1** (orchestrator)
3. Go to **Configurations** tab
4. Click **Edit** on the active configuration
5. Scroll to **Network Interfaces**
6. Add a new interface:
   - **Purpose:** VLAN
   - **Label:** `demo-vlan`
   - **IPAM Address:** `10.0.0.1/24`
7. Click **Save**

## Step 2: Attach VM2 to the Same VLAN

1. Navigate to **Linodes** → select **VM2** (specialist)
2. Go to **Configurations** tab → **Edit**
3. Add a new interface:
   - **Purpose:** VLAN
   - **Label:** `demo-vlan` (must match exactly)
   - **IPAM Address:** `10.0.0.2/24`
4. Click **Save**

## Step 3: Reboot Both VMs

The VLAN interface (`eth1`) only appears after a reboot.

```bash
# On each VM:
sudo reboot
```

## Step 4: Configure VLAN IPs

After reboot, verify `eth1` exists and configure the IP:

```bash
# On VM1:
ip link show eth1        # Should show the interface
sudo make setup-vlan     # Reads ORCHESTRATOR_HOST from .env, applies Netplan

# On VM2:
ip link show eth1
sudo make setup-vlan     # Reads SPECIALIST_HOST from .env
```

## Step 5: Verify Connectivity

```bash
# From VM1:
ping -c 3 10.0.0.2

# From VM2:
ping -c 3 10.0.0.1
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `eth1` not found | VLAN not attached or VM not rebooted. Check Cloud Manager. |
| Can't ping peer | Check both VMs use the same VLAN label. Verify Netplan applied (`ip addr show eth1`). |
| Ollama unreachable over VLAN | Ensure Ollama is bound to `0.0.0.0:11434` (run `make setup-ollama`). Check UFW allows port 11434 from 10.0.0.0/24. |

## Without VLAN

If VLAN setup is impractical, you can use the VMs' private IPs directly:

1. Find each VM's private IP in Cloud Manager (under the **Network** tab)
2. Update `.env` on VM1:
   ```
   ORCHESTRATOR_HOST=<vm1-private-ip>
   SPECIALIST_HOST=<vm2-private-ip>
   MANAGER_BASE_URL=http://<vm1-private-ip>:11434
   SPECIALIST_BASE_URL=http://<vm2-private-ip>:11434
   ```
3. Ensure UFW allows Ollama traffic from the private subnet
