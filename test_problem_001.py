# 400 GPM of water at 60F is flowing through the following piping system:
# 1.) At 0 ft elevation and unspecified pressure, water flows through 110 ft of 4-inch schedule 40 pipe.
# 2.) A r/d = 1.5 elbow directs flow vertically and an enlarger expands the pipe to 5-inch schedule 40
# and rises 75 feet
# 3.) Another 90-degree r/d=1.5 elbow directs flow horizontally, still 5-inch schedule 40, for 150 feet.
# 4.) Find the Piping DP.  Answer should be around 39 PSID.

#Assume an arbitrary P1 of 100 PSIA.  Solve part 1:

from pipe_hydraulics import calc_pipe_segment_p2_psia, calc_total_fitting_k, calc_pipe_diameter_change_k, transition_dp

pipe01 = calc_pipe_segment_p2_psia(400,100,4,'40','steel_commercial_new',62.4,0,0,110, {},1.2)
print(pipe01)

#Get elbow and transition k-values and solve for pressure change.  Solve part 2.

elbow_k = calc_total_fitting_k({'elbow_90_long_radius': 1},pipe01['outputs']['reynolds number'], 4)
enlarger_k = calc_pipe_diameter_change_k(4.026,5.047,45)
print("elbow_k = " + str(elbow_k))
print("enlarger_k = " + str(enlarger_k))

trans_dp = transition_dp(pipe01['inputs']['fluid density (lb/ft3)'],elbow_k+enlarger_k,pipe01['outputs']['fluid velocity (fps)'])
print("trans_dp = " + str(trans_dp))

press_after_transition = pipe01['outputs']['outlet pressure (psia)']- trans_dp
print("press_after_transition = " + str(press_after_transition))

pipe02 = calc_pipe_segment_p2_psia(400,press_after_transition,5,'40','steel_commercial_new',pipe01['inputs']['fluid density (lb/ft3)'],0,75,75,{},1.2)
print(pipe02)

#Finally, solve for the third pipe.
elbow2_k = calc_total_fitting_k({'elbow_90_long_radius': 1},
                                  pipe02['outputs']['reynolds number'], 5)
elbow2_dp = (pipe02['inputs']['fluid density (lb/ft3)']/144) * elbow2_k * (pipe02['outputs']['fluid velocity (fps)']**2) / (2*32.174)
press_after_elbow2 = pipe02['outputs']['outlet pressure (psia)'] - elbow2_dp

pipe03 = calc_pipe_segment_p2_psia(400, press_after_elbow2, 5, '40', 'steel_commercial_new', 62.4, 75, 75, 150, {}, 1.2)
print(pipe03)

final_answer_dp_psid = pipe01['inputs']['inlet pressure (psia)'] - pipe03['outputs']['outlet pressure (psia)']
print(final_answer_dp_psid)