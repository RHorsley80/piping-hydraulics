#Use this to calculate pipe hydraulics.
#Functions follow the standard hydraulic workflow:
# Velocity → Reynolds → Friction Factor → Head Loss → Bernoulli

import math
from scipy.optimize import fsolve
from reference_datatables import PIPE_ROUGHNESS_INCH, BWG_WALL_THICKNESS_INCH, FITTING_K_VALUES
from fluids.piping import nearest_pipe, t_from_gauge


def calc_piping_velocity_fps(flow_rate_cfs, pipe_diam_inch):
    #Start with error handling for invalid inputs:
    if pipe_diam_inch <= 0:
        raise ValueError("Pipe diameter must be a positive number")
    if flow_rate_cfs < 0:
        raise ValueError("Flow rate cannot be negative or zero")
    #Get cross-sectional area in square feet
    pipe_area_ft2 = (math.pi/4)*((pipe_diam_inch/12)**2)
    #calculate piping velocity in fps
    velocity_fps = flow_rate_cfs/pipe_area_ft2
    return velocity_fps

def calc_reynolds_number(pipe_diam_inch, velocity_fps, density_lb_ft3, visc_cp):
    #Start by controlling for incorrect inputs.
    if pipe_diam_inch <= 0:
        raise ValueError("Pipe diameter must be a positive number")
    if velocity_fps <= 0:
        raise ValueError("Flow rate cannot be negative or zero")
    if density_lb_ft3 <= 0:
        raise ValueError("Density must be a positive number")
    if visc_cp <= 0:
        raise ValueError("Viscosity must be greater than zero")
    #Convert pipe diameter from inches to feet
    pipe_diam_ft = pipe_diam_inch/12
    # Convert dynamic viscosity from cP to lbm/(ft·s): 1 cP = 1/1488.16 lbm/(ft·s)
    visc_lb_ft_s = visc_cp/1488.1639
    #Now, calculate Reynolds Number
    reynolds = (pipe_diam_ft*velocity_fps*density_lb_ft3)/(visc_lb_ft_s)
    return reynolds

def get_pipe_roughness_inch(material="steel_commercial_new"):
    # Returns absolute roughness in inches for the specified pipe material.
    # Defaults to commercial steel if no material is specified.
    if material not in PIPE_ROUGHNESS_INCH:
        raise ValueError(f"Material '{material}' not found. Available materials: {list(PIPE_ROUGHNESS_INCH.keys())}")
    return PIPE_ROUGHNESS_INCH[material]

def get_pipe_id_inch(nps_inch, schedule='40'):
    # Returns pipe inner diameter in inches for a given nominal pipe size and schedule.
    # Uses fluids library (ASME B36.10/B36.19). Dimensions converted from meters to inches.
    meters_to_inch = 39.3701
    NPS, ID_m, OD_m, wall_m = nearest_pipe(NPS=nps_inch, schedule=schedule)
    return ID_m * meters_to_inch

def get_tubing_id_inch(od_inch, bwg_gauge):
    # Returns tubing inner diameter in inches for a given OD and BWG gauge.
    # Wall thickness looked up from BWG standard via fluids library.
    # ID = OD - 2 * wall thickness
    wall_m = t_from_gauge(bwg_gauge, schedule='BWG')
    wall_inch = wall_m * 39.3701
    id_inch = od_inch - (2 * wall_inch)
    if id_inch <= 0:
        raise ValueError(f"BWG {bwg_gauge} wall thickness exceeds tubing OD of {od_inch} inches")
    return id_inch

def get_bwg_wall_thickness_inch(bwg_gauge):
    # Returns wall thickness in inches for a given BWG gauge number.
    # Lower gauge number = thicker wall.
    if bwg_gauge not in BWG_WALL_THICKNESS_INCH:
        raise ValueError(f"BWG gauge {bwg_gauge} not in table. Available gauges: {list(BWG_WALL_THICKNESS_INCH.keys())}")
    return BWG_WALL_THICKNESS_INCH[bwg_gauge]

