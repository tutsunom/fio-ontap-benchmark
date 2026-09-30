#!/bin/bash
# 検証2 LFSR SAN only redo (vdb mounted correctly)
exec > /root/fio-ontap/test2-lfsr-san-redo.log 2>&1

SAN_IP=192.168.x.55
FIO=/usr/local/bin/fio
NODE="wk-01.cluster.example.com"
RUNTIME=120
RAMP=10
SIZE=450G
FILENAME=/myvol/testfile
IODEPTHS="1 2 4 8 16 32 64 128"
PATTERNS="randread randwrite"
ITERATIONS=3

OUTDIR="/root/fio-ontap/test2-lfsr-san"
mkdir -p "$OUTDIR"

echo "============================================"
echo "=== SAN LFSR redo (vdb mounted) ==="
echo "=== $(date) ==="
echo "============================================"

# Verify mount
echo "Verifying /myvol mount..."
sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${SAN_IP} "df -h /myvol" 2>/dev/null
echo ""

TOTAL=$((8 * 2 * 3))
COUNT=0

for RW in $PATTERNS; do
    for ITER in $(seq 1 $ITERATIONS); do
        for DEPTH in $IODEPTHS; do
            COUNT=$((COUNT + 1))
            echo ""
            echo "=== [$COUNT/$TOTAL] SAN $RW iodepth=$DEPTH iter=$ITER === $(date +%H:%M:%S)"

            # Drop caches
            oc debug node/$NODE --quiet -- chroot /host sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null
            sleep 2

            if [ "$RW" = "randread" ]; then KEY="read"; else KEY="write"; fi

            sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${SAN_IP} \
                "sudo $FIO \
                    --name=test \
                    --ioengine=libaio \
                    --direct=1 \
                    --bs=4k \
                    --rw=${RW} \
                    --iodepth=${DEPTH} \
                    --numjobs=1 \
                    --size=${SIZE} \
                    --runtime=${RUNTIME} \
                    --ramp_time=${RAMP} \
                    --time_based \
                    --filename=${FILENAME} \
                    --random_generator=lfsr \
                    --output-format=json" > "$OUTDIR/fio-iodepth${DEPTH}-${RW}-iter${ITER}.json" 2>/dev/null

            python3 -c "
import json
with open('$OUTDIR/fio-iodepth${DEPTH}-${RW}-iter${ITER}.json') as f:
    d = json.load(f)
j = d['jobs'][0]['$KEY']
print('  IOPS: %.0f  Lat: %.1f us  BW: %.1f MiB/s' % (j['iops'], j['lat_ns']['mean']/1000, j['bw']/1024))
" 2>/dev/null
        done
    done
done

echo ""
echo "============================================"
echo "=== SAN LFSR redo complete at $(date) ==="
echo "============================================"
