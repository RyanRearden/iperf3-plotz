import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.offsetbox import TextArea, AnnotationBbox
import os


file_path = 'data/data.json'
# Extract the JSON filename without extension for naming the output files
json_name = os.path.splitext(os.path.basename(file_path))[0]

# Load the data
with open(file_path, 'r') as file:
    data = json.load(file)

# Extract plot data
times = []
bytes_sent = []
times_recv = []
bytes_recv = []
times_loss = []
lost_percent = []
times_jitter = []
jitter_ms = []

for interval in data.get("intervals", []):
    for stream in interval.get("streams", []):
        if stream.get("sender"):
            times.append(stream["end"])
            bytes_sent.append(stream["bytes"])
        if stream.get("sender") is False:
            times_recv.append(stream["end"])
            bytes_recv.append(stream["bytes"])
            if "lost_percent" in stream:
                times_loss.append(stream["end"])
                lost_percent.append(stream["lost_percent"])
            if "jitter_ms" in stream:
                times_jitter.append(stream["end"])
                jitter_ms.append(stream["jitter_ms"])

# Extract metadata
start = data.get("start", {})
timestamp = start.get("timestamp", {})
protocol = start.get("test_start", {}).get("protocol", "N/A")
connected = start.get("connected", [{}])[0]  # use first connection

info_text = (
    f"Time: {timestamp.get('time')}\n"
    f"Protocol: {protocol}\n"
    f"Local Host: {connected.get('local_host')}\n"
    f"Remote Host: {connected.get('remote_host')}"
)
#looks nice
plt.style.use('seaborn-v0_8-whitegrid')

# BYTE SENDER PLOT 
fig1, ax1 = plt.subplots(1, 1, figsize=(12, 8))

ax1.plot(times, bytes_sent, marker='o', color='#007acc', linewidth=2, label='Bytes Sent (Sender)')
ax1.fill_between(times, bytes_sent, color='#007acc', alpha=0.1)

# Axis formatting for sender plot
ax1.set_title("Network Throughput: Bytes Sent Over Time", fontsize=18, weight='bold', pad=15)
ax1.set_xlabel("Time (seconds)", fontsize=14)
ax1.set_ylabel("Bytes Sent", fontsize=14)
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax1.tick_params(axis='both', which='major', labelsize=12)
legend1 = ax1.legend(fontsize=12, loc='upper right', frameon=True, fancybox=True, shadow=False)
legend1.get_frame().set_facecolor('whitesmoke')
legend1.get_frame().set_edgecolor('gray')
legend1.get_frame().set_alpha(0.95)

text_box = TextArea(info_text, textprops=dict(
    fontsize=11, family='monospace', linespacing=1.4
))

# Add a nice box :)
box = AnnotationBbox(
    text_box,
    (1, 0.02),  # Bottom-right of axes
    xycoords='axes fraction',
    boxcoords="offset points",
    box_alignment=(1, 0),  # Anchor box's bottom-right corner
    pad=0.5,
    frameon=True,
    bboxprops=dict(facecolor='whitesmoke', edgecolor='gray', alpha=0.95)
)
ax1.add_artist(box)

plt.tight_layout()
# Save sender plot
plt.savefig(f'graphs/senderBytes_{json_name}.jpg', dpi=300, bbox_inches='tight')
plt.close()

# Create receiver plot
fig2, ax2 = plt.subplots(1, 1, figsize=(12, 8))

ax2.plot(times_recv, bytes_recv, marker='s', color='#cc0000', linewidth=2, label='Bytes Received (Receiver)')
ax2.fill_between(times_recv, bytes_recv, color='#cc0000', alpha=0.1)
ax2.set_title("Network Throughput: Bytes Received Over Time", fontsize=18, weight='bold', pad=15)
ax2.set_xlabel("Time (seconds)", fontsize=14)
ax2.set_ylabel("Bytes Received", fontsize=14)
legend2 = ax2.legend(fontsize=12, loc='upper right', frameon=True, fancybox=True, shadow=False)
legend2.get_frame().set_facecolor('whitesmoke')
legend2.get_frame().set_edgecolor('gray')
legend2.get_frame().set_alpha(0.95)
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax2.tick_params(axis='both', which='major', labelsize=12)

# Add info text box to receiver plot as well
text_box2 = TextArea(info_text, textprops=dict(
    fontsize=11, family='monospace', linespacing=1.4
))

box2 = AnnotationBbox(
    text_box2,
    (1, 0.02),  # Bottom-right of axes
    xycoords='axes fraction',
    boxcoords="offset points",
    box_alignment=(1, 0),  # Anchor box's bottom-right corner
    pad=0.5,
    frameon=True,
    bboxprops=dict(facecolor='whitesmoke', edgecolor='gray', alpha=0.95)
)
ax2.add_artist(box2)

plt.tight_layout()
# Save receiver plot
plt.savefig(f'graphs/receiverBytes_{json_name}.jpg', dpi=300, bbox_inches='tight')
plt.close()

fig_loss, ax_loss = plt.subplots(figsize=(12, 6))
# Plot packet lost %
ax_loss.plot(times_loss, lost_percent, marker='^', color='#ff9900', linewidth=2, label='Packet Lost (%)')
ax_loss.fill_between(times_loss, lost_percent, color='#ff9900', alpha=0.1)
ax_loss.set_title("Receiver: Packets Lost Percentage Over Time", fontsize=16, weight='bold')
ax_loss.set_xlabel("Time (seconds)", fontsize=13)
ax_loss.set_ylabel("Packet Loss Percent", fontsize=13)
legend = ax_loss.legend(fontsize=12, loc='lower left', frameon=True, fancybox=True, shadow=False)
legend.get_frame().set_facecolor('whitesmoke')
legend.get_frame().set_edgecolor('gray')
legend.get_frame().set_alpha(0.95)
ax_loss.tick_params(axis='both', labelsize=11)

