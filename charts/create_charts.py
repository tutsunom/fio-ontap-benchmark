import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 150

bs_labels = ['4k', '8k', '16k', '32k', '64k', '128k', '256k']
x = np.arange(len(bs_labels))

# Benchmark data (iter2-3 average with drop_caches, iter1 excluded)
data = {
    'randwrite': {
        'san_iops': [1940, 1765, 1673, 1531, 1332, 916, 665],
        'nas_iops': [1776, 1895, 1548, 1090, 965, 905, 737],
    },
    'randread': {
        'san_iops': [2418, 2406, 1931, 1730, 1463, 1292, 980],
        'nas_iops': [1869, 1703, 1414, 1192, 1032, 952, 656],
    },
    'write': {
        'san_bw': [8.7, 14.6, 27.7, 50.7, 88.7, 117.2, 176.1],
        'nas_bw': [8.1, 15.6, 25.0, 35.1, 61.9, 116.0, 188.6],
        'san_lat': [448.8, 534.5, 561.5, 614.4, 702.9, 1064.0, 1417.5],
        'nas_lat': [482.6, 500.0, 623.8, 887.2, 1006.8, 1075.6, 1323.1],
    },
    'read': {
        'san_bw': [18.2, 33.1, 46.8, 82.0, 144.8, 241.5, 396.4],
        'nas_bw': [10.7, 19.7, 31.9, 50.4, 92.7, 175.7, 269.5],
        'san_lat': [212.9, 234.4, 332.6, 379.4, 429.8, 515.7, 629.1],
        'nas_lat': [362.2, 394.1, 488.8, 618.4, 672.0, 709.4, 925.5],
    },
}

rw_san_lat = [512.8, 564.2, 595.2, 650.6, 747.8, 1089.6, 1500.7]
rw_nas_lat = [560.5, 525.0, 643.5, 914.8, 1033.1, 1102.1, 1354.4]
rr_san_lat = [411.4, 413.4, 515.5, 575.7, 681.5, 771.8, 1018.8]
rr_nas_lat = [532.8, 584.8, 704.8, 836.7, 966.9, 1048.4, 1520.8]

SAN_COLOR = '#2196F3'
NAS_COLOR = '#FF9800'
BAR_WIDTH = 0.35

outdir = './output'

# --- Chart 1: IOPS (Random Write / Random Read) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.bar(x - BAR_WIDTH/2, data['randread']['san_iops'], BAR_WIDTH, label='ontap-san', color=SAN_COLOR)
ax1.bar(x + BAR_WIDTH/2, data['randread']['nas_iops'], BAR_WIDTH, label='ontap-nas', color=NAS_COLOR)
ax1.set_title('Random Read — IOPS')
ax1.set_xlabel('Block Size')
ax1.set_ylabel('IOPS')
ax1.set_xticks(x)
ax1.set_xticklabels(bs_labels)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

ax2.bar(x - BAR_WIDTH/2, data['randwrite']['san_iops'], BAR_WIDTH, label='ontap-san', color=SAN_COLOR)
ax2.bar(x + BAR_WIDTH/2, data['randwrite']['nas_iops'], BAR_WIDTH, label='ontap-nas', color=NAS_COLOR)
ax2.set_title('Random Write — IOPS')
ax2.set_xlabel('Block Size')
ax2.set_ylabel('IOPS')
ax2.set_xticks(x)
ax2.set_xticklabels(bs_labels)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

fig.tight_layout()
fig.savefig(f'{outdir}/fio-chart-iops.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-iops.png')

# --- Chart 2: Bandwidth (Sequential Write / Sequential Read) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.bar(x - BAR_WIDTH/2, data['read']['san_bw'], BAR_WIDTH, label='ontap-san', color=SAN_COLOR)
ax1.bar(x + BAR_WIDTH/2, data['read']['nas_bw'], BAR_WIDTH, label='ontap-nas', color=NAS_COLOR)
ax1.set_title('Sequential Read — Throughput (MiB/s)')
ax1.set_xlabel('Block Size')
ax1.set_ylabel('MiB/s')
ax1.set_xticks(x)
ax1.set_xticklabels(bs_labels)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

ax2.bar(x - BAR_WIDTH/2, data['write']['san_bw'], BAR_WIDTH, label='ontap-san', color=SAN_COLOR)
ax2.bar(x + BAR_WIDTH/2, data['write']['nas_bw'], BAR_WIDTH, label='ontap-nas', color=NAS_COLOR)
ax2.set_title('Sequential Write — Throughput (MiB/s)')
ax2.set_xlabel('Block Size')
ax2.set_ylabel('MiB/s')
ax2.set_xticks(x)
ax2.set_xticklabels(bs_labels)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

fig.tight_layout()
fig.savefig(f'{outdir}/fio-chart-bandwidth.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-bandwidth.png')

# --- Chart 3: Latency (2 panels — Random IO only, in ms) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

