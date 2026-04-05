import copy
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from maths.state import initialize_env
from maths.step import step_environment
from maths.root_length import compute_total_uptake, compute_root_growth_rate


def ensure_output_dir() -> Path:
    out_dir = Path("plots_maths")
    out_dir.mkdir(exist_ok=True)
    return out_dir


def save_fig(out_dir: Path, name: str):
    plt.tight_layout()
    plt.savefig(out_dir / name, dpi=180)
    plt.close()


def plot_water_constitutive_curves(params: dict, out_dir: Path):
    theta_min = 0.01
    theta_s = params.get("theta_s", 0.45)
    ksat = params.get("Ksat", 1e-5)
    k_w = params.get("k_w", 1e-6)
    K_w = params.get("K_w", 0.2)

    theta = np.linspace(theta_min, theta_s, 250)
    K = ksat * (theta / theta_s) ** 3
    psi = -0.1 * (theta_s / (theta + 1e-8))
    S_w = k_w * (theta / (theta + K_w + 1e-12))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    axes[0].plot(theta, K, color="tab:blue")
    axes[0].set_title("Hydraulic Conductivity K(theta)")
    axes[0].set_xlabel("theta")
    axes[0].set_ylabel("K")
    axes[0].grid(alpha=0.3)

    axes[1].plot(theta, psi, color="tab:orange")
    axes[1].set_title("Water Potential psi(theta)")
    axes[1].set_xlabel("theta")
    axes[1].set_ylabel("psi")
    axes[1].grid(alpha=0.3)

    axes[2].plot(theta, S_w, color="tab:green")
    axes[2].set_title("Root Water Sink Flux Term")
    axes[2].set_xlabel("theta")
    axes[2].set_ylabel("k_w * theta/(theta + K_w)")
    axes[2].grid(alpha=0.3)

    save_fig(out_dir, "01_water_constitutive_curves.png")


def plot_nutrient_uptake_curves(params: dict, out_dir: Path):
    C = np.linspace(0.0, 0.12, 300)

    nutrient_config = {
        "N": (params.get("Imax_N", 1e-6), params.get("Km_N", 0.01), "tab:blue"),
        "P": (params.get("Imax_P", 5e-7), params.get("Km_P", 0.005), "tab:green"),
        "K": (params.get("Imax_K", 8e-7), params.get("Km_K", 0.01), "tab:red"),
    }

    plt.figure(figsize=(7.5, 5.0))
    for nutrient, (imax, km, color) in nutrient_config.items():
        uptake = imax * C / (km + C + 1e-12)
        plt.plot(C, uptake, label=f"{nutrient}: Imax*C/(Km+C)", color=color)

    plt.title("Michaelis-Menten Nutrient Uptake Flux")
    plt.xlabel("C_i at root surface")
    plt.ylabel("Uptake flux")
    plt.legend()
    plt.grid(alpha=0.3)
    save_fig(out_dir, "02_nutrient_uptake_curves.png")


def plot_total_uptake_and_u_eff(state: dict, params: dict, out_dir: Path):
    base_state = copy.deepcopy(state)
    concentration_scale = np.linspace(0.2, 2.0, 120)

    U_N, U_P, U_K, U_eff = [], [], [], []

    for scale in concentration_scale:
        s = copy.deepcopy(base_state)
        s["C_N"] = s["C_N"] * scale
        s["C_P"] = s["C_P"] * scale
        s["C_K"] = s["C_K"] * scale

        uptake = compute_total_uptake(s, params)
        U_N.append(uptake["U_N"])
        U_P.append(uptake["U_P"])
        U_K.append(uptake["U_K"])
        U_eff.append(uptake["U_eff"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))

    axes[0].plot(concentration_scale, U_N, label="U_N", color="tab:blue")
    axes[0].plot(concentration_scale, U_P, label="U_P", color="tab:green")
    axes[0].plot(concentration_scale, U_K, label="U_K", color="tab:red")
    axes[0].set_title("Total Uptake U_i")
    axes[0].set_xlabel("Uniform concentration scale")
    axes[0].set_ylabel("U_i")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(concentration_scale, U_eff, label="U_eff", color="tab:purple")
    axes[1].set_title("Effective Nutrient U_eff")
    axes[1].set_xlabel("Uniform concentration scale")
    axes[1].set_ylabel("U_eff")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    save_fig(out_dir, "03_total_uptake_and_u_eff.png")