def calc_friction_factor(reynolds, epsilon_inch, pipe_diam_inch):
    #Start by controlling for incorrect inputs.
    if reynolds <= 0:
        raise ValueError("Reynolds number must be positive")
    if epsilon_inch < 0:
        raise  ValueError("Piping absolute roughness (epsilon) must not be negative")
    if pipe_diam_inch <= 0:
        raise ValueError("Pipe diameter must be positive")
    if 2300 < reynolds < 4000:
        print("Warning: Reynolds number is in the transitional flow regime. Results are inherently uncertain.")
    #Use Churchill(1977) to cover the span of flow regimes from laminar through transitional to turbulent
    #Calculate in three parts: churchill_a, churchill_b, and finally churchill_f
    churchill_a = (2.457*(math.log(((7/reynolds)**0.9 + 0.27*(epsilon_inch/pipe_diam_inch))**-1)))**16
    #Calculate churchill_b
    churchill_b = (37530/reynolds)**16
    #calculate churchill_f
    churchill_f = 8*((((8/reynolds)**12)+((churchill_a+churchill_b)**-1.5))**(1/12))
    return churchill_f

def calc_fitting_k(fitting_type, reynolds, nps_inch):
    # Calculates K value for a single fitting using the 2-K method.
    # K = (K1/Re) + Kinf*(1 + 1/NPS)
    if fitting_type not in FITTING_K_VALUES:
        raise ValueError(f"Fitting '{fitting_type}' not found. Available fittings: {list(FITTING_K_VALUES.keys())}")
    if reynolds <= 0:
        raise ValueError("Reynolds number must be positive")
    if nps_inch <= 0:
        raise ValueError("NPS must be positive")
    k1   = FITTING_K_VALUES[fitting_type]['K1']
    kinf = FITTING_K_VALUES[fitting_type]['Kinf']
    return (k1 / reynolds) + kinf * (1 + (1 / nps_inch))

def calc_total_fitting_k(fitting_counts, reynolds, nps_inch):
    # Calculates total K for multiple fittings on a pipe segment.
    # fitting_counts: dict of {fitting_type: quantity}, e.g. {'elbow_90_std_flanged_welded': 3, 'valve_gate_full_bore': 1}
    total_k = 0.0
    for fitting_type, quantity in fitting_counts.items():
        total_k += calc_fitting_k(fitting_type, reynolds, nps_inch) * quantity
    return total_k

def calc_headloss_ft(friction_factor, length_ft, pipe_diam_inch, fitting_k, velocity_fps):
    #Start by controlling for incorrect inputs
    if friction_factor < 0:
        raise ValueError("friction factor must not be negative")
    if length_ft<= 0:
        raise ValueError("The pipe length must be positive")
    if pipe_diam_inch <= 0:
        raise  ValueError("The pipe diameter must be positive")
    if velocity_fps <= 0:
        raise ValueError("The flow velocity must be positive")
    #Calculate headloss
    g_ft_s2 = 32.174  # gravitational acceleration, ft/s²
    hl_ft = (friction_factor*(length_ft/(pipe_diam_inch/12))+fitting_k)*((velocity_fps**2)/(2*g_ft_s2))
    return  hl_ft

def calc_pipe_diameter_change_k(inlet_diam_inch, outlet_diam_inch, angle_degrees=45):
    if inlet_diam_inch <= 0:
        raise ValueError("Inlet diameter must be positive")
    if outlet_diam_inch <= 0:
        raise ValueError("Outlet diameter must be positive")
    if inlet_diam_inch == outlet_diam_inch:
        raise ValueError("No diameter change has been specified.")
    if angle_degrees <= 0 or angle_degrees >= 180:
        raise ValueError("The angle must be between 0 and 180 degrees.  45 degrees is the default value.")
    #Pass inputs to enlarger/reducer calculations, as appropriate
    if inlet_diam_inch > outlet_diam_inch:
        return calc_reducer_fitting_k(inlet_diam_inch, outlet_diam_inch, angle_degrees)
    else:
        return calc_enlarger_fitting_k(inlet_diam_inch, outlet_diam_inch, angle_degrees)

def transition_dp(density_lb_ft3,transition_k,inlet_velocity_fps):
    if density_lb_ft3 <= 0:
        raise ValueError("The density must be a positive number")
    if inlet_velocity_fps < 0:
        raise ValueError("Inlet velocity must be positive")
    g_ft_s2 = 32.174  # gravitational acceleration, ft/s²
    in2_per_ft2 = 144  # converts lb/ft² to psi
    return (density_lb_ft3/in2_per_ft2)* transition_k *(inlet_velocity_fps ** 2)/(2 * g_ft_s2)

