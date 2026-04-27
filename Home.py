import math
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from pipe_hydraulics import calc_pipe_segment_p2_psia, transition_dp, calc_pipe_diameter_change_k, get_pipe_id_inch
from reference_datatables import (PIPE_ROUGHNESS_INCH, FITTING_DISPLAY_NAMES, FITTINGS_EXCLUDED_FROM_UI)

st.markdown("""
    <style>
    .fitting-row {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border: 1px solid #444;
        border-radius: 4px;
        margin-bottom: 4px;
        background-color: #1e1e1e;
    }
    .fitting-label {
        flex: 3;
        color: #ffffff;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Pipe Hydraulics Calculator")
st.write("Isothermal liquid flow analysis")

# Initialize session state
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'current_flow_gpm' not in st.session_state:
    st.session_state.current_flow_gpm = 100.0
if 'current_pressure_psia' not in st.session_state:
    st.session_state.current_pressure_psia = 100.0
if 'density' not in st.session_state:
    st.session_state.density = 62.4
if 'visc_cp' not in st.session_state:
    st.session_state.visc_cp = 1.2
if 'inlet_pressure' not in st.session_state:
    st.session_state.inlet_pressure = 100.0
if 'total_flow_gpm' not in st.session_state:
    st.session_state.total_flow_gpm = 100.0

# Fluid properties - entered once, inherited by all segments
st.header("Fluid Properties")
col1, col2, col3 = st.columns(3)
with col1:
    st.session_state.density = st.number_input(
        "Density (lb/ft³)",
        min_value=0.1,
        value=st.session_state.density)
with col2:
    st.session_state.visc_cp = st.number_input(
        "Viscosity (cP)",
        min_value=0.001,
        value=st.session_state.visc_cp)
with col3:
    st.session_state.inlet_pressure = st.number_input(
        "Inlet Pressure (psia)",
        min_value=0.1,
        value=st.session_state.inlet_pressure)

st.header("Inlet Flow")
st.session_state.total_flow_gpm = st.number_input(
    "Total Flow Rate (GPM)",
    min_value=0.1,
    value=st.session_state.total_flow_gpm)