def plot_root_growth_terms(state: dict, params: dict, out_dir: Path):
    base_state = copy.deepcopy(state)

    theta_values = np.linspace(0.01, params.get("theta_s", 0.45), 120)
    dL_theta = []
    branch_theta = []

    for theta_val in theta_values:
        s = copy.deepcopy(base_state)
        s["theta"][:] = theta_val
        diag = compute_root_growth_rate(s, params)
        dL_theta.append(diag["dL_dt"])
        branch_theta.append(diag["branching"])

    C_s_values = np.linspace(0.01, 0.5, 120)
    dL_cs = []
    growth_cs = []

    for cs in C_s_values:
        s = copy.deepcopy(base_state)
        s["C_s"] = cs
        diag = compute_root_growth_rate(s, params)
        dL_cs.append(diag["dL_dt"])
        growth_cs.append(diag["growth"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))

    axes[0].plot(theta_values, dL_theta, label="dL/dt", color="tab:blue")
    axes[0].plot(theta_values, branch_theta, label="branching", color="tab:orange")
    axes[0].set_title("Root Dynamics vs Water")
    axes[0].set_xlabel("theta")
    axes[0].set_ylabel("rate")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(C_s_values, dL_cs, label="dL/dt", color="tab:green")
    axes[1].plot(C_s_values, growth_cs, label="growth term", color="tab:red")
    axes[1].set_title("Root Dynamics vs Storage Carbon")
    axes[1].set_xlabel("C_s")
    axes[1].set_ylabel("rate")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    save_fig(out_dir, "04_root_growth_terms.png")


