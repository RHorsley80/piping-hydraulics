import math
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from pipe_hydraulics import (calc_pipe_segment_p2_psia, transition_dp,
                              calc_pipe_diameter_change_k, get_pipe_id_inch)
from reference_datatables import (PIPE_ROUGHNESS_INCH, FITTING_DISPLAY_NAMES,
                                   FITTINGS_EXCLUDED_FROM_UI)

# Segment type selector
segment_type = st.selectbox("Segment Type",
    ["Pipe", "Reducer", "Enlarger", "Flow Split", "Flow Merge", "Pump"])

# Determine inlet conditions from previous segment or initial conditions
if st.session_state.segments:
    last_seg = st.session_state.segments[-1]
    inherited_flow = last_seg['flow_gpm']
    inherited_pressure = last_seg['outlet_pressure']
else:
    inherited_flow = st.session_state.total_flow_gpm
    inherited_pressure = st.session_state.inlet_pressure

st.info(f"Inherited from upstream: {inherited_flow:.1f} GPM at {inherited_pressure:.2f} psia")

# Pipe geometry - common to most segment types
if segment_type == "Pipe":
    col1, col2, col3 = st.columns(3)
    with col1:
        nps_inch = st.number_input("NPS (inches)", min_value=0.5, value=4.0)
    with col2:
        schedule = st.selectbox("Schedule", ['40', '80', 'STD', 'XS', 'XXS', '160'])
    with col3:
        material_options = list(PIPE_ROUGHNESS_INCH.keys())
        material = st.selectbox("Material", material_options,
                     index=material_options.index('steel_commercial_new'))

    col1, col2, col3 = st.columns(3)
    with col1:
        pipe_length_ft = st.number_input("Pipe Length (ft)", min_value=0.1, value=100.0)
    with col2:
        elev1_ft = st.number_input("Inlet Elevation (ft)", value=0.0)
    with col3:
        elev2_ft = st.number_input("Outlet Elevation (ft)", value=0.0)

# Reducer/Enlarger specific
if segment_type in ["Reducer", "Enlarger"]:
        st.write(f"Incoming flow: {inherited_flow:.1f} GPM at {inherited_pressure:.2f} psia")
        outlet_default = 2.0 if segment_type == "Reducer" else 6.0

        col1, col2, col3 = st.columns(3)
        with col1:
            inlet_nps = st.number_input("Inlet NPS (inches)", min_value=0.5, value=4.0)
            inlet_schedule = st.selectbox("Inlet Schedule",
                                ['40', '80', 'STD', 'XS', 'XXS', '160'],
                                key='inlet_schedule')
        with col2:
            outlet_nps = st.number_input("Outlet NPS (inches)", min_value=0.5, value=outlet_default)
            outlet_schedule = st.selectbox("Outlet Schedule",
                                ['40', '80', 'STD', 'XS', 'XXS', '160'],
                                key='outlet_schedule')
        with col3:
            angle_degrees = st.number_input("Transition Angle (degrees)",
                                             min_value=1.0, max_value=179.0, value=45.0)
            material_options = list(PIPE_ROUGHNESS_INCH.keys())
            trans_material = st.selectbox("Material", material_options,
                             index=material_options.index('steel_commercial_new'),
                             key='trans_material')

if segment_type in ["Reducer", "Enlarger"]:
    if st.session_state.segments:
        last_seg = st.session_state.segments[-1]
        # Check if last segment was a pipe and extract its NPS
        if 'details' in last_seg and last_seg['details']:
            upstream_nps = last_seg['details']['inputs'].get('pipe nps (inch)', None)
            if upstream_nps and inlet_nps != upstream_nps:
                st.warning(f"Note: Upstream pipe is {upstream_nps}\". "
                          f"Inlet NPS of {inlet_nps}\" differs — "
                          f"confirm this is intentional.")

# Flow split specific
if segment_type == "Flow Split":
    st.write(f"Incoming flow: {inherited_flow:.1f} GPM")
    branch_flow = st.number_input("Flow leaving main path (GPM)",
                                   min_value=0.1,
                                   max_value=float(inherited_flow)-0.1,
                                   value=inherited_flow/2)
    st.info(f"Flow continuing downstream: {inherited_flow - branch_flow:.1f} GPM")

# Flow merge specific
if segment_type == "Flow Merge":
    added_flow = st.number_input("Flow joining main path (GPM)",
                                  min_value=0.1, value=10.0)
    st.info(f"Total flow after merge: {inherited_flow + added_flow:.1f} GPM")

# Fittings - only for pipe segments
if segment_type == "Pipe":
    st.subheader("Fittings")
    fitting_counts = {}

    for key, display_name in FITTING_DISPLAY_NAMES.items():
        if key not in FITTINGS_EXCLUDED_FROM_UI:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(display_name)
                with col2:
                    qty = st.number_input(" ", min_value=0, value=0,
                                          step=1, key=f"fitting_{key}")
                    if qty > 0:
                        fitting_counts[key] = qty
                st.divider()
