import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from pipe_hydraulics import calc_friction_factor

if 'segments' not in st.session_state:
    st.session_state.segments = []

st.title("System Results")

if not st.session_state.segments:
    st.info("No segments defined yet. Use the Pipeline Builder page to add segments.")
    st.stop()

segments = st.session_state.segments

# ---------------------------------------------------------------- Segments
st.subheader("Defined Segments")
for i, seg in enumerate(segments):
    st.write(f"**Segment {i + 1}:** {seg['type']} — "
             f"Inlet: {seg['inlet_pressure']:.2f} psia, "
             f"Outlet: {seg['outlet_pressure']:.2f} psia, "
             f"Flow: {seg['flow_gpm']:.1f} GPM")

# ----------------------------------------------------------- Summary table
st.subheader("System Summary")
summary_data = []
for i, seg in enumerate(segments):
    summary_data.append({
        'Segment': i + 1,
        'Type': seg['type'],
        'Flow (GPM)': f"{seg['flow_gpm']:.1f}",
        'Inlet P (psia)': f"{seg['inlet_pressure']:.2f}",
        'Outlet P (psia)': f"{seg['outlet_pressure']:.2f}",
        'Pressure Change (psi)': f"{seg['outlet_pressure'] - seg['inlet_pressure']:+.2f}",
        'Velocity (fps)': f"{seg['velocity_fps']:.2f}",
        'Reynolds': f"{seg['reynolds']:.0f}",
        'Friction Factor': f"{seg['friction_factor']:.4f}",
    })
df = pd.DataFrame(summary_data).set_index('Segment')
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------------- Warnings
st.subheader("System Warnings")

velocity_limit = st.number_input(
    "Velocity warning threshold (fps)", min_value=1.0, value=10.0, step=1.0,
    help="Common liquid rule of thumb is about 10 fps; adjust for your service.")

warning_count = 0

# Diameter continuity
for i in range(1, len(segments)):
    prev_outlet = segments[i - 1].get('outlet_nps')
    curr_inlet = segments[i].get('inlet_nps')
    if prev_outlet and curr_inlet and prev_outlet != curr_inlet:
        st.warning(f"Segment {i} outlet NPS ({prev_outlet}\") "
                   f"does not match Segment {i + 1} inlet NPS ({curr_inlet}\")")
        warning_count += 1

# Velocity (skips pumps, splits and merges, which store 0.0)
for i, seg in enumerate(segments):
    v = seg['velocity_fps']
    if v > velocity_limit:
        st.warning(f"Segment {i + 1} ({seg['type']}): velocity {v:.1f} fps "
                   f"exceeds the {velocity_limit:.1f} fps threshold.")
        warning_count += 1
for i, seg in enumerate(segments):
    for w in seg.get('warnings', []):
        st.warning(f"Segment {i + 1} ({seg['type']}): {w}")
        warning_count += 1
if warning_count == 0:
    st.caption("No warnings.")

# -------------------------------------------------------- Energy grade line
st.subheader("Energy Grade Line")
if len(segments) > 1:
    segment_numbers = list(range(len(segments) + 1))
    pressures = [segments[0]['inlet_pressure']] + [s['outlet_pressure'] for s in segments]
    x_labels = ['Inlet'] + [f"Seg {i + 1}" for i in range(len(segments))]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(segment_numbers, pressures, 'b-o', linewidth=2, markersize=8)

    for i, seg in enumerate(segments):
        ax.annotate(f"Seg {i + 1}\n{seg['type'].split('-')[0].strip()}",
                    xy=(i + 1, seg['outlet_pressure']),
                    xytext=(0, 15), textcoords='offset points',
                    ha='center', fontsize=8)

    ax.set_xticks(segment_numbers)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.set_ylabel("Pressure (psia)")
    ax.set_title("Energy Grade Line")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(min(pressures) - 1, max(pressures) + 3)
    ax.fill_between(segment_numbers, pressures, min(pressures) - 1, alpha=0.1, color='blue')

    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("Add at least two segments to display the Energy Grade Line.")

# ------------------------------------------------------ Net pressure change
net_change = segments[-1]['outlet_pressure'] - segments[0]['inlet_pressure']
st.metric("Net Pressure Change (outlet − inlet)", f"{net_change:+.2f} psi")

# ------------------------------------------------------------ Moody diagram
st.subheader("Moody Diagram")
if any(seg['reynolds'] > 0 for seg in segments):
    fig2, ax2 = plt.subplots(figsize=(12, 8))

    re_laminar = np.logspace(2.7, 4, 50)
    re_turbulent = np.logspace(4, 8, 200)
    ax2.plot(re_laminar, 64 / re_laminar, 'b-', linewidth=1.5, label='Laminar')

    # Background curves use the same Churchill function as the calculations
    # (epsilon/D passed with D = 1 gives relative roughness directly)
    roughness_lines = [0.00001, 0.0001, 0.0002, 0.0005, 0.001,
                       0.002, 0.005, 0.01, 0.02, 0.05]
    for ed in roughness_lines:
        ff_values = [calc_friction_factor(re, ed, 1.0) for re in re_turbulent]
        ax2.plot(re_turbulent, ff_values, 'gray', linewidth=0.8, alpha=0.6)
        ax2.annotate(f'ε/D={ed}', xy=(re_turbulent[-1], ff_values[-1]),
                     fontsize=7, color='gray', va='center')

    colors = plt.cm.tab10(np.linspace(0, 1, len(segments)))
    for i, seg in enumerate(segments):
        if seg['reynolds'] > 0 and seg['friction_factor'] > 0:
            ax2.scatter(seg['reynolds'], seg['friction_factor'],
                        color=colors[i % 10], s=100, zorder=5,
                        label=f"Seg {i + 1}: {seg['type'].split('-')[0].strip()}")
            ax2.annotate(f"Seg {i + 1}",
                         xy=(seg['reynolds'], seg['friction_factor']),
                         xytext=(5, 5), textcoords='offset points',
                         fontsize=8, color=colors[i % 10])

    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xlabel('Reynolds Number', fontsize=12)
    ax2.set_ylabel('Darcy Friction Factor', fontsize=12)
    ax2.set_title('Moody Diagram', fontsize=14)
    ax2.set_xlim(5e2, 1e8)
    ax2.set_ylim(0.008, 0.1)
    ax2.grid(True, which='both', alpha=0.3)
    ax2.legend(loc='upper right', fontsize=8)
    ax2.text(1.10, 0.5, 'Relative Roughness (ε/D)', transform=ax2.transAxes,
             rotation=90, va='center', fontsize=12, color='black')

    st.pyplot(fig2)
    plt.close(fig2)
else:
    st.info("Add at least one pipe segment to display the Moody Diagram.")

# ------------------------------------------------------------------- Reset
if st.button("Reset Pipeline"):
    st.session_state.segments = []
    st.rerun()