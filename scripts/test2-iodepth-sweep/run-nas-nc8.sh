#!/bin/bash
# test2 nc8 再測定: randread iter2-3 + randwrite iter1-3
exec > /root/fio-ontap/test2-nc8-remaining.log 2>&1

NAS_IP=192.168.x.56
FIO=/usr/local/bin/fio
RUNTIME=120
RAMP=10
SIZE=450G
FILENAME=/myvol/testfile
IODEPTHS="1 2 4 8 16 32 64 128"

NODE=$(oc get vmi rhel10-ontap-nas -n utubo-test -o jsonpath="{.status.nodeName}" 2>/dev/null)
echo "VM node: $NODE"

OUTDIR="/root/fio-ontap/test2-nc8-redo"
mkdir -p "$OUTDIR"

# iter1 randread は test2-warmcache-check から流用するのでコピー
for D in $IODEPTHS; do
    cp /root/fio-ontap/test2-warmcache-check/fio-iodepth${D}-randread.json \
       "$OUTDIR/fio-iodepth${D}-randread-iter1.json" 2>/dev/null
done

echo "============================================"
echo "=== test2 nc8 再測定 (remaining) ==="
echo "=== $(date) ==="
echo "============================================"

TOTAL=40
COUNT=0

# randread iter2-3
for ITER in 2 3; do
    for DEPTH in $IODEPTHS; do
        COUNT=$((COUNT + 1))
        echo ""
        echo "=== [$COUNT/$TOTAL] randread iodepth=$DEPTH iter=$ITER === $(date +%H:%M:%S)"

        oc debug node/$NODE --quiet -- chroot /host sh -c "sync; echo 3 > /proc/sys/vm/drop_caches" 2>/dev/null
        sleep 2

        sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${NAS_IP} \
            "sudo $FIO \
                --name=test \
                --ioengine=libaio \
                --direct=1 \
                --bs=4k \
                --rw=randread \
                --iodepth=${DEPTH} \
                --numjobs=1 \
                --size=${SIZE} \
                --runtime=${RUNTIME} \
                --ramp_time=${RAMP} \
                --time_based \
                --filename=${FILENAME} \
                --random_generator=lfsr \
                --output-format=json" > "$OUTDIR/fio-iodepth${DEPTH}-randread-iter${ITER}.json" 2>/dev/null

        python3 -c "
import json
with open('$OUTDIR/fio-iodepth${DEPTH}-randread-iter${ITER}.json') as f:
    d = json.load(f)
j = d['jobs'][0]['read']
print('  IOPS: %.0f  Lat: %.1f us  BW: %.1f MiB/s' % (j['iops'], j['lat_ns']['mean']/1000, j['bw']/1024))
" 2>/dev/null
    done
done

# randwrite iter1-3
for ITER in 1 2 3; do
    for DEPTH in $IODEPTHS; do
        COUNT=$((COUNT + 1))
        echo ""
        echo "=== [$COUNT/$TOTAL] randwrite iodepth=$DEPTH iter=$ITER === $(date +%H:%M:%S)"

        oc debug node/$NODE --quiet -- chroot /host sh -c "sync; echo 3 > /proc/sys/vm/drop_caches" 2>/dev/null
        sleep 2

        sshpass -p <PASSWORD> ssh -o StrictHostKeyChecking=no cloud-user@${NAS_IP} \
            "sudo $FIO \
                --name=test \
                --ioengine=libaio \
                --direct=1 \
                --bs=4k \
                --rw=randwrite \
                --iodepth=${DEPTH} \
                --numjobs=1 \
                --size=${SIZE} \
                --runtime=${RUNTIME} \
                --ramp_time=${RAMP} \
                --time_based \
                --filename=${FILENAME} \
                --random_generator=lfsr \
                --output-format=json" > "$OUTDIR/fio-iodepth${DEPTH}-randwrite-iter${ITER}.json" 2>/dev/null

        python3 -c "
import json
with open('$OUTDIR/fio-iodepth${DEPTH}-randwrite-iter${ITER}.json') as f:
    d = json.load(f)
j = d['jobs'][0]['write']
print('  IOPS: %.0f  Lat: %.1f us  BW: %.1f MiB/s' % (j['iops'], j['lat_ns']['mean']/1000, j['bw']/1024))
" 2>/dev/null
    done
done

echo ""
echo "============================================"
echo "=== 完了: $(date) ==="
echo "============================================"

# iter2-3 平均サマリ
echo ""
echo "=== iter2-3 平均サマリ ==="
python3 << 'PYEOF'
import json, os
outdir = "/root/fio-ontap/test2-nc8-redo"
for rw in ["randread", "randwrite"]:
    key = "read" if rw == "randread" else "write"
    print("\n%s:" % rw)
    print("%5s  %8s  %10s  %10s" % ("depth", "IOPS", "Lat(us)", "BW(MiB/s)"))
    print("-" * 40)
    for d in [1,2,4,8,16,32,64,128]:
        iops_list = []
        lat_list = []
        bw_list = []
        for i in [2,3]:
            fp = "%s/fio-iodepth%d-%s-iter%d.json" % (outdir, d, rw, i)
            if os.path.exists(fp):
                with open(fp) as f:
                    data = json.load(f)
                j = data["jobs"][0][key]
                iops_list.append(j["iops"])
                lat_list.append(j["lat_ns"]["mean"]/1000)
                bw_list.append(j["bw"]/1024)
        if iops_list:
            print("%5d  %8.0f  %10.1f  %10.1f" % (d, sum(iops_list)/len(iops_list), sum(lat_list)/len(lat_list), sum(bw_list)/len(bw_list)))
PYEOF