else:
    fitting_counts = {}

    if segment_type == "Pump":
        st.write(f"Incoming flow: {inherited_flow:.1f} GPM at {inherited_pressure:.2f} psia")

        pump_type = st.radio("Pump Type",
                             ["Centrifugal", "Positive Displacement"])

        if pump_type == "Positive Displacement":
            st.info(f"Flow rate inherited from upstream: {inherited_flow:.1f} GPM")
            pump_mode = st.radio("Specify pump by",
                                 ["Discharge Pressure (psia)",
                                  "Differential Pressure (psi)"])
        else:
            pump_mode = st.radio("Specify pump by",
                                 ["Discharge Pressure (psia)",
                                  "Differential Pressure (psi)",
                                  "Head-Flow Curve (centrifugal only)"])

        # Input blocks — run for all valid mode/type combinations
        if pump_mode == "Discharge Pressure (psia)":
            pump_discharge_psia = st.number_input(
                "Discharge Pressure (psia)",
                min_value=float(inherited_pressure),
                value=float(inherited_pressure) + 50.0)
            pump_dp = pump_discharge_psia - inherited_pressure
            st.info(f"Discharge pressure: {pump_discharge_psia:.2f} psia "
                    f"(+{pump_dp:.2f} psi)")

        elif pump_mode == "Differential Pressure (psi)":
            pump_dp = st.number_input(
                "Differential Pressure (psi)",
                min_value=0.1, value=50.0)
            pump_discharge_psia = inherited_pressure + pump_dp
            st.info(f"Discharge pressure: {pump_discharge_psia:.2f} psia "
                    f"(+{pump_dp:.2f} psi)")

        elif pump_mode == "Head-Flow Curve (centrifugal only)":
            st.write("Enter pump curve data points (minimum 3, maximum 7):")
            st.caption("Tip: Include shutoff head (Q=0) and runout point for best fit")

            num_points = st.slider("Number of curve points",
                                   min_value=3, max_value=7, value=3)

            curve_data = []
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Flow (GPM)**")
            with col2:
                st.write("**Head (ft)**")

            for i in range(num_points):
                col1, col2 = st.columns(2)
                with col1:
                    q = st.number_input(f"Q{i + 1}", min_value=0.0,
                                        value=float(i * 100),
                                        key=f"pump_q_{i}")
                with col2:
                    h = st.number_input(f"H{i + 1}", min_value=0.0,
                                        value=float(200 - i * 30),
                                        key=f"pump_h_{i}")
                curve_data.append((q, h))

            import numpy as np

            flows = np.array([p[0] for p in curve_data])
            heads = np.array([p[1] for p in curve_data])

            if len(set(flows)) >= 3:
                coeffs = np.polyfit(flows, heads, 2)
                q_range = np.linspace(0, max(flows) * 1.1, 100)
                h_fitted = np.polyval(coeffs, q_range)

                fig_pump, ax_pump = plt.subplots(figsize=(8, 4))
                ax_pump.plot(q_range, h_fitted, 'b-',
                             linewidth=2, label='Fitted curve')
                ax_pump.scatter(flows, heads, color='red',
                                zorder=5, label='Input points')

                h_operating = np.polyval(coeffs, inherited_flow)
                ax_pump.scatter(inherited_flow, h_operating,
                                color='green', s=200, zorder=6,
                                marker='*', label='Operating point')
                ax_pump.annotate(f"  {inherited_flow:.0f} GPM\n  {h_operating:.1f} ft",
                                 xy=(inherited_flow, h_operating),
                                 fontsize=9)

                ax_pump.set_xlabel("Flow Rate (GPM)")
                ax_pump.set_ylabel("Differential Head (ft)")
                ax_pump.set_title("Pump Curve")
                ax_pump.grid(True, alpha=0.3)
                ax_pump.legend()
                st.pyplot(fig_pump)
                plt.close()

                pump_dp = h_operating * st.session_state.density / 144
                pump_discharge_psia = inherited_pressure + pump_dp

                st.info(f"At {inherited_flow:.1f} GPM: "
                        f"Head = {h_operating:.1f} ft, "
                        f"ΔP = {pump_dp:.2f} psi, "
                        f"Discharge = {pump_discharge_psia:.2f} psia")
            else:
                st.warning("Please enter at least 3 distinct flow values")
                pump_dp = 0.0
                pump_discharge_psia = inherited_pressure
    #The "add segment" button code

