# Absolute roughness values in inches, by pipe material
# Could be a handy reference for future users.
PIPE_ROUGHNESS_INCH = {
    "steel_welded_seamless":      0.002,
    "steel_sheet_metal_new":      0.0016,
    "steel_commercial_new":       0.0015,
    "steel_riveted":              0.1,
    "steel_rusted":               0.07,
    "stainless_steel":            0.00007,
    "ductile_iron":               0.002,
    "iron_cast_new":              0.0085,
    "iron_wrought_new":           0.0015,
    "iron_galvanized_new":        0.005,
    "iron_asphalted_cast":        0.004,
    "ductile_iron_asphalt_coated":0.004,
    "copper_brass":               0.02,
    "brass_new":                  0.00007,
    "glass":                      0.00005,
    "thermoplastic":              0.00005,
    "drawn_tubing":               0.00005,
    "concrete_smoothed":          0.0013,
    "concrete_rough":             0.07,
    "rubber_smoothed":            0.00033,
    "wood_stave":                 0.016
}

# BWG (Birmingham Wire Gauge) wall thickness reference table
# Values in inches. Common process/heat exchanger tubing range: BWG 8 to BWG 22
BWG_WALL_THICKNESS_INCH = {
    8:  0.165,
    9:  0.148,
    10: 0.134,
    11: 0.120,
    12: 0.109,
    13: 0.095,
    14: 0.083,
    15: 0.072,
    16: 0.065,
    17: 0.058,
    18: 0.049,
    19: 0.042,
    20: 0.035,
    21: 0.032,
    22: 0.028
}

# Fitting K values for the 2-K method (Hooper, 1981)
# K_fitting = (K1/Reynolds) + K_inf*(1 + (1/NPS_inch))
# Source: Perry's Chemical Engineers' Handbook
FITTING_K_VALUES = {
    # Elbows - 90 degree
    'elbow_90_std_threaded':          {'K1': 800,  'Kinf': 0.40},
    'elbow_90_std_flanged_welded':    {'K1': 800,  'Kinf': 0.25},
    'elbow_90_long_radius':           {'K1': 800,  'Kinf': 0.20},
    'elbow_90_mitered':               {'K1': 1000, 'Kinf': 1.15},
    # Elbows - 45 degree
    'elbow_45_std_threaded':          {'K1': 500,  'Kinf': 0.20},
    'elbow_45_long_radius':           {'K1': 500,  'Kinf': 0.15},
    'elbow_45_mitered':               {'K1': 500,  'Kinf': 0.25},
    # Elbows - 180 degree
    'elbow_180_std_threaded':         {'K1': 1000, 'Kinf': 0.70},
    'elbow_180_std_flanged_welded':   {'K1': 1000, 'Kinf': 0.35},
    'elbow_180_long_radius':          {'K1': 1000, 'Kinf': 0.30},
    # Tees - used as elbows
    'tee_elbow_std_threaded':         {'K1': 500,  'Kinf': 0.70},
    'tee_elbow_long_radius_threaded': {'K1': 800,  'Kinf': 0.40},
    'tee_elbow_std_flanged_welded':   {'K1': 800,  'Kinf': 0.80},
    'tee_elbow_stub_in_branch':       {'K1': 1000, 'Kinf': 1.00},
    # Tees - run-through
    'tee_run_threaded':               {'K1': 200,  'Kinf': 0.10},
    'tee_run_flanged_welded':         {'K1': 150,  'Kinf': 0.50},
    'tee_run_stub_in_branch':         {'K1': 100,  'Kinf': 0.05},
    # Valves - gate, ball, plug
    'valve_gate_full_bore':           {'K1': 300,  'Kinf': 0.10},
    'valve_gate_reduced_09':          {'K1': 500,  'Kinf': 0.15},
    'valve_gate_reduced_08':          {'K1': 1000, 'Kinf': 0.25},
    # Valves - globe
    'valve_globe_std':                {'K1': 1500, 'Kinf': 4.00},
    'valve_globe_angle_y':            {'K1': 1000, 'Kinf': 2.00},
    # Valves - other
    'valve_diaphragm_full_open':      {'K1': 1000, 'Kinf': 2.00},
    'valve_butterfly_full_open':      {'K1': 800,  'Kinf': 0.25},
    # Valves - check
    'valve_check_lift':               {'K1': 2000, 'Kinf': 10.00},
    'valve_check_swing':              {'K1': 1500, 'Kinf': 1.50},
    'valve_check_tilting_disk':       {'K1': 1000, 'Kinf': 0.50},
}

