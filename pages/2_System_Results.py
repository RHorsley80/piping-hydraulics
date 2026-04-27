import math
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import pandas as pd
from pipe_hydraulics import get_pipe_roughness_inch, get_pipe_id_inch

# Show existing segments summary if any exist

if st.session_state.segments:
    st.subheader("Defined Segments")
    for i, seg in enumerate(st.session_state.segments):
        st.write(f"**Segment {i + 1}:** {seg['type']} — "
                 f"Inlet: {seg['inlet_pressure']:.2f} psia, "
                 f"Outlet: {seg['outlet_pressure']:.2f} psia, "
                 f"Flow: {seg['flow_gpm']:.1f} GPM")

    # Summary table
    st.subheader("System Summary")
    import pandas as pd

    summary_data = []
    for i, seg in enumerate(st.session_state.segments):
        summary_data.append({
            'Segment': i + 1,
            'Type': seg['type'],
            'Flow (GPM)': f"{seg['flow_gpm']:.1f}",
            'Inlet P (psia)': f"{seg['inlet_pressure']:.2f}",
            'Outlet P (psia)': f"{seg['outlet_pressure']:.2f}",
            'ΔP (psi)': f"{seg['inlet_pressure'] - seg['outlet_pressure']:.2f}",
            'Velocity (fps)': f"{seg['velocity_fps']:.2f}",
            'Reynolds': f"{seg['reynolds']:.0f}",
            'Friction Factor': f"{seg['friction_factor']:.4f}",
        })

    df = pd.DataFrame(summary_data)
    df = df.set_index('Segment')  # use Segment as the index
    st.dataframe(df, use_container_width=True)

    # After building the summary table, check for diameter continuity
    st.subheader("System Warnings")
    for i in range(1, len(st.session_state.segments)):
        prev = st.session_state.segments[i - 1]
        curr = st.session_state.segments[i]
        prev_outlet = prev.get('outlet_nps', None)
        curr_inlet = curr.get('inlet_nps', None)
        if prev_outlet and curr_inlet and prev_outlet != curr_inlet:
            st.warning(f"Segment {i} outlet NPS ({prev_outlet}\") "
                       f"does not match Segment {i + 1} inlet NPS ({curr_inlet}\")")

    #Energy Grade Line Plot
    st.subheader("Energy Grade Line")

    if len(st.session_state.segments) > 1:

        # Build the EGL data points
        segment_numbers = [0]
        pressures = [st.session_state.segments[0]['inlet_pressure']]

        for seg in st.session_state.segments:
            segment_numbers.append(segment_numbers[-1] + 1)
            pressures.append(seg['outlet_pressure'])

        # Update x-axis labels to show "Inlet" then segment numbers
        x_labels = ['Inlet'] + [f"Seg {i + 1}" for i in range(len(st.session_state.segments))]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(segment_numbers, pressures, 'b-o', linewidth=2, markersize=8)
        ax.set_xticks(segment_numbers)
        ax.set_xticklabels(x_labels, rotation=45, ha='right')

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(segment_numbers, pressures, 'b-o', linewidth=2, markersize=8)

        # Label each segment
        for i, seg in enumerate(st.session_state.segments):
            ax.annotate(f"Seg {i + 1}\n{seg['type'].split('-')[0].strip()}",
                        xy=(i + 1, seg['outlet_pressure']),
                        xytext=(0, 15),
                        textcoords='offset points',
                        ha='center', fontsize=8)

        ax.set_xlabel("Segment Number")
        ax.set_ylabel("Pressure (psia)")
        ax.set_title("Energy Grade Line")
        ax.grid(True, alpha=0.3)
        ax.set_xticks(segment_numbers)
        ax.set_ylim(min(pressures) - 1, max(pressures) + 3)  # add headroom at top

        # Shade area under curve for visual impact
        ax.fill_between(segment_numbers, pressures,
                        min(pressures) - 1, alpha=0.1, color='blue')

        st.pyplot(fig)
        plt.close()

    else:
        st.info("Add at least two segments to display the Energy Grade Line.")

    # Cumulative pressure drop
    total_dp = (st.session_state.segments[0]['inlet_pressure'] -
                st.session_state.segments[-1]['outlet_pressure'])
    st.metric("Total System ΔP", f"{total_dp:.2f} psi")
