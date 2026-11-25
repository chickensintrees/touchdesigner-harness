# Running remotely

TouchDesigner needs **macOS or Windows with a GPU**. There's no Linux build and no headless mode. So "remote" means one of these:

## A. Local (start here)

TD and Claude Code run on your Mac or PC. This has the lowest latency and the least to go wrong.

## B. Drive your own machine from anywhere

TD and Claude Code still run on your Mac or PC. You steer the session from your phone, another computer, or claude.ai.

- Start Claude Code on the TD machine, in this repo, as a **Remote Control** session: `claude remote-control`, or use the Claude desktop app. It then shows up in the Claude Code app and on claude.ai/code. See https://code.claude.com/docs for the current steps.
- The MCP server stays on `127.0.0.1`, and only the local Claude Code talks to it. Nothing is exposed to the network.
- A cloud Claude Code session (like the one that wrote this harness) runs in a Linux container. It can edit the harness, but it can't reach TD unless it's attached to your machine through Remote Control.

## C. A GPU VM in the cloud (the "VPS" option)

A normal Linux VPS **cannot** run TD. You need a GPU VM running Windows (or a cloud Mac):

| Option | Notes |
|--------|-------|
| Windows GPU VM (e.g. AWS EC2 G4dn/G5, Azure NV-series, or a GPU desktop-as-a-service) | Install the vendor's GPU driver for that instance type. TD needs Vulkan, and stock VM display drivers won't work. |
| Cloud Mac (e.g. AWS EC2 Mac, MacStadium) | Apple Silicon GPUs run TD. AWS Mac hosts have a minimum allocation period, so check pricing before trying it out. |

Setup on the VM is the same as `SETUP.md`: TD, Claude Code, this repo, `lab.toe` with TDMCP. Then use option B on the VM itself, or SSH in and run `claude` in tmux.

Things to check (none tested yet):

- **Display:** TD needs a desktop session with the GPU attached. Use a GPU-aware remote desktop (NICE DCV, Parsec, or the provider's own), not plain RDP. RDP sessions often use a software display adapter.
- **License:** a TD key runs on **one machine at a time**. Moving it between your computer and the VM means deactivating on one before activating on the other. The Non-Commercial 1280×1280 cap still applies.
- **Never expose the MCP port** (13316 / 9981 / 9870) to the internet. These servers execute arbitrary Python. If Claude Code must run on a different machine from TD, tunnel the port (`ssh -L 13316:127.0.0.1:13316 vm`, or Tailscale) rather than binding TD to `0.0.0.0`.
- **Cost:** GPU VMs bill by the hour. Stop the instance when you're not using it.

When you've tried one of these, record what worked (instance type, driver, remote-desktop tool, TD build) at the bottom of this file.