FITTING_DISPLAY_NAMES = {
    'elbow_90_std_threaded':            '90° Elbow - Standard (r/d=1), Threaded',
    'elbow_90_std_flanged_welded':      '90° Elbow - Standard (r/d=1), Flanged/Welded',
    'elbow_90_long_radius':             '90° Elbow - Long Radius (r/d=1.5)',
    'elbow_90_mitered':                 '90° Elbow - Mitered',
    'elbow_45_std_threaded':            '45° Elbow - Standard, Threaded',
    'elbow_45_long_radius':             '45° Elbow - Long Radius',
    'elbow_45_mitered':                 '45° Elbow - Mitered',
    'elbow_180_std_threaded':           '180° Return - Standard, Threaded',
    'elbow_180_std_flanged_welded':     '180° Return - Standard, Flanged/Welded',
    'elbow_180_long_radius':            '180° Return - Long Radius',
    'tee_elbow_std_threaded':           'Tee - Branch Flow, Standard Threaded',
    'tee_elbow_long_radius_threaded':   'Tee - Branch Flow, Long Radius Threaded',
    'tee_elbow_std_flanged_welded':     'Tee - Branch Flow, Flanged/Welded',
    'tee_elbow_stub_in_branch':         'Tee - Branch Flow, Stub-In',
    'tee_run_threaded':                 'Tee - Run Through, Threaded',
    'tee_run_flanged_welded':           'Tee - Run Through, Flanged/Welded',
    'tee_run_stub_in_branch':           'Tee - Run Through, Stub-In',
    'valve_gate_full_bore':             'Gate/Ball/Plug Valve - Full Bore',
    'valve_gate_reduced_09':            'Gate/Ball/Plug Valve - Reduced Trim (β=0.9)',
    'valve_gate_reduced_08':            'Gate/Ball/Plug Valve - Reduced Trim (β=0.8)',
    'valve_globe_std':                  'Globe Valve - Standard',
    'valve_globe_angle_y':              'Globe Valve - Angle or Y-Type',
    'valve_diaphragm_full_open':        'Diaphragm Valve - Full Open',
    'valve_butterfly_full_open':        'Butterfly Valve - Full Open',
    'valve_check_lift':                 'Check Valve - Lift',
    'valve_check_swing':                'Check Valve - Swing',
    'valve_check_tilting_disk':         'Check Valve - Tilting Disk'
}

# These fittings are handled internally by calc_flow_split and calc_flow_merge
# and are excluded from the UI fitting selector to avoid double-counting.
# TODO: Revisit tee handling consistency between UI segment types and FITTING_K_VALUES.
# Currently tee K values are retained in FITTING_K_VALUES for internal calculation use
# by calc_flow_split and calc_flow_merge, but hidden from the user-facing UI.
FITTINGS_EXCLUDED_FROM_UI = [
    'tee_elbow_std_threaded',
    'tee_elbow_long_radius_threaded',
    'tee_elbow_std_flanged_welded',
    'tee_elbow_stub_in_branch',
    'tee_run_threaded',
    'tee_run_flanged_welded',
    'tee_run_stub_in_branch'
]

# TODO: Implement entrance loss coefficients in UI
# Sharp-edged entrance: K = 0.5
# Slightly rounded entrance: K = 0.23
# Well-rounded entrance: K = 0.04
# Beveled entrance: K = 0.25
# Projecting (Borda) entrance: K = 0.8
# Source: Crane TP-410
ENTRANCE_K_VALUES = {
    'entrance_sharp_edged':     0.50,
    'entrance_slightly_rounded': 0.23,
    'entrance_well_rounded':    0.04,
    'entrance_beveled':         0.25,
    'entrance_projecting':      0.80
}