#Moody Diagram
    st.subheader("Moody Diagram")

    if any(seg['reynolds'] > 0 for seg in st.session_state.segments):

        fig2, ax2 = plt.subplots(figsize=(12, 8))

        # Reynolds number range for background curves
        re_laminar = np.logspace(2.7, 4, 50)
        re_turbulent = np.logspace(4, 8, 200)

        # Laminar line: f = 64/Re
        ax2.plot(re_laminar, 64 / re_laminar, 'b-', linewidth=1.5, label='Laminar')

        # Background Moody curves for standard relative roughness values
        roughness_lines = [0.00001, 0.0001, 0.0002, 0.0005, 0.001,
                           0.002, 0.005, 0.01, 0.02, 0.05]

        for ed in roughness_lines:
            ff_values = []
            for re in re_turbulent:
                # Churchill correlation for each background curve
                A = (2.457 * math.log(((7 / re) ** 0.9 + 0.27 * ed) ** -1)) ** 16
                B = (37530 / re) ** 16
                f = 8 * ((8 / re) ** 12 + (A + B) ** -1.5) ** (1 / 12)
                ff_values.append(f)
            ax2.plot(re_turbulent, ff_values, 'gray', linewidth=0.8, alpha=0.6)
            # Label the roughness lines on the right side
            ax2.annotate(f'ε/D={ed}',
                         xy=(re_turbulent[-1], ff_values[-1]),
                         fontsize=7, color='gray',
                         va='center')

        # Plot operating points for each pipe segment
        colors = plt.cm.tab10(np.linspace(0, 1, len(st.session_state.segments)))

        for i, seg in enumerate(st.session_state.segments):
            if seg['reynolds'] > 0 and seg['friction_factor'] > 0:
                # Calculate relative roughness for this segment
                from pipe_hydraulics import get_pipe_roughness_inch, get_pipe_id_inch

                if 'details' in seg and seg['details']:
                    material = seg['details']['inputs'].get('pipe material',
                                                            'steel_commercial_new')
                    nps = seg['details']['inputs'].get('pipe nps (inch)', 4)
                    schedule = seg['details']['inputs'].get('pipe schedule', '40')
                    epsilon = get_pipe_roughness_inch(material)
                    pipe_id = get_pipe_id_inch(nps, schedule)
                    rel_roughness = epsilon / pipe_id

                ax2.scatter(seg['reynolds'], seg['friction_factor'],
                            color=colors[i], s=100, zorder=5,
                            label=f"Seg {i + 1}: {seg['type'].split('-')[0].strip()}")
                ax2.annotate(f"Seg {i + 1}",
                             xy=(seg['reynolds'], seg['friction_factor']),
                             xytext=(5, 5), textcoords='offset points',
                             fontsize=8, color=colors[i])

        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax2.set_xlabel('Reynolds Number', fontsize=12)
        ax2.set_ylabel('Darcy Friction Factor', fontsize=12)
        ax2.set_title('Moody Diagram', fontsize=14)
        ax2.set_xlim(5e2, 1e8)
        ax2.set_ylim(0.008, 0.1)
        ax2.grid(True, which='both', alpha=0.3)
        ax2.legend(loc='upper right', fontsize=8)
        ax2.text(1.10, 0.5, 'Relative Roughness (ε/D)',
                 transform=ax2.transAxes,
                 rotation=90, va='center', fontsize=12, color='black')

        st.pyplot(fig2)
        plt.close()

    else:
        st.info("Add at least one pipe segment to display the Moody Diagram.")

    # Reset button
    if st.button("Reset Pipeline"):
        st.session_state.segments = []
        st.rerun()