def calc_enlarger_fitting_k(inlet_diam_inch, outlet_diam_inch, expansion_angle_degrees=45):
    #45-degrees is taken as a default value.
    #K-values are based on velocity of the larger pipe.  From Crane Technical Paper 410, 2-11
    if inlet_diam_inch <= 0:
        raise ValueError("The inlet pipe diameter must be greater than zero")
    if outlet_diam_inch <= 0:
        raise ValueError("The outlet pipe diameter must be greater than zero")
    if inlet_diam_inch >= outlet_diam_inch:
        raise ValueError("The outlet diameter must be greater than the inlet diameter")
    if expansion_angle_degrees <= 0 or expansion_angle_degrees >= 180:
        raise ValueError("The expansion angle must be between 0 and 180 degrees.")
    #Now, do the calculations.
    beta = outlet_diam_inch/inlet_diam_inch
    if expansion_angle_degrees <= 45:
        enlarger_k = (2.6 * math.sin(math.radians(expansion_angle_degrees / 2))*(1-beta**2)**2)/(beta**4)
    else:
        enlarger_k = ((1-beta**2)**2)/(beta**4)
    return enlarger_k

def calc_reducer_fitting_k(inlet_diam_inch, outlet_diam_inch, contraction_angle_degrees=45):
    #45-degrees is taken as a default value.
    #K-values are based on velocity of the larger pipe.  From Crane Technical Paper 410, 2-11
    if inlet_diam_inch <= 0:
        raise ValueError("The inlet pipe diameter must be greater than zero")
    if outlet_diam_inch <= 0:
        raise ValueError("The outlet pipe diameter must be greater than zero")
    if inlet_diam_inch <= outlet_diam_inch:
        raise ValueError("The inlet diameter must be greater than the outlet diameter")
    if contraction_angle_degrees <= 0 or contraction_angle_degrees >= 180:
        raise ValueError("The contraction angle must be between 0 and 180 degrees.")
    beta = outlet_diam_inch/inlet_diam_inch
    if contraction_angle_degrees <= 45:
        reducer_k = (0.8* math.sin(math.radians(contraction_angle_degrees / 2))*(1-beta**2))/(beta**4)
    else:
        reducer_k = 0.5*(math.sin(math.radians(contraction_angle_degrees / 2))**0.5)*(1-beta**2)/(beta**4)
    return reducer_k

# TODO: Convert the bernoulli function to an optional arguments function, such that any variable can be solved for.
def calc_bernoulli_p2_psia(press1_psia, vel1_fps, vel2_fps, density_lb_ft3, elev1_ft, elev2_ft, headloss_ft):
    #Start by controlling for incorrect inputs
    if vel1_fps <0:
        raise ValueError("inlet velocity must be positive")
    if vel2_fps < 0:
        raise ValueError("Outlet velocity must be positive")
    if density_lb_ft3 <= 0:
        raise ValueError("All densities must be positive")
    #Simplify the equation by calculating the pressure and velocity heads separately.
    g_ft_s2 = 32.174  # gravitational acceleration, ft/s²
    in2_to_ft2 = (1/144) # converts lb/ft² to psi (lb/in²)
    velocity_head = (((vel1_fps**2)-(vel2_fps**2))/(2*g_ft_s2)) * density_lb_ft3 * in2_to_ft2
    elev_head = density_lb_ft3 * (elev2_ft - elev1_ft) * in2_to_ft2
    press2_psia = press1_psia+velocity_head-elev_head-(headloss_ft * (density_lb_ft3 * in2_to_ft2))
    return  press2_psia

