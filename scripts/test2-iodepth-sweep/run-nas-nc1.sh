#!/bin/bash
# 検証2 LFSR NAS nconnect=1
exec > /root/fio-ontap/test2-lfsr-nas-nc1.log 2>&1

NAS_IP=192.168.x.56
FIO=/usr/local/bin/fio
NODE="wk-03.cluster.example.com"
RUNTIME=120
RAMP=10
SIZE=450G
FILENAME=/myvol/testfile
IODEPTHS="1 2 4 8 16 32 64 128"
PATTERNS="randread randwrite"
ITERATIONS=3

OUTDIR="/root/fio-ontap/test2-lfsr-nas-nc1"
mkdir -p "$OUTDIR"

echo "============================================"
echo "=== NAS nconnect=1 LFSR test ==="
echo "=== $(date) ==="
echo "============================================"

TOTAL=$((8 * 2 * 3))
COUNT=0

for RW in $PATTERNS; do
    for ITER in $(seq 1 $ITERATIONS); do
        for DEPTH in $IODEPTHS; do
            COUNT=$((COUNT + 1))
            echo ""
            echo "=== [$COUNT/$TOTAL] NAS-nc1 $RW iodepth=$DEPTH iter=$ITER === $(date +%H:%M:%S)"

            oc debug node/$NODE --quiet -- chroot /host sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null
            sleep 2

            if [ "$RW" = "randread" ]; then KEY="read"; else KEY="write"; fi

            sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${NAS_IP} \
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
echo "=== NAS nconnect=1 LFSR complete at $(date) ==="
echo "============================================"