panels = [
    (ax1, 'Random Read', rr_san_lat, rr_nas_lat),
    (ax2, 'Random Write', rw_san_lat, rw_nas_lat),
]
for ax, title, san_us, nas_us in panels:
    san_ms = [v / 1000 for v in san_us]
    nas_ms = [v / 1000 for v in nas_us]
    ax.plot(bs_labels, san_ms, 'o-', color=SAN_COLOR, label='ontap-san', linewidth=2, markersize=6)
    ax.plot(bs_labels, nas_ms, 's-', color=NAS_COLOR, label='ontap-nas', linewidth=2, markersize=6)
    ax.set_title(f'{title} — Avg Latency')
    ax.set_xlabel('Block Size')
    ax.set_ylabel('Latency (ms)')
    ax.legend()
    ax.grid(alpha=0.3)

fig.suptitle('Average Latency: ontap-san vs ontap-nas (ms) — Random IO', fontsize=14, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(f'{outdir}/fio-chart-latency.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-latency.png')

# --- Chart 4: Performance Ratio (SAN/NAS) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

def ratio(a, b):
    return [ai/bi for ai, bi in zip(a, b)]

rw_iops_ratio = ratio(data['randwrite']['san_iops'], data['randwrite']['nas_iops'])
rr_iops_ratio = ratio(data['randread']['san_iops'], data['randread']['nas_iops'])
sw_iops_ratio = ratio(data['write']['san_bw'], data['write']['nas_bw'])
sr_iops_ratio = ratio(data['read']['san_bw'], data['read']['nas_bw'])

for ax in [ax1, ax2]:
    ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('Block Size')
    ax.set_xticks(range(len(bs_labels)))
    ax.set_xticklabels(bs_labels)
    ax.grid(alpha=0.3)

sw_lat_ratio = ratio(data['write']['nas_lat'], data['write']['san_lat'])
rw_lat_ratio = ratio(rw_nas_lat, rw_san_lat)
sr_lat_ratio = ratio(data['read']['nas_lat'], data['read']['san_lat'])
rr_lat_ratio = ratio(rr_nas_lat, rr_san_lat)

ax1.plot(bs_labels, sr_lat_ratio, '^-', color='#2E7D32', label='Seq Read', linewidth=2)
ax1.plot(bs_labels, rr_lat_ratio, 'D-', color='#FF8F00', label='Rand Read', linewidth=2)
ax1.plot(bs_labels, sw_lat_ratio, 'o-', color='#1565C0', label='Seq Write', linewidth=2)
ax1.plot(bs_labels, rw_lat_ratio, 's-', color='#42A5F5', label='Rand Write', linewidth=2)
ax1.set_title('Latency Ratio (NAS÷SAN)')
ax1.set_ylabel('Ratio (>1 = NAS slower)')
ax1.legend(fontsize=9)

ax2.plot(bs_labels, sr_iops_ratio, '^-', color='#2E7D32', label='Seq Read', linewidth=2)
ax2.plot(bs_labels, rr_iops_ratio, 'D-', color='#FF8F00', label='Rand Read', linewidth=2)
ax2.plot(bs_labels, sw_iops_ratio, 'o-', color='#1565C0', label='Seq Write', linewidth=2)
ax2.plot(bs_labels, rw_iops_ratio, 's-', color='#42A5F5', label='Rand Write', linewidth=2)
ax2.set_title('IOPS / Throughput Ratio (SAN÷NAS)')
ax2.set_ylabel('Ratio (>1 = SAN wins)')
ax2.legend(fontsize=9)

fig.suptitle('Performance Ratio: ontap-san / ontap-nas (>1 = SAN wins)', fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f'{outdir}/fio-chart-ratio.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-ratio.png')

# --- Chart 5: IOPS vs Latency scatter ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

for ax, title, san_iops, nas_iops, san_lat_us, nas_lat_us in [
    (ax1, 'Random Write', data['randwrite']['san_iops'], data['randwrite']['nas_iops'], rw_san_lat, rw_nas_lat),
    (ax2, 'Random Read', data['randread']['san_iops'], data['randread']['nas_iops'], rr_san_lat, rr_nas_lat),
]:
    san_lat_ms = [v / 1000 for v in san_lat_us]
    nas_lat_ms = [v / 1000 for v in nas_lat_us]
    ax.plot(san_iops, san_lat_ms, 'o-', color=SAN_COLOR, label='ontap-san', linewidth=2, markersize=7)
    ax.plot(nas_iops, nas_lat_ms, 's-', color=NAS_COLOR, label='ontap-nas', linewidth=2, markersize=7)
    for i, bs in enumerate(bs_labels):
        ax.annotate(bs, (san_iops[i], san_lat_ms[i]), textcoords='offset points', xytext=(8, 4), fontsize=8, color=SAN_COLOR)
        ax.annotate(bs, (nas_iops[i], nas_lat_ms[i]), textcoords='offset points', xytext=(8, -10), fontsize=8, color=NAS_COLOR)
    ax.set_title(f'{title} — IOPS vs Latency')
    ax.set_xlabel('IOPS')
    ax.set_ylabel('Latency (ms)')
    ax.set_yscale('log')
    ax.legend()
    ax.grid(alpha=0.3)

fig.suptitle('IOPS vs Latency (log scale, lower-right = better)', fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f'{outdir}/fio-chart-iops-vs-latency.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-iops-vs-latency.png')

print('All charts generated.')
