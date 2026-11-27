import math
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from pipe_hydraulics import (calc_pipe_segment_p2_psia, transition_dp,
                             calc_pipe_diameter_change_k, get_pipe_id_inch,
                             calc_cv_required, calc_valve_dp,
                             calc_cv_fraction_from_open, calc_fraction_open_from_cv,
                             calc_choked_dp,
                             calc_dp_device_forward, calc_dp_device_bore_from_tap_dp,
                             calc_dp_device_bore_from_perm_loss, get_dp_device_warnings)
from reference_datatables import (PIPE_ROUGHNESS_INCH, FITTING_DISPLAY_NAMES,
                                  FITTINGS_EXCLUDED_FROM_UI,
                                  VALVE_FL_DEFAULTS, VALVE_CHARACTERISTICS, DP_DEVICES)

# Segment type selector
segment_type = st.selectbox("Segment Type",
    ["Pipe", "Reducer", "Enlarger", "Flow Split", "Flow Merge", "Pump",
     "Control Valve", "Orifice / Nozzle / Venturi"])

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
# Control valve specific
if segment_type == "Control Valve":
    st.write(f"Incoming flow: {inherited_flow:.1f} GPM at {inherited_pressure:.2f} psia")
    st.caption("Incompressible liquid service. Piping geometry factor (Fp) is neglected.")

    col1, col2 = st.columns(2)
    with col1:
        valve_type = st.selectbox("Valve Type", list(VALVE_FL_DEFAULTS.keys()))
        characteristic_label = st.selectbox("Inherent Characteristic",
                                            list(VALVE_CHARACTERISTICS.keys()))
    with col2:
        cv_max = st.number_input("Rated Cv (fully open)", min_value=0.1, value=200.0)
        valve_fl = st.number_input("FL (liquid pressure recovery factor)",
                                   min_value=0.1, max_value=1.0,
                                   value=VALVE_FL_DEFAULTS[valve_type],
                                   key=f"fl_{valve_type}")  # key resets the default when type changes
    st.caption("FL defaults are typical full-travel values only. For design, consult "
               "ANSI/ISA-75.01.01 or the vendor datasheet, and overwrite FL here.")

    characteristic = VALVE_CHARACTERISTICS[characteristic_label]
    rangeability = 50.0
    if characteristic == 'equal_percentage':
        rangeability = st.number_input("Rangeability (R)", min_value=5.0,
                                       max_value=200.0, value=50.0)

    valve_mode = st.radio("Calculate",
                          ["Rating: find ΔP from % open",
                           "Sizing: find % open from allowable ΔP"])
    density_now = st.session_state.density

    if valve_mode.startswith("Rating"):
        pct_open = st.number_input("Valve opening (%)", min_value=1.0,
                                   max_value=100.0, value=50.0)
        fraction_open = pct_open / 100
        cv_operating = cv_max * calc_cv_fraction_from_open(fraction_open, characteristic, rangeability)
        valve_dp = calc_valve_dp(inherited_flow, cv_operating, density_now)
    else:
        valve_dp = st.number_input("Allowable valve ΔP (psi)", min_value=0.1, value=15.0)
        cv_operating = calc_cv_required(inherited_flow, valve_dp, density_now)
        try:
            fraction_open = calc_fraction_open_from_cv(cv_operating / cv_max,
                                                       characteristic, rangeability)
        except ValueError as e:
            st.error(str(e))
            st.stop()

    valve_outlet_psia = inherited_pressure - valve_dp
    if valve_outlet_psia <= 0:
        st.error("Valve ΔP exceeds the inlet pressure. Check your inputs.")
        st.stop()

    # Warnings, stored with the segment so the results page can show them too
    pv = st.session_state.vapor_pressure_psia
    pc = st.session_state.critical_pressure_psia
    dp_choked = calc_choked_dp(inherited_pressure, pv, pc, valve_fl)
    valve_warnings = []
    if valve_dp > dp_choked:
        valve_warnings.append(
            f"Valve ΔP ({valve_dp:.1f} psi) exceeds the estimated choked ΔP "
            f"({dp_choked:.1f} psi). Flow is choked, with cavitation or flashing likely; "
            f"downstream numbers are unreliable. Screening estimate; confirm FL with the vendor.")
    elif valve_outlet_psia < pv:
        valve_warnings.append(
            f"Valve outlet pressure ({valve_outlet_psia:.2f} psia) is below the vapor "
            f"pressure ({pv:.2f} psia): flashing.")
    if not 0.2 <= fraction_open <= 0.8:
        valve_warnings.append(
            f"Valve is {fraction_open * 100:.0f}% open. Controllability is usually best "
            f"between about 20% and 80%.")

    st.info(f"Cv at operating point: {cv_operating:.1f}  |  Opening: {fraction_open * 100:.1f}%  |  "
            f"Valve ΔP: {valve_dp:.2f} psi  |  Outlet: {valve_outlet_psia:.2f} psia")
    for w in valve_warnings:
        st.warning(w)

    # Characteristic curve with operating point
    xs = np.linspace(0.02, 1.0, 100)
    ys = [calc_cv_fraction_from_open(x, characteristic, rangeability) for x in xs]
    fig_cv, ax_cv = plt.subplots(figsize=(6, 3.5))
    ax_cv.plot(xs * 100, np.array(ys) * 100, 'b-', linewidth=2)
    ax_cv.axvspan(20, 80, color='gray', alpha=0.1)
    ax_cv.scatter(fraction_open * 100, cv_operating / cv_max * 100,
                  color='green', s=200, marker='*', zorder=5, label='Operating point')
    ax_cv.set_xlabel("Valve opening (%)")
    ax_cv.set_ylabel("Cv (% of rated)")
    ax_cv.set_title(f"Inherent characteristic: {characteristic_label}")
    ax_cv.grid(True, alpha=0.3)
    ax_cv.legend()
    st.pyplot(fig_cv)
    plt.close(fig_cv)