def plot_carbon_and_lai_functions(params: dict, out_dir: Path):
    k_g = params.get("k_g", 0.05)
    r_m = params.get("r_m", 0.01)
    c_r = params.get("c_r", 0.02)
    alpha = params.get("alpha", 0.7)
    delta = params.get("delta", 0.02)
    C_crit = params.get("C_crit", 0.05)
    epsilon = params.get("epsilon", 1e-6)
    c_L = params.get("c_L", 3.0)
    beta = params.get("beta", 0.8)
    light_ext = params.get("light_ext_coeff", 0.5)
    g_max = params.get("g_max", 1.0)
    K_theta = params.get("K_theta", 0.2)
    Vcmax = params.get("Vcmax", 1.0)
    J = params.get("J", 1.0)
    Kc = params.get("Kc", 0.5)

    LAI = np.linspace(0.0, 8.0, 250)
    theta = np.linspace(0.01, 0.45, 250)
    g_s = g_max * theta / (theta + K_theta + 1e-12)
    C_leaf = g_s
    W_c = Vcmax * (C_leaf / (C_leaf + Kc + 1e-12))
    W_j = J * (C_leaf / (4.0 * (C_leaf + Kc + 1e-12)))

    A_low = np.minimum(W_c[40], W_j[40]) * (1 - np.exp(-light_ext * LAI))
    A_mid = np.minimum(W_c[130], W_j[130]) * (1 - np.exp(-light_ext * LAI))
    A_high = np.minimum(W_c[-1], W_j[-1]) * (1 - np.exp(-light_ext * LAI))

    C_s = np.linspace(0.001, 0.5, 250)
    C_p_ref = 0.2
    dC_p_dt = alpha * k_g * C_s - delta * C_p_ref * (C_crit / (C_s + epsilon))

    C_p = np.linspace(0.0, 2.0, 250)
    LAI_cp = c_L * (C_p ** beta)

    C_s_axis = np.linspace(0.001, 0.5, 250)
    dL_ref = 0.01
    A_ref = A_mid.mean()
    dC_s_dt = A_ref - k_g * C_s_axis - r_m * C_p_ref - c_r * dL_ref

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.6))

    axes[0, 0].plot(LAI, A_low, label="A at low water", color="tab:red")
    axes[0, 0].plot(LAI, A_mid, label="A at medium water", color="tab:orange")
    axes[0, 0].plot(LAI, A_high, label="A at high water", color="tab:green")
    axes[0, 0].set_title("Photosynthesis A vs LAI")
    axes[0, 0].set_xlabel("LAI")
    axes[0, 0].set_ylabel("A")
    axes[0, 0].legend()
    axes[0, 0].grid(alpha=0.3)

    axes[0, 1].plot(theta, g_s, label="g_s(theta)", color="tab:blue")
    axes[0, 1].plot(theta, W_c, label="W_c(theta)", color="tab:purple")
    axes[0, 1].plot(theta, W_j, label="W_j(theta)", color="tab:brown")
    axes[0, 1].set_title("Stomatal and Biochemical Coupling")
    axes[0, 1].set_xlabel("theta")
    axes[0, 1].set_ylabel("value")
    axes[0, 1].legend()
    axes[0, 1].grid(alpha=0.3)

    axes[1, 0].plot(C_s, dC_p_dt, color="tab:green")
    axes[1, 0].axhline(0.0, color="black", linewidth=1)
    axes[1, 0].set_title("Structural Carbon Rate dC_p/dt vs C_s")
    axes[1, 0].set_xlabel("C_s")
    axes[1, 0].set_ylabel("dC_p/dt")
    axes[1, 0].grid(alpha=0.3)

    axes[1, 1].plot(C_p, LAI_cp, color="tab:blue", label="LAI(C_p)")
    axes[1, 1].set_title("LAI Function")
    axes[1, 1].set_xlabel("C_p")
    axes[1, 1].set_ylabel("LAI")
    axes[1, 1].legend()
    axes[1, 1].grid(alpha=0.3)

    save_fig(out_dir, "05_carbon_and_lai_functions.png")

    plt.figure(figsize=(7.2, 4.8))
    plt.plot(C_s_axis, dC_s_dt, color="tab:purple")
    plt.axhline(0.0, color="black", linewidth=1)
    plt.title("Storage Carbon Rate dC_s/dt vs C_s (reference cut)")
    plt.xlabel("C_s")
    plt.ylabel("dC_s/dt")
    plt.grid(alpha=0.3)
    save_fig(out_dir, "06_storage_carbon_rate_reference.png")


