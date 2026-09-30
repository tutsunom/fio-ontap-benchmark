#!/bin/bash
# fio benchmark with drop_caches before each test pattern, 3 iterations
# Usage: ./fio-dropcache-sweep.sh <vm_ip> <output_dir>

VM_IP="$1"
OUTDIR="$2"
NODE="wk-03.cluster.example.com"
SSH_CMD="sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${VM_IP}"
FIO="/usr/local/bin/fio"

BLOCK_SIZES="4k 8k 16k 32k 64k 128k 256k"
PATTERNS="randwrite write randread read"
RUNTIME=120
RAMP_TIME=10
SIZE="450G"
FILENAME="/myvol/testfile"
ITERATIONS=3

mkdir -p "$OUTDIR"

total=$((28 * ITERATIONS))
count=0

for iter in $(seq 1 $ITERATIONS); do
  echo "========================================"
  echo "=== Iteration $iter / $ITERATIONS ==="
  echo "========================================"
  for bs in $BLOCK_SIZES; do
    for rw in $PATTERNS; do
      count=$((count + 1))
      echo "=== [$count/$total] iter=$iter bs=$bs rw=$rw ==="

      # Drop caches on the node
      echo "  Dropping caches on $NODE..."
      oc debug node/$NODE --quiet -- chroot /host sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null
      sleep 2

      # Run fio
      echo "  Running fio (runtime=${RUNTIME}s)..."
      $SSH_CMD "sudo $FIO \
        --name=test \
        --ioengine=libaio \
        --direct=1 \
        --bs=$bs \
        --rw=$rw \
        --size=$SIZE \
        --numjobs=1 \
        --iodepth=1 \
        --runtime=$RUNTIME \
        --time_based \
        --ramp_time=$RAMP_TIME \
        --startdelay=5 \
        --filename=$FILENAME \
        --output-format=json" > "$OUTDIR/fio-${bs}-${rw}-iter${iter}.json" 2>/dev/null

      # Extract key metrics
      if [ "$rw" = "read" ] || [ "$rw" = "randread" ]; then
        iops=$(python3 -c "import json; d=json.load(open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json')); print(f\"{d['jobs'][0]['read']['iops']:.0f}\")" 2>/dev/null)
        lat=$(python3 -c "import json; d=json.load(open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json')); print(f\"{d['jobs'][0]['read']['lat_ns']['mean']/1000:.1f}\")" 2>/dev/null)
        bw=$(python3 -c "import json; d=json.load(open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json')); print(f\"{d['jobs'][0]['read']['bw']/1024:.1f}\")" 2>/dev/null)
      else
        iops=$(python3 -c "import json; d=json.load(open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json')); print(f\"{d['jobs'][0]['write']['iops']:.0f}\")" 2>/dev/null)
        lat=$(python3 -c "import json; d=json.load(open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json')); print(f\"{d['jobs'][0]['write']['lat_ns']['mean']/1000:.1f}\")" 2>/dev/null)
        bw=$(python3 -c "import json; d=json.load(open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json')); print(f\"{d['jobs'][0]['write']['bw']/1024:.1f}\")" 2>/dev/null)
      fi
      echo "  Result: IOPS=$iops  Lat=${lat}us  BW=${bw}MiB/s"
      echo ""
    done
  done
done

echo "=== All $ITERATIONS iterations complete. Results in $OUTDIR ==="