if st.button("Add Segment"):
    try:
        if segment_type == "Pipe":
            result = calc_pipe_segment_p2_psia(
                inherited_flow, inherited_pressure, nps_inch, schedule,
                material, st.session_state.density, elev1_ft, elev2_ft,
                pipe_length_ft, fitting_counts, st.session_state.visc_cp)

            st.session_state.segments.append({
                'type': f"Pipe - {nps_inch}\" Sch {schedule}",
                'flow_gpm': inherited_flow,
                'inlet_pressure': inherited_pressure,
                'outlet_pressure': result['outputs']['outlet pressure (psia)'],
                'velocity_fps': result['outputs']['fluid velocity (fps)'],
                'reynolds': result['outputs']['reynolds number'],
                'friction_factor': result['outputs']['friction factor'],
                'head_loss_ft': result['outputs']['head loss (ft)'],
                'details': result,
                'inlet_nps': nps_inch,
                'outlet_nps': nps_inch,  # same for straight pipe
            })

        elif segment_type in ["Reducer", "Enlarger"]:

            inlet_id = get_pipe_id_inch(inlet_nps, inlet_schedule)
            outlet_id = get_pipe_id_inch(outlet_nps, outlet_schedule)

            if segment_type == "Reducer" and inlet_id <= outlet_id:
                st.error("Reducer inlet must be larger than outlet. Check your NPS values.")
                st.stop()
            if segment_type == "Enlarger" and inlet_id >= outlet_id:
                st.error("Enlarger outlet must be larger than inlet. Check your NPS values.")
                st.stop()

            k = calc_pipe_diameter_change_k(inlet_id, outlet_id, angle_degrees)
            velocity = inherited_flow / (7.4805 * 60) / (math.pi / 4 * (inlet_id / 12) ** 2)
            dp = transition_dp(st.session_state.density, k, velocity)
            outlet_pressure = inherited_pressure - dp

            st.session_state.segments.append({
                'type': f"{segment_type} - {inlet_nps}\" to {outlet_nps}\"",
                'flow_gpm': inherited_flow,
                'inlet_pressure': inherited_pressure,
                'outlet_pressure': outlet_pressure,
                'velocity_fps': velocity,
                'reynolds': 0,
                'friction_factor': 0,
                'head_loss_ft': dp * 144 / st.session_state.density,
                'details': {},
                'inlet_nps': inlet_nps,
                'outlet_nps': outlet_nps
            })

        elif segment_type == "Flow Split":

            # Get upstream NPS to pass through
            upstream_nps = (st.session_state.segments[-1]['outlet_nps']
                            if st.session_state.segments
                            else 4.0)

            st.session_state.segments.append({
                'type': f"Flow Split - {branch_flow:.1f} GPM leaves",
                'flow_gpm': inherited_flow - branch_flow,
                'inlet_pressure': inherited_pressure,
                'outlet_pressure': inherited_pressure,
                'velocity_fps': 0,
                'reynolds': 0,
                'friction_factor': 0,
                'head_loss_ft': 0,
                'details': {},
                'inlet_nps': upstream_nps,
                'outlet_nps': upstream_nps,  # flow splits/merges don't change diameter
            })

        elif segment_type == "Flow Merge":

            # Get upstream NPS to pass through
            upstream_nps = (st.session_state.segments[-1]['outlet_nps']
                            if st.session_state.segments
                            else 4.0)

            st.session_state.segments.append({
                'type': f"Flow Merge - {added_flow:.1f} GPM joins",
                'flow_gpm': inherited_flow + added_flow,
                'inlet_pressure': inherited_pressure,
                'outlet_pressure': inherited_pressure,
                'velocity_fps': 0,
                'reynolds': 0,
                'friction_factor': 0,
                'head_loss_ft': 0,
                'details': {},
                'inlet_nps': upstream_nps,
                'outlet_nps': upstream_nps,  # flow splits/merges don't change diameter
            })

        elif segment_type == "Pump":
            # Validate pump_dp is defined
            if pump_dp <= 0:
                st.error("Pump must add pressure. Check your inputs.")
                st.stop()

            pump_label = (f"{pump_type} Pump - "
                          f"{pump_mode.split('(')[0].strip()}")

            upstream_nps = (st.session_state.segments[-1]['outlet_nps']
                            if st.session_state.segments else 4.0)

            st.session_state.segments.append({
                'type': pump_label,
                'flow_gpm': inherited_flow,  # PD inherits, centrifugal TBD
                'inlet_pressure': inherited_pressure,
                'outlet_pressure': pump_discharge_psia,
                'velocity_fps': 0.0,
                'reynolds': 0,
                'friction_factor': 0.0,
                'head_loss_ft': -(pump_dp * 144 / st.session_state.density),  # negative = energy added
                'inlet_nps': upstream_nps,
                'outlet_nps': upstream_nps,
                'details': {
                    'inputs': {
                        'pump type': pump_type,
                        'pump mode': pump_mode,
                        'differential pressure (psi)': pump_dp,
                        'flow (gpm)': inherited_flow
                    }
                }
            })

        st.rerun()

    except ValueError as e:
        st.error(f"Calculation error: {e}")

# At the bottom of 1_Pipeline_Builder.py, after the Add Segment button
if st.session_state.segments:
    st.divider()
    st.caption("**Current pipeline:**")
    for i, seg in enumerate(st.session_state.segments):
        st.caption(f"Seg {i+1}: {seg['type']} — "
                  f"{seg['inlet_pressure']:.1f} → {seg['outlet_pressure']:.1f} psia")
    if st.button("Reset Pipeline", key="reset_builder"):
        st.session_state.segments = []
        st.rerun()