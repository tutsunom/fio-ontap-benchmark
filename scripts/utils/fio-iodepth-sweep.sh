#!/bin/bash
# 4k random read/write — iodepth sweep
# Usage: ./fio-iodepth-sweep.sh <VM_IP> <label>
# e.g.  ./fio-iodepth-sweep.sh 192.168.x.55 ontap-san

VM_IP="$1"
LABEL="${2:-test}"
OUTDIR="/root/fio-iodepth-results-${LABEL}"
mkdir -p "$OUTDIR"

IODEPTHS=(1 2 4 8 16 32 64 128)
PATTERNS=(randread randwrite)

TOTAL=$(( ${#IODEPTHS[@]} * ${#PATTERNS[@]} ))
COUNT=0

echo "=== fio iodepth sweep: $LABEL ($VM_IP) ==="
echo "Tests: $TOTAL (${#PATTERNS[@]} patterns x ${#IODEPTHS[@]} iodepths)"
echo ""

for pattern in "${PATTERNS[@]}"; do
  for depth in "${IODEPTHS[@]}"; do
    COUNT=$((COUNT + 1))
    OUTFILE="${OUTDIR}/${pattern}_iodepth${depth}.json"
    echo "[${COUNT}/${TOTAL}] ${pattern} iodepth=${depth} ... $(date +%H:%M:%S)"

    sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password cloud-user@${VM_IP} \
      "sudo /usr/local/bin/fio \
        --name=test \
        --ioengine=libaio \
        --direct=1 \
        --bs=4k \
        --rw=${pattern} \
        --iodepth=${depth} \
        --numjobs=1 \
        --size=450G \
        --runtime=300 \
        --ramp_time=10 \
        --time_based \
        --filename=/myvol/testfile \
        --output-format=json" > "$OUTFILE" 2>/dev/null

    # Show summary
    if [ "$pattern" = "randread" ]; then
      iops=$(python3 -c "import json; d=json.load(open()); print(f\"{d[jobs][0][read][iops]:.0f}\")")
      lat=$(python3 -c "import json; d=json.load(open()); print(f\"{d[jobs][0][read][lat_ns][mean]/1000:.1f}\")")
    else
      iops=$(python3 -c "import json; d=json.load(open()); print(f\"{d[jobs][0][write][iops]:.0f}\")")
      lat=$(python3 -c "import json; d=json.load(open()); print(f\"{d[jobs][0][write][lat_ns][mean]/1000:.1f}\")")
    fi
    echo "  -> IOPS: ${iops}  Latency: ${lat} µs"
    echo ""
  done
done

echo "=== 完了: $LABEL ==="
echo "Results in: $OUTDIR/"