def calc_pipe_segment_p2_psia(flow_gpm, press1_psia, nps_inch, schedule, material, density_lb_ft3, elev1_ft, elev2_ft, pipe_length_ft, fitting_counts, visc_cp):
    #Start by controlling for incorrect inputs
    if flow_gpm <= 0:
        raise ValueError("Flow must be positive")
    if press1_psia <= 0:
        raise ValueError("The absolute inlet pressure must be positive")
    if nps_inch <= 0:
        raise ValueError("The pipe diameter must be positive")
    if not schedule:
        raise ValueError("A pipe schedule needs to be specified.")
    if density_lb_ft3 <= 0:
        raise ValueError("The density must be positive")
    if pipe_length_ft <= 0:
        raise ValueError("The pipe length must be positive")
    if visc_cp<=0:
        raise ValueError("The fluid viscosity must be positive")
    if not isinstance(fitting_counts, dict):
        raise ValueError("fitting_counts must be a dictionary, e.g. {} for no fittings or {'elbow_90_long_radius': 2} for fittings")
    #First, we need the actual non-nominal pipe diameter
    pipe_id_inch = get_pipe_id_inch(nps_inch, schedule)
    #Convert the flow to ft3/s at the inlet.  An enlarger or reducer when used will be the beginning of a new pipe segment.
    gal_per_cf = 7.4805 #7.4805 gallons per cubic foot
    sec_per_min = 60 #60 seconds per minute.
    flow_cfs = flow_gpm*(1/gal_per_cf)*(1/sec_per_min)
    velocity_fps = calc_piping_velocity_fps(flow_cfs, pipe_id_inch)
    #Find the reynolds number at the inlet and outlet.
    reynolds = calc_reynolds_number(pipe_id_inch, velocity_fps, density_lb_ft3, visc_cp)
    #Get absolute roughness
    epsilon_in = get_pipe_roughness_inch(material)
    #Calculate friction factor
    ff = calc_friction_factor(reynolds, epsilon_in, pipe_id_inch)
    #Calculate K for fittings
    fitting_k = calc_total_fitting_k(fitting_counts,reynolds,pipe_id_inch)
    #Calculate Head Loss
    h_l = calc_headloss_ft(ff, pipe_length_ft, pipe_id_inch, fitting_k, velocity_fps)
    #Bernoulli calculation for P2
    #As mentioned above, we will assume that a pipe segment is of constant diameter.  An enlarger or reducer will signify a new pipe segment.
    press2_psia = calc_bernoulli_p2_psia(press1_psia,velocity_fps,velocity_fps,density_lb_ft3,elev1_ft,elev2_ft,h_l)
    #Flag outlet pressure being below absolute pressure as an error if it happens.
    if press2_psia < 0:
        raise ValueError(f"Outlet pressure ({press2_psia:.2f} psia) is below absolute zero - check inputs.")

    pipe_segment_data = {
        "inputs": {
            "flow (gpm)":flow_gpm,
            "inlet pressure (psia)": press1_psia,
            "pipe nps (inch)": nps_inch,
            "pipe schedule": schedule,
            "pipe material": material,
            "fluid density (lb/ft3)": density_lb_ft3,
            "inlet elevation (ft)": elev1_ft,
            "outlet elevation (ft)": elev2_ft,
            "pipe length (ft)": pipe_length_ft,
            "fitting counts": fitting_counts,
            "viscosity (cp)": visc_cp
        },
        "outputs":{
        "actual pipe diam (inch)": pipe_id_inch,
        "fluid velocity (fps)": velocity_fps,
        "reynolds number": reynolds,
        "fitting K": fitting_k,
        "friction factor": ff,
        "head loss (ft)": h_l,
        "outlet pressure (psia)": press2_psia
        }
    }
    return pipe_segment_data


