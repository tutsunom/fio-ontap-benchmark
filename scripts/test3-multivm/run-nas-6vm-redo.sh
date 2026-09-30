#!/bin/bash
# 検証3 LFSR NAS 6VM redo: randread + randwrite, 3 iter
cd /root/fio-ontap
SSH_OPTS="-o StrictHostKeyChecking=no -o PreferredAuthentications=password -o ConnectTimeout=10"
RUNTIME=120
RAMP=10
SIZE="80G"
FIO="/usr/bin/fio"
FILENAME="/myvol/testfile"

VM_IPS=(192.168.x.17 192.168.x.10 192.168.x.12 192.168.x.14 192.168.x.59 192.168.x.15)
VM_COUNT=6
ITERATIONS=3
IODEPTHS=(1 4 16 64)
PATTERNS=(randread randwrite)
OUTDIR="/root/fio-ontap/test3-lfsr-nas-6vm"

echo "============================================"
echo "=== 検証3 LFSR NAS 6VM redo ==="
echo "=== $(date) ==="
echo "============================================"
echo ""
echo "### NAS 6VM (2/2/2 on wk-01/02/03) ###"
for idx in $(seq 0 $((VM_COUNT-1))); do
  echo "  VM$((idx+1)): ${VM_IPS[$idx]}"
done

# Clean old results
rm -rf $OUTDIR
mkdir -p $OUTDIR

TOTAL=$((ITERATIONS * ${#IODEPTHS[@]} * ${#PATTERNS[@]}))
COUNT=0

for iter in $(seq 1 $ITERATIONS); do
  echo "--- Iteration $iter / $ITERATIONS ---"
  echo ""
  for rw in "${PATTERNS[@]}"; do
    for depth in "${IODEPTHS[@]}"; do
      COUNT=$((COUNT+1))
      echo "=== [$COUNT/$TOTAL] 6VM nas iter=$iter rw=$rw iodepth=$depth === $(date +%H:%M:%S)"

      LFSR_OPT=""
      if [[ "$rw" == rand* ]]; then
        LFSR_OPT="--random_generator=lfsr"
      fi

      pids=()
      for vm_idx in $(seq 0 $((VM_COUNT-1))); do
        ip=${VM_IPS[$vm_idx]}
        vm_num=$((vm_idx+1))
        outfile="$OUTDIR/fio-vm${vm_num}-iodepth${depth}-${rw}-iter${iter}.json"

        sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip \
          "sudo $FIO \
            --name=test \
            --ioengine=libaio \
            --direct=1 \
            --bs=4k \
            --rw=$rw \
            --size=$SIZE \
            --numjobs=1 \
            --iodepth=$depth \
            --runtime=$RUNTIME \
            --time_based \
            --ramp_time=$RAMP \
            --startdelay=5 \
            --filename=$FILENAME \
            $LFSR_OPT \
            --output-format=json" > "$outfile" 2>/dev/null &
        pids+=($!)
      done

      for pid in "${pids[@]}"; do wait $pid; done

      total_iops=0
      rw_key="read"; [ "$rw" = "randwrite" ] && rw_key="write"
      for vm_idx in $(seq 1 $VM_COUNT); do
        f="$OUTDIR/fio-vm${vm_idx}-iodepth${depth}-${rw}-iter${iter}.json"
        if [ -s "$f" ]; then
          iops=$(python3 -c "import json; d=json.load(open()); print(int(d[jobs][0][][iops]))" 2>/dev/null)
          total_iops=$((total_iops + ${iops:-0}))
        fi
      done
      echo "  Total IOPS: $total_iops"
      echo ""
    done
  done
done

echo "============================================"
echo "=== 検証3 LFSR NAS 6VM redo complete at $(date) ==="
echo "============================================"
