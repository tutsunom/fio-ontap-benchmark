#!/bin/bash
# Cache check v2: use volume statistics API to measure WAFL-level latency

ONTAP_PASS=$(oc get secret backend-ontap-nas-secret -n trident -o jsonpath='{.data.password}' | base64 -d)
ONTAP_USER=$(oc get secret backend-ontap-nas-secret -n trident -o jsonpath='{.data.username}' | base64 -d)
MGMT=192.168.x.103

# NAS datadisk volume name
NAS_VOL="trident_pvc_6e3fc26f_68cf_4b54_8fff_36ca69a6828a"
# Find SAN datadisk volume (500Gi LUN)
SAN_VOL=$(curl -sk -u "$ONTAP_USER:$ONTAP_PASS" \
    "https://$MGMT/api/storage/volumes?fields=name,space.size&max_records=50" 2>/dev/null \
    | python3 -c "
import sys,json
d = json.load(sys.stdin)
for r in d.get('records',[]):
    n = r.get('name','')
    sz = r.get('space',{}).get('size',0)
    if 'trident' in n and sz > 500000000000:
        print(n)
        break
")

echo "NAS vol: $NAS_VOL"
echo "SAN vol: $SAN_VOL"

SAN_IP=192.168.x.55
NAS_IP=192.168.x.56
FIO=/usr/local/bin/fio
NODE="wk-01.cluster.example.com"

get_vol_stats() {
    local VOL=$1
    curl -sk -u "$ONTAP_USER:$ONTAP_PASS" \
        "https://$MGMT/api/storage/volumes?name=$VOL&fields=statistics" 2>/dev/null \
    | python3 -c "
import sys,json
d = json.load(sys.stdin)
r = d['records'][0]['statistics']
print('%d %d' % (r['iops_raw']['read'], r['latency_raw']['read']))
"
}

run_test() {
    local LABEL=$1
    local VM_IP=$2
    local VOL=$3

    echo ""
    echo "============================================"
    echo "=== $LABEL ==="
    echo "============================================"

    # Drop caches
    echo "Dropping node caches..."
    oc debug node/$NODE --quiet -- chroot /host sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null
    sleep 3

    # BEFORE
    BEFORE=$(get_vol_stats "$VOL")
    B_OPS=$(echo $BEFORE | awk '{print $1}')
    B_LAT=$(echo $BEFORE | awk '{print $2}')
    echo "BEFORE: ops=$B_OPS cumulative_lat=$B_LAT"

    # Run fio 60s
    echo "Running fio (60s, iodepth=64, 4k randread)..."
    RESULT=$(sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${VM_IP} \
        "sudo $FIO --name=test --ioengine=libaio --direct=1 --bs=4k --rw=randread \
         --iodepth=64 --numjobs=1 --size=450G --runtime=60 --ramp_time=10 \
         --time_based --filename=/myvol/testfile --output-format=json" 2>/dev/null)

    # Extract fio-reported metrics
    echo "$RESULT" | python3 -c "
import sys,json
d = json.load(sys.stdin)
j = d['jobs'][0]['read']
print('fio reported: IOPS=%.0f  lat=%.1f us  bw=%.1f MiB/s' % (j['iops'], j['lat_ns']['mean']/1000, j['bw']/1024))
"

    # AFTER
    sleep 2
    AFTER=$(get_vol_stats "$VOL")
    A_OPS=$(echo $AFTER | awk '{print $1}')
    A_LAT=$(echo $AFTER | awk '{print $2}')
    echo "AFTER:  ops=$A_OPS cumulative_lat=$A_LAT"

    # Calculate
    python3 -c "
d_ops = $A_OPS - $B_OPS
d_lat = $A_LAT - $B_LAT
if d_ops > 0:
    avg_lat = d_lat / d_ops
    print('')
    print('ONTAP WAFL-level stats during test:')
    print('  Total read ops: %d' % d_ops)
    print('  Avg WAFL read latency: %.1f us' % avg_lat)
    print('')
    if avg_lat < 100:
        print('  >>> VERY LOW latency suggests HIGH cache hit rate')
    elif avg_lat < 200:
        print('  >>> Low latency suggests moderate cache hits')
    elif avg_lat < 400:
        print('  >>> Normal SSD latency range - minimal cache effect')
    else:
        print('  >>> High latency - disk/SSD bound, no cache benefit')
else:
    print('No delta ops detected')
"
}

echo "=== ONTAP Read Cache Hit Rate Check ==="
echo "=== $(date) ==="

run_test "ontap-nas (NFS nconnect=8)" "$NAS_IP" "$NAS_VOL"
run_test "ontap-san (iSCSI)" "$SAN_IP" "$SAN_VOL"

echo ""
echo "=== Done at $(date) ==="