#TODO: This will treat all divergences, wyes and tees, as tees with a straight run-through leg and a branch-leg.
# Crane 410, on 2-16, shows that a 90-degree tee produces a K that is equal or higher than lesser degrees.
# This provides a conservative result and should be fine for all but the most detailed work.
def calc_flow_split(
            total_flow_gpm,
            press1_psia,
            density_lb_ft3,
            visc_cp,
            branch_a_params,
            branch_b_params,
            initial_guess_gpm=None,
            add_tee_fittings=True,  # set False when equivalent lengths already include fitting losses
            runthru_tee_type='tee_run_flanged_welded',
            branch_tee_type='tee_elbow_std_flanged_welded'
    ):

    # Initial guess defaults to 50% of total_flow_gpm
    if initial_guess_gpm is None:
        initial_guess_gpm = total_flow_gpm/2

    #Define flow split for two pipes: the run-through and the branch.
    def pressure_balance(q_branch_guess):
        q_runthru = total_flow_gpm - q_branch_guess[0]
        result_a = calc_pipe_segment_p2_psia(q_runthru, press1_psia,
                                             branch_a_params['nps'], branch_a_params['schedule'],
                                             branch_a_params['material'], density_lb_ft3,
                                             branch_a_params['elev1'], branch_a_params['elev2'],
                                             branch_a_params['length'], ({**branch_a_params['fittings'], runthru_tee_type: 1}
                    if add_tee_fittings
                    else branch_a_params['fittings']), visc_cp)
        result_b = calc_pipe_segment_p2_psia(q_branch_guess[0], press1_psia,
                                             branch_b_params['nps'], branch_b_params['schedule'],
                                             branch_b_params['material'], density_lb_ft3,
                                             branch_b_params['elev1'], branch_b_params['elev2'],
                                             branch_b_params['length'], ({**branch_b_params['fittings'], branch_tee_type: 1}
                   if add_tee_fittings
                   else branch_b_params['fittings']), visc_cp)
        return result_a['outputs']['outlet pressure (psia)'] - result_b['outputs']['outlet pressure (psia)']

    branch_flow = fsolve(pressure_balance, x0=[initial_guess_gpm])[0]
    runthru_flow = total_flow_gpm - branch_flow

    final_runthru = calc_pipe_segment_p2_psia(runthru_flow, press1_psia,
                                              branch_a_params['nps'], branch_a_params['schedule'],
                                              branch_a_params['material'], density_lb_ft3,
                                              branch_a_params['elev1'], branch_a_params['elev2'],
                                              branch_a_params['length'], ({**branch_a_params['fittings'], runthru_tee_type: 1}
                                                if add_tee_fittings
                                                else branch_a_params['fittings']), visc_cp)

    final_branch = calc_pipe_segment_p2_psia(branch_flow, press1_psia,
                                             branch_b_params['nps'], branch_b_params['schedule'],
                                             branch_b_params['material'], density_lb_ft3,
                                             branch_b_params['elev1'], branch_b_params['elev2'],
                                             branch_b_params['length'], ({**branch_b_params['fittings'], branch_tee_type: 1}
                                            if add_tee_fittings
                                            else branch_b_params['fittings']), visc_cp)

    flow_split_results = {
        'run-through': final_runthru,
        'branch': final_branch,
        'flow split': {
            'run-through flow (gpm)': runthru_flow,
            'branch flow (gpm)': branch_flow,
            'run-through fraction': runthru_flow / total_flow_gpm,
            'branch fraction': branch_flow / total_flow_gpm
        }
    }

    return flow_split_results

def calc_flow_merge(
    stream_a_result,  # full result dict from calc_pipe_segment_p2_psia
    stream_b_result,  # full result dict from calc_pipe_segment_p2_psia
    outlet_nps,
    outlet_schedule,
    outlet_material,
    outlet_length_ft,
    outlet_fittings,
    outlet_elev1_ft,
    outlet_elev2_ft,
    visc_cp,
    add_tee_fittings = True,  # set False when equivalent lengths already include fitting losses
    runthru_tee_type = 'tee_run_flanged_welded',
    ):

    # Calculate the total flow rate
    total_flow_gpm = stream_a_result['inputs']['flow (gpm)']+stream_b_result['inputs']['flow (gpm)']
    # The network solver iterates the upstream flows until the merging stream pressures are equal.
    inlet_pressure_delta_psid = stream_a_result['outputs']['outlet pressure (psia)'] - stream_b_result['outputs'][
        'outlet pressure (psia)']
    #Once the pressures are equal, accept either one.  It doesn't matter.
    merge_input_pressure_psia = stream_a_result['outputs']['outlet pressure (psia)']
    #TODO: if non-isothermal or vapor systems are included, expect to change the density calc below.
    merge_density = stream_a_result['inputs']['fluid density (lb/ft3)']
    #Fittings logic
    merge_fittings = ({**outlet_fittings, runthru_tee_type: 1}
                      if add_tee_fittings
                      else outlet_fittings)
    #Everything else is just a pipe.
    #Crane 410 makes merge calculation way more complex.  Just use a 90-degree T for conservatism.
    merge_hydraulics = calc_pipe_segment_p2_psia(total_flow_gpm,merge_input_pressure_psia,outlet_nps,outlet_schedule,outlet_material,merge_density,outlet_elev1_ft,outlet_elev2_ft,outlet_length_ft,merge_fittings,visc_cp)

    return {
        'merged_stream': merge_hydraulics,
        'merge_diagnostics': {
            'stream_a_inlet_pressure (psia)': stream_a_result['outputs']['outlet pressure (psia)'],
            'stream_b_inlet_pressure (psia)': stream_b_result['outputs']['outlet pressure (psia)'],
            'pressure_discrepancy (psi)': inlet_pressure_delta_psid,
            'stream_a_flow (gpm)': stream_a_result['inputs']['flow (gpm)'],
            'stream_b_flow (gpm)': stream_b_result['inputs']['flow (gpm)'],
            'total_flow (gpm)': total_flow_gpm
        }
    }