# Add annotation box
text_box_loss = TextArea(info_text, textprops=dict(fontsize=11, family='monospace', linespacing=1.4))
box_loss = AnnotationBbox(
    text_box_loss, (1, 0.02),  # Bottom-right of axes
    xycoords='axes fraction',
    boxcoords="offset points",
    box_alignment=(1, 0),  # Anchor box's bottom-right corner
    pad=0.5,
    frameon=True,
    bboxprops=dict(facecolor='whitesmoke', edgecolor='gray', alpha=0.95)
)
ax_loss.add_artist(box_loss)

# Save packet loss plot
plt.tight_layout()
plt.savefig(f'graphs/packetLoss_{json_name}.jpg', dpi=300, bbox_inches='tight')
plt.close()

# Create jitter plot
fig_jitter, ax_jitter = plt.subplots(figsize=(12, 6))
# Plot jitter ms
ax_jitter.plot(times_jitter, jitter_ms, marker='d', color='#9933cc', linewidth=2, label='Jitter (ms)')
ax_jitter.fill_between(times_jitter, jitter_ms, color='#9933cc', alpha=0.1)
ax_jitter.set_title("Network Jitter: Jitter Over Time", fontsize=18, weight='bold', pad=15)
ax_jitter.set_xlabel("Time (seconds)", fontsize=14)
ax_jitter.set_ylabel("Jitter (ms)", fontsize=14)
legend_jitter = ax_jitter.legend(fontsize=12, loc='upper right', frameon=True, fancybox=True, shadow=False)
legend_jitter.get_frame().set_facecolor('whitesmoke')
legend_jitter.get_frame().set_edgecolor('gray')
legend_jitter.get_frame().set_alpha(0.95)
ax_jitter.tick_params(axis='both', which='major', labelsize=12)

# Add info text box to jitter plot
text_box_jitter = TextArea(info_text, textprops=dict(
    fontsize=11, family='monospace', linespacing=1.4
))

box_jitter = AnnotationBbox(
    text_box_jitter,
    (0.01, 0.98),  # Top-left of axes
    xycoords='axes fraction',
    boxcoords="offset points",
    box_alignment=(0.01, 0.98), # Anchor box's top-left corner
    pad=0.5,
    frameon=True,
    bboxprops=dict(facecolor='whitesmoke', edgecolor='gray', alpha=0.95)
)
ax_jitter.add_artist(box_jitter)

# Save jitter plot
plt.tight_layout()
plt.savefig(f'graphs/jitter_{json_name}.jpg', dpi=300, bbox_inches='tight')
plt.close()

# Create combined plot for bytes sent and received
fig_combined, ax_combined = plt.subplots(1, 1, figsize=(12, 8))

# Plot both sender and receiver data
ax_combined.plot(times, bytes_sent, marker='o', color='#007acc', linewidth=2, label='Bytes Sent (Sender)')
ax_combined.plot(times_recv, bytes_recv, marker='s', color='#cc0000', linewidth=2, label='Bytes Received (Receiver)')

# Fill areas with transparency
ax_combined.fill_between(times, bytes_sent, color='#007acc', alpha=0.1)
ax_combined.fill_between(times_recv, bytes_recv, color='#cc0000', alpha=0.1)

# Axis formatting for combined plot
ax_combined.set_title("Network Throughput: Bytes Sent vs Received Over Time", fontsize=18, weight='bold', pad=15)
ax_combined.set_xlabel("Time (seconds)", fontsize=14)
ax_combined.set_ylabel("Bytes", fontsize=14)
ax_combined.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax_combined.tick_params(axis='both', which='major', labelsize=12)

# Legend with styled box
legend_combined = ax_combined.legend(fontsize=12, loc='upper right', frameon=True, fancybox=True, shadow=False)
legend_combined.get_frame().set_facecolor('whitesmoke')
legend_combined.get_frame().set_edgecolor('gray')
legend_combined.get_frame().set_alpha(0.95)

# Add info text box to combined plot
text_box_combined = TextArea(info_text, textprops=dict(
    fontsize=11, family='monospace', linespacing=1.4
))

box_combined = AnnotationBbox(
    text_box_combined,
    (1, 0.02),  # Bottom-right of axes
    xycoords='axes fraction',
    boxcoords="offset points",
    box_alignment=(1, 0),  # Anchor box's bottom-right corner
    pad=0.5,
    frameon=True,
    bboxprops=dict(facecolor='whitesmoke', edgecolor='gray', alpha=0.95)
)
ax_combined.add_artist(box_combined)

# Save combined plot
plt.tight_layout()
plt.savefig(f'graphs/combined_{json_name}.jpg', dpi=300, bbox_inches='tight')
plt.close()

print(f"Graphs saved as:")
print(f"- graphs/senderBytes_{json_name}.jpg")
print(f"- graphs/receiverBytes_{json_name}.jpg")
print(f"- graphs/packetLoss_{json_name}.jpg")
print(f"- graphs/jitter_{json_name}.jpg")
print(f"- graphs/combined_{json_name}.jpg")
