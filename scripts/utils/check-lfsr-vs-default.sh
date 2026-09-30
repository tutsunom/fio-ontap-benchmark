#!/bin/bash
# Compare tausworthe (default) vs LFSR random generator
# to measure cache effect on 4k randread iodepth=64

SAN_IP=192.168.x.55
NAS_IP=192.168.x.56
FIO=/usr/local/bin/fio
NODE="wk-01.cluster.example.com"
RUNTIME=120
RAMP=10

run_fio() {
    local LABEL=$1
    local IP=$2
    local RANDGEN=$3  # tausworthe or lfsr

    echo ""
    echo "--- $LABEL ($RANDGEN) ---"

    # Drop caches
    oc debug node/$NODE --quiet -- chroot /host sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null
    sleep 3

    sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${IP} \
        "sudo $FIO --name=test --ioengine=libaio --direct=1 --bs=4k --rw=randread \
         --iodepth=64 --numjobs=1 --size=450G --runtime=$RUNTIME --ramp_time=$RAMP \
         --time_based --filename=/myvol/testfile --random_generator=$RANDGEN \
         --output-format=json" 2>/dev/null \
    | python3 -c "
import sys,json
d = json.load(sys.stdin)
j = d['jobs'][0]['read']
print('  IOPS: %.0f  Latency: %.1f us  BW: %.1f MiB/s' % (j['iops'], j['lat_ns']['mean']/1000, j['bw']/1024))
"
}

echo "=== LFSR vs Default Random Generator Comparison ==="
echo "=== 4k randread, iodepth=64, runtime=${RUNTIME}s ==="
echo "=== $(date) ==="

echo ""
echo "===== ontap-nas (NFS nconnect=8) ====="
run_fio "NAS" "$NAS_IP" "tausworthe"
run_fio "NAS" "$NAS_IP" "lfsr"

echo ""
echo "===== ontap-san (iSCSI) ====="
run_fio "SAN" "$SAN_IP" "tausworthe"
run_fio "SAN" "$SAN_IP" "lfsr"

echo ""
echo "=== Done at $(date) ==="