def run_step_simulation_and_plot(state: dict, params: dict, out_dir: Path):
    action = {
        "theta_boundary": 0.35,
        "C_boundary_N": params.get("C_boundary_N", 0.05),
        "C_boundary_P": params.get("C_boundary_P", 0.02),
        "C_boundary_K": params.get("C_boundary_K", 0.04),
    }

    dt = 0.01
    steps = 250

    records = {
        "C_s": [],
        "C_p": [],
        "L": [],
        "LAI": [],
        "U_eff": [],
        "reward": [],
        "theta_root": [],
        "done": [],
    }

    r = state["r"]
    r0 = params["r0"]
    root_idx = int(np.argmin(np.abs(r - r0)))

    theta_history = []
    Cn_history = []
    Cp_history = []
    Ck_history = []

    for _ in range(steps):
        state, reward, done, info = step_environment(state, action, params, dt=dt)

        records["C_s"].append(state["C_s"])
        records["C_p"].append(state["C_p"])
        records["L"].append(state["L"])
        records["LAI"].append(state["LAI"])
        records["U_eff"].append(state.get("U_eff", np.nan))
        records["reward"].append(reward)
        records["theta_root"].append(state["theta"][root_idx])
        records["done"].append(done)

        theta_history.append(state["theta"].copy())
        Cn_history.append(state["C_N"].copy())
        Cp_history.append(state["C_P"].copy())
        Ck_history.append(state["C_K"].copy())

        if done:
            break

    t = np.arange(len(records["C_s"])) * dt

    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.8))

    axes[0, 0].plot(t, records["C_s"], color="tab:purple")
    axes[0, 0].set_title("Storage Carbon C_s")
    axes[0, 0].set_xlabel("time")
    axes[0, 0].grid(alpha=0.3)

    axes[0, 1].plot(t, records["C_p"], color="tab:green")
    axes[0, 1].set_title("Structural Carbon C_p")
    axes[0, 1].set_xlabel("time")
    axes[0, 1].grid(alpha=0.3)

    axes[0, 2].plot(t, records["L"], color="tab:brown")
    axes[0, 2].set_title("Root Length L")
    axes[0, 2].set_xlabel("time")
    axes[0, 2].grid(alpha=0.3)

    axes[1, 0].plot(t, records["LAI"], color="tab:blue")
    axes[1, 0].set_title("LAI")
    axes[1, 0].set_xlabel("time")
    axes[1, 0].grid(alpha=0.3)

    axes[1, 1].plot(t, records["U_eff"], color="tab:red")
    axes[1, 1].set_title("U_eff")
    axes[1, 1].set_xlabel("time")
    axes[1, 1].grid(alpha=0.3)

    axes[1, 2].plot(t, records["reward"], color="black")
    axes[1, 2].set_title("Reward")
    axes[1, 2].set_xlabel("time")
    axes[1, 2].grid(alpha=0.3)

    save_fig(out_dir, "07_step_time_series.png")

    theta_history = np.array(theta_history)
    Cn_history = np.array(Cn_history)
    Cp_history = np.array(Cp_history)
    Ck_history = np.array(Ck_history)

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0))

    im0 = axes[0, 0].imshow(theta_history, aspect="auto", origin="lower", extent=[r[0], r[-1], 0, len(theta_history)])
    axes[0, 0].set_title("Water theta(r,t)")
    axes[0, 0].set_xlabel("radius")
    axes[0, 0].set_ylabel("step")
    plt.colorbar(im0, ax=axes[0, 0], fraction=0.046)

    im1 = axes[0, 1].imshow(Cn_history, aspect="auto", origin="lower", extent=[r[0], r[-1], 0, len(Cn_history)])
    axes[0, 1].set_title("N concentration C_N(r,t)")
    axes[0, 1].set_xlabel("radius")
    axes[0, 1].set_ylabel("step")
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046)

    im2 = axes[1, 0].imshow(Cp_history, aspect="auto", origin="lower", extent=[r[0], r[-1], 0, len(Cp_history)])
    axes[1, 0].set_title("P concentration C_P(r,t)")
    axes[1, 0].set_xlabel("radius")
    axes[1, 0].set_ylabel("step")
    plt.colorbar(im2, ax=axes[1, 0], fraction=0.046)

    im3 = axes[1, 1].imshow(Ck_history, aspect="auto", origin="lower", extent=[r[0], r[-1], 0, len(Ck_history)])
    axes[1, 1].set_title("K concentration C_K(r,t)")
    axes[1, 1].set_xlabel("radius")
    axes[1, 1].set_ylabel("step")
    plt.colorbar(im3, ax=axes[1, 1], fraction=0.046)

    save_fig(out_dir, "08_field_evolution_heatmaps.png")



def main():
    out_dir = ensure_output_dir()

    state, params = initialize_env()

    plot_water_constitutive_curves(params, out_dir)
    plot_nutrient_uptake_curves(params, out_dir)
    plot_total_uptake_and_u_eff(state, params, out_dir)
    plot_root_growth_terms(state, params, out_dir)
    plot_carbon_and_lai_functions(params, out_dir)
    run_step_simulation_and_plot(copy.deepcopy(state), params, out_dir)

    print(f"Saved plots to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
