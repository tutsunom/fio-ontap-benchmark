import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

san_randread = {
    'iodepth': [1, 2, 4, 8, 16, 32, 64, 128],
    'iops':    [5552, 16027, 29395, 57233, 107404, 152900, 187717, 186608],
    'lat_ms':  [0.179, 0.124, 0.135, 0.139, 0.148, 0.208, 0.340, 0.685],
}

nas_randread = {
    'iodepth': [1, 2, 4, 8, 16, 32, 64, 128],
    'iops':    [6891, 20348, 38123, 70270, 123437, 175654, 185302, 186018],
    'lat_ms':  [0.144, 0.097, 0.104, 0.113, 0.129, 0.181, 0.345, 0.687],
}

san_randwrite = {
    'iodepth': [1, 2, 4, 8, 16, 32, 64, 128],
    'iops':    [1843, 3871, 7377, 11995, 17240, 22792, 28650, 33311],
    'lat_ms':  [0.540, 0.515, 0.540, 0.665, 0.927, 1.403, 2.233, 3.841],
}

nas_randwrite = {
    'iodepth': [1, 2, 4, 8, 16, 32, 64, 128],
    'iops':    [942, 2710, 4923, 7880, 11017, 14273, 17279, 19554],
    'lat_ms':  [1.059, 0.736, 0.810, 1.013, 1.451, 2.240, 3.703, 6.545],
}

SAN_COLOR = '#2563EB'
NAS_COLOR = '#DC2626'

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
fig.suptitle('IOPS vs Latency — ontap-san (iSCSI) vs ontap-nas (NFS)\n4k Random I/O, iodepth sweep (1→128)',
             fontsize=15, fontweight='bold', y=0.98)

# --- Random Read ---
ax1.plot(san_randread['iops'], san_randread['lat_ms'],
         'o-', color=SAN_COLOR, linewidth=2.5, markersize=9, label='ontap-san (iSCSI)', zorder=5)
ax1.plot(nas_randread['iops'], nas_randread['lat_ms'],
         's-', color=NAS_COLOR, linewidth=2.5, markersize=9, label='ontap-nas (NFS)', zorder=5)

for i, d in enumerate(san_randread['iodepth']):
    ax1.annotate(f'{d}', (san_randread['iops'][i], san_randread['lat_ms'][i]),
                 textcoords="offset points", xytext=(10, -5), fontsize=8.5, color=SAN_COLOR, fontweight='bold')
for i, d in enumerate(nas_randread['iodepth']):
    ax1.annotate(f'{d}', (nas_randread['iops'][i], nas_randread['lat_ms'][i]),
                 textcoords="offset points", xytext=(-18, 8), fontsize=8.5, color=NAS_COLOR, fontweight='bold')

ax1.set_title('4k Random Read', fontsize=14, fontweight='bold', pad=12)
ax1.set_xlabel('IOPS', fontsize=12)
ax1.set_ylabel('Average Latency (ms)', fontsize=12)
ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x/1000:,.0f}k'))
ax1.legend(fontsize=11, loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 200000)
ax1.set_ylim(0, 0.8)

# --- Random Write ---
ax2.plot(san_randwrite['iops'], san_randwrite['lat_ms'],
         'o-', color=SAN_COLOR, linewidth=2.5, markersize=9, label='ontap-san (iSCSI)', zorder=5)
ax2.plot(nas_randwrite['iops'], nas_randwrite['lat_ms'],
         's-', color=NAS_COLOR, linewidth=2.5, markersize=9, label='ontap-nas (NFS)', zorder=5)

for i, d in enumerate(san_randwrite['iodepth']):
    ax2.annotate(f'{d}', (san_randwrite['iops'][i], san_randwrite['lat_ms'][i]),
                 textcoords="offset points", xytext=(10, -5), fontsize=8.5, color=SAN_COLOR, fontweight='bold')
for i, d in enumerate(nas_randwrite['iodepth']):
    ax2.annotate(f'{d}', (nas_randwrite['iops'][i], nas_randwrite['lat_ms'][i]),
                 textcoords="offset points", xytext=(-18, 8), fontsize=8.5, color=NAS_COLOR, fontweight='bold')

ax2.set_title('4k Random Write', fontsize=14, fontweight='bold', pad=12)
ax2.set_xlabel('IOPS', fontsize=12)
ax2.set_ylabel('Average Latency (ms)', fontsize=12)
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x/1000:,.0f}k'))
ax2.legend(fontsize=11, loc='upper left')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 36000)
ax2.set_ylim(0, 7.0)

plt.tight_layout(rect=[0, 0, 1, 0.94])
outpath = './output/fio-chart-hockey-stick.png'
plt.savefig(outpath, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Saved: {outpath}')