# Exit loss coefficient
# All exits: K = 1.0 (all kinetic energy is lost)
EXIT_K_VALUES = {
    'exit_all_types': 1.00
}

# Typical FL at full travel. Where the table gave a range, the LOW end is used,
# which gives a lower choked dP and so a more conservative warning.
# For design, use ANSI/ISA-75.01.01 or the vendor datasheet.
VALVE_FL_DEFAULTS = {
    'Globe, single-port, contoured plug, flow-to-open':        0.90,
    'Globe, single-port, contoured plug, flow-to-close':       0.80,
    'Globe, single-port, V-port plug or drilled-hole cage':    0.90,
    'Globe, angle, contoured plug, flow-to-open':              0.85,
    'Globe, angle, contoured plug, flow-to-close (venturi)':   0.45,
    'Ball, full bore (70° open)':                              0.74,
    'Ball, segmented / V-notch':                               0.60,
    'Butterfly, swing-through (60° open)':                     0.70,
    'Butterfly, swing-through (70° open)':                     0.62,
    'Butterfly, high-performance eccentric (70°)':             0.67,
    'Other / vendor data':                                     0.90,
}

VALVE_CHARACTERISTICS = {
    'Linear': 'linear',
    'Equal percentage': 'equal_percentage',
    'Quick opening (approximate)': 'quick_opening',
}

# Differential-pressure devices. 'meter_type' strings are the `fluids` library's.
# Validity limits: my recollection of ISO 5167 scope limits; verify against the standard.
DP_DEVICES = {
    'Orifice, concentric square-edged (ISO 5167)': {
        'meter_type': 'ISO 5167 orifice',
        'taps': {'Flange taps': 'flange', 'Corner taps': 'corner', 'D and D/2 taps': 'D'},
        'limits': {'D_mm': (50, 1000), 'beta': (0.1, 0.75),
                   're_min': lambda b: 5000 if b <= 0.56 else 16000 * b * b, 're_max': None},
    },
    'Orifice, eccentric (ISO 15377)': {
        'meter_type': 'ISO 15377 eccentric orifice',
        'taps': {'Flange taps': 'flange', 'Corner taps': 'corner', 'D and D/2 taps': 'D'},
        'limits': None,
    },
    'Orifice, quarter-circle (ISO 15377)': {
        'meter_type': 'ISO 15377 quarter-circle orifice', 'taps': None, 'limits': None,
    },
    'Nozzle, ISA 1932': {
        'meter_type': 'ISA 1932 nozzle', 'taps': None,
        'limits': {'D_mm': (50, 500), 'beta': (0.3, 0.8),
                   're_min': lambda b: 7e4 if b < 0.44 else 2e4,
                   're_max': lambda b: 1e7 if b < 0.44 else 2e6},
    },
    'Nozzle, long radius': {
        'meter_type': 'long radius nozzle', 'taps': None,
        'limits': {'D_mm': (50, 630), 'beta': (0.2, 0.8),
                   're_min': lambda b: 1e4, 're_max': lambda b: 1e7},
    },
    'Venturi tube, as-cast convergent': {
        'meter_type': 'as cast convergent venturi tube', 'taps': None,
        'limits': {'D_mm': (100, 800), 'beta': (0.3, 0.75),
                   're_min': lambda b: 2e5, 're_max': lambda b: 2e6},
    },
    'Venturi tube, machined convergent': {
        'meter_type': 'machined convergent venturi tube', 'taps': None,
        'limits': {'D_mm': (50, 250), 'beta': (0.4, 0.75),
                   're_min': lambda b: 2e5, 're_max': lambda b: 1e6},
    },
    'Venturi tube, rough-welded convergent': {
        'meter_type': 'rough welded convergent venturi tube', 'taps': None,
        'limits': {'D_mm': (200, 1200), 'beta': (0.4, 0.7),
                   're_min': lambda b: 2e5, 're_max': lambda b: 2e6},
    },
}