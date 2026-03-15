"""
This is the same as test_problem_002, but it adds a converging tee at the end.
"""
"""
"Water flows through an 8-in steel pipe at an average velocity of 6 feet per second.
Downstream, the pipe divides into an 8 inch main and a 2 inch bypass.
The equivalent length of the bypass is 22 feet; the length of the 8-inch pipe in the bypassed section is 16 feet.

New: The flows re-combine into another 8-inch pipe of the same specs before the bypass.
Do the manual and function call solutions match?

"""

from scipy.optimize import fsolve
from pipe_hydraulics import calc_pipe_segment_p2_psia, calc_flow_split, calc_flow_merge

#First, let's solve for the upstream pipe volumetric flow.  No need to make this hard, just hardcode the number.
# Upstream 8-inch Sch 40 pipe, ID = 7.981 inches, velocity = 6 fps
# Q = V * A = 6 * (pi/4) * (7.981/12)^2 = 2.08 ft3/s = 935.6 GPM
total_flow_gpm = 935.6

#Assume the 2-inch bypass is standard and the water properties are also typical around 60F.
bypass_id_inch = 2.067
water_density_lb_ft3 = 62.4
water_visc_cp = 1.2

def pressure_balance(q_bypass_guess):
    q_main = total_flow_gpm - q_bypass_guess[0]
    result_main = calc_pipe_segment_p2_psia(q_main, 100, 8, '40','steel_commercial_new',water_density_lb_ft3,0,0,16,{},water_visc_cp)
    result_bypass = calc_pipe_segment_p2_psia(q_bypass_guess[0], 100, 2, '40','steel_commercial_new',water_density_lb_ft3,0,0,22,{},water_visc_cp)
    return result_main['outputs']['outlet pressure (psia)'] - result_bypass['outputs']['outlet pressure (psia)']

solution = fsolve(pressure_balance, x0=[50])  # initial guess of 50 GPM through bypass
q_bypass = solution[0]
q_main = total_flow_gpm - q_bypass

# Now get full results with solved flows
result_main = calc_pipe_segment_p2_psia(q_main, 100, 8, '40',
                'steel_commercial_new', water_density_lb_ft3,
                0, 0, 16, {}, water_visc_cp)

result_bypass = calc_pipe_segment_p2_psia(q_bypass, 100, 2, '40',
                'steel_commercial_new', water_density_lb_ft3,
                0, 0, 22, {}, water_visc_cp)

print("result_main:")
print(result_main)
print("result_bypass:")
print(result_bypass)
# Verify pressure balance
print("\n")
print(f"Pressure discrepancy: {result_main['outputs']['outlet pressure (psia)'] - result_bypass['outputs']['outlet pressure (psia)']:.4f} psi")
print("\n")

result_merge = calc_pipe_segment_p2_psia(result_main['inputs']['flow (gpm)']+result_bypass['inputs']['flow (gpm)'],result_main['outputs']['outlet pressure (psia)'],8,'40','steel_commercial_new',62.4,0,0,10,{},1.2)
print("manual merge_test results:")
print(result_merge)

'''
Does calc_flow_split create the same result?
'''

branch_a = {
    'nps': 8,
    'schedule': '40',
    'material': 'steel_commercial_new',
    'length': 16,
    'fittings': {},
    'elev1': 0,
    'elev2': 0
}

branch_b = {
    'nps': 2,
    'schedule': '40',
    'material': 'steel_commercial_new',
    'length': 22,
    'fittings': {},
    'elev1': 0,
    'elev2': 0
}

test = calc_flow_split(total_flow_gpm,100,water_density_lb_ft3,water_visc_cp,branch_a,branch_b,20,False)
merge_test = calc_flow_merge(test['run-through'],test['branch'],8,'40','steel_commercial_new',10,{},0,0,1.2, False)
print("merge_test:")
print(merge_test)

print("ratio of results: manual calc/calc_flow_merge")
print("flow ratio:" + str(result_merge['inputs']['flow (gpm)']/merge_test['merged_stream']['inputs']['flow (gpm)']))
print("outlet pressure ratio:" + str(result_merge['outputs']['outlet pressure (psia)']/merge_test['merged_stream']['outputs']['outlet pressure (psia)']))
#If both are 1.o, things are good.