# Orifice / nozzle / venturi specific
if segment_type == "Orifice / Nozzle / Venturi":
    st.write(f"Incoming flow: {inherited_flow:.1f} GPM at {inherited_pressure:.2f} psia")
    st.caption("Incompressible liquid. Discharge coefficients from ISO 5167 / ISO 15377 "
               "correlations (fluids library). The system pressure change is the PERMANENT loss, "
               "not the differential at the taps.")

    purpose = st.radio("Purpose", ["Restriction orifice (pressure letdown)",
                                   "Flow meter (differential)"], horizontal=True)
    is_ro = purpose.startswith("Restriction")

    col1, col2 = st.columns(2)
    with col1:
        device_label = st.selectbox("Device Type", list(DP_DEVICES.keys()))
        device = DP_DEVICES[device_label]
        taps = None
        if device['taps']:
            tap_label = st.selectbox("Pressure Taps", list(device['taps'].keys()))
            taps = device['taps'][tap_label]
    with col2:
        upstream_nps = (st.session_state.segments[-1]['outlet_nps']
                        if st.session_state.segments else 4.0)
        default_id = get_pipe_id_inch(upstream_nps)   # Sch 40 by default
        line_id_in = st.number_input("Line inside diameter (in)", min_value=0.1,
                                     value=round(default_id, 3), format="%.3f",
                                     key=f"dp_id_{upstream_nps}")  # key resets default if NPS changes
        st.caption(f"Defaults to the Sch 40 ID of the upstream {upstream_nps:g}\" line. "
                   "Overwrite it for other schedules.")

    dp_mode = st.radio("Calculate", ["Rating: find ΔP from bore",
                                     "Sizing: find bore from target ΔP"])
    density_now = st.session_state.density
    visc_now = st.session_state.visc_cp

    try:
        if dp_mode.startswith("Rating"):
            bore_in = st.number_input("Bore diameter (in)", min_value=0.01,
                                      value=2.0, format="%.4f")
        else:
            if is_ro:
                target_dp = st.number_input("Target permanent pressure loss (psi)",
                                            min_value=0.01, value=15.0)
                bore_in = calc_dp_device_bore_from_perm_loss(
                    inherited_flow, line_id_in, target_dp, density_now, visc_now,
                    inherited_pressure, device['meter_type'], taps)
            else:
                target_dp = st.number_input("Target differential at taps (psi)",
                                            min_value=0.01, value=3.6,
                                            help="1 psi = 27.68 inH2O")
                bore_in = calc_dp_device_bore_from_tap_dp(
                    inherited_flow, line_id_in, target_dp, density_now, visc_now,
                    inherited_pressure, device['meter_type'], taps)
        dp_res = calc_dp_device_forward(inherited_flow, line_id_in, bore_in, density_now,
                                        visc_now, inherited_pressure,
                                        device['meter_type'], taps)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    dp_outlet_psia = inherited_pressure - dp_res['perm_loss_psi']
    pv = st.session_state.vapor_pressure_psia
    dp_warnings = get_dp_device_warnings(device['limits'], line_id_in,
                                         dp_res['beta'], dp_res['re_pipe'])
    if dp_res['p2_tap_psia'] <= pv:
        dp_warnings.append(
            f"Pressure at the downstream tap/throat ({dp_res['p2_tap_psia']:.2f} psia) is at or "
            f"below vapor pressure ({pv:.2f} psia): cavitation or flashing is likely and the "
            f"ΔP correlation no longer holds. Screening check only.")
    elif dp_outlet_psia <= pv:
        dp_warnings.append(
            f"Recovered downstream pressure ({dp_outlet_psia:.2f} psia) is at or below vapor "
            f"pressure ({pv:.2f} psia): flashing downstream.")

    st.info(f"Bore: {bore_in:.4f} in  |  β: {dp_res['beta']:.3f}  |  C: {dp_res['C']:.4f}  |  "
            f"Re(pipe): {dp_res['re_pipe']:,.0f}")
    st.info(f"Differential at taps: {dp_res['tap_dp_psi']:.2f} psi "
            f"({dp_res['tap_dp_psi'] * 27.68:.1f} inH2O)  |  "
            f"Permanent loss: {dp_res['perm_loss_psi']:.2f} psi  |  "
            f"Outlet: {dp_outlet_psia:.2f} psia")
    for w in dp_warnings:
        st.warning(w)

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
        elif segment_type == "Control Valve":
            upstream_nps = (st.session_state.segments[-1]['outlet_nps']
                            if st.session_state.segments else 4.0)

            st.session_state.segments.append({
                'type': f"Control Valve - {fraction_open * 100:.0f}% open, Cv {cv_operating:.0f}",
                'flow_gpm': inherited_flow,
                'inlet_pressure': inherited_pressure,
                'outlet_pressure': valve_outlet_psia,
                'velocity_fps': 0.0,
                'reynolds': 0,
                'friction_factor': 0.0,
                'head_loss_ft': valve_dp * 144 / st.session_state.density,
                'inlet_nps': upstream_nps,
                'outlet_nps': upstream_nps,
                'warnings': valve_warnings,
                'details': {
                    'inputs': {
                        'valve type': valve_type,
                        'characteristic': characteristic_label,
                        'rated Cv': cv_max,
                        'FL': valve_fl,
                        'operating Cv': cv_operating,
                        'percent open': fraction_open * 100,
                        'valve dP (psi)': valve_dp,
                    }
                }
            })
        elif segment_type == "Orifice / Nozzle / Venturi":
            upstream_nps = (st.session_state.segments[-1]['outlet_nps']
                            if st.session_state.segments else 4.0)
            kind = "Restriction Orifice" if is_ro else "Flow Meter"
            st.session_state.segments.append({
                'type': f"{kind} - β {dp_res['beta']:.3f}, bore {bore_in:.3f} in",
                'flow_gpm': inherited_flow,
                'inlet_pressure': inherited_pressure,
                'outlet_pressure': dp_outlet_psia,
                'velocity_fps': 0.0,
                'reynolds': 0,
                'friction_factor': 0.0,
                'head_loss_ft': dp_res['perm_loss_psi'] * 144 / st.session_state.density,
                'inlet_nps': upstream_nps,
                'outlet_nps': upstream_nps,
                'warnings': dp_warnings,
                'details': {
                    'inputs': {
                        'device': device_label,
                        'taps': taps if taps else 'n/a',
                        'purpose': purpose,
                        'line ID (in)': line_id_in,
                        'bore (in)': bore_in,
                        'beta': dp_res['beta'],
                        'discharge coefficient C': dp_res['C'],
                        'tap differential (psi)': dp_res['tap_dp_psi'],
                        'permanent loss (psi)': dp_res['perm_loss_psi'],
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