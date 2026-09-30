# fio-ontap-benchmark

A collection of [fio](https://fio.readthedocs.io/) benchmark scripts for testing NetApp ONTAP storage (ontap-nas / ontap-san) from VMs running on OpenShift Virtualization.

## Environment

| Component | Detail |
|---|---|
| Kubernetes | OpenShift Container Platform 4.x |
| Virtualization | OpenShift Virtualization |
| Storage | NetApp AFF C190 (ONTAP) |
| CSI Driver | Astra Trident (ontap-nas / ontap-san) |
| Benchmark Tool | fio 3.x |

## Tests

### Test 1: Block Size Sweep (Single VM)

Exhaustive benchmark across block sizes (4k–512k) and I/O patterns (randread / randwrite / seqread / seqwrite).

- `scripts/test1-blocksize-sweep/run-nas-nc8.sh` — NAS (nconnect=8)
- `scripts/test1-blocksize-sweep/run-san.sh` — SAN (iSCSI)

### Test 2: iodepth Sweep (Single VM)

Measures IOPS vs. latency (hockey-stick curve) by ramping iodepth from 1 to 128 with 4k random read/write.

- `scripts/test2-iodepth-sweep/run-san.sh` — SAN
- `scripts/test2-iodepth-sweep/run-nas-nc8.sh` — NAS (nconnect=8)
- `scripts/test2-iodepth-sweep/run-nas-nc1.sh` — NAS (nconnect=1, for comparison)

### Test 3: Multi-VM Parallel (3VM / 6VM)

Runs fio concurrently from multiple VMs to measure scalability under parallel load.

- `scripts/test3-multivm/run-all.sh` — SAN + NAS (3VM / 6VM)
- `scripts/test3-multivm/run-nas-6vm-redo.sh` — NAS 6VM re-measurement

## Directory Structure

```
.
├── scripts/
│   ├── setup/                      # Environment setup
│   │   ├── create-test3-vms.sh     #   Create VMs (OCP VirtualMachine manifests)
│   │   ├── setup-test3-vms.sh      #   Format and mount data disks
│   │   └── register-and-install-fio.sh  # Install fio on VMs
│   │
│   ├── test1-blocksize-sweep/      # Test 1: Block size sweep
│   ├── test2-iodepth-sweep/        # Test 2: iodepth sweep
│   ├── test3-multivm/              # Test 3: Multi-VM parallel
│   │
│   └── utils/                      # Utilities
│       ├── check-cache.sh          #   Measure ONTAP cache hit rate
│       ├── check-lfsr-vs-default.sh #  Compare LFSR vs tausworthe RNG
│       ├── fio-dropcache-sweep.sh  #   Block size sweep with drop_caches
│       └── fio-iodepth-sweep.sh    #   Standalone iodepth sweep
│
├── jobfiles/
│   └── fiojob.fio                  # fio job definition file (reference)
│
└── charts/                         # Chart generation scripts (Python)
    ├── create_charts.py            #   IOPS / bandwidth / latency charts
    ├── create_charts_nconnect.py   #   nconnect comparison charts
    ├── create_hockey_stick.py      #   Hockey-stick curve
    ├── create_hockey_stick_chart.py #  Hockey-stick curve (detailed)
    ├── create_iodepth_iops.py      #   iodepth vs IOPS chart
    └── gen_pptx.py                 #   PowerPoint slide generation
```

## Usage

### Prerequisites

- Logged into an OpenShift cluster via `oc`
- Astra Trident configured with ontap-nas / ontap-san backends
- SSH access to VMs via `sshpass`

### Configuration

Replace the following placeholders in the scripts with your environment values:

| Placeholder | Description |
|---|---|
| `192.168.x.*` | VM IP addresses |
| `<PASSWORD>` | VM SSH password |
| `<ORG_ID>` | subscription-manager org ID |
| `<ACTIVATION_KEY>` | subscription-manager activation key |
| `cluster.example.com` | OpenShift cluster domain |

## fio Parameters

Key test parameters:

| Parameter | Value |
|---|---|
| ioengine | libaio |
| direct | 1 (O_DIRECT) |
| numjobs | 1 |
| runtime | 120s–300s |
| ramp_time | 10s |
| size | 450G |
| random_generator | lfsr |
