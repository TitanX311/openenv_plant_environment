# Plant–Soil Carbon Dynamics: Model Equations

A coupled model describing nutrient uptake, photosynthesis, carbon allocation, and biomass accumulation in a soil–plant system.

---

## 1. Soil Nutrient Dynamics

The concentration $C_i$ of nutrient $i$ in the soil evolves via radial diffusion in cylindrical coordinates (around a root of radius $r_0$):

$$
\frac{\partial C_i}{\partial t} = D_i \frac{1}{r} \frac{\partial}{\partial r}\!\left(r \frac{\partial C_i}{\partial r}\right)
$$

| Symbol | Description | Units |
|--------|-------------|-------|
| $C_i$ | Soil concentration of nutrient $i$ | mol m⁻³ |
| $D_i$ | Effective diffusion coefficient of nutrient $i$ in soil | m² s⁻¹ |
| $r$ | Radial distance from root axis | m |

### Boundary Conditions

**Inner boundary** (root surface, $r = r_0$) — flux equals root uptake rate:

$$
-D_i \frac{\partial C_i}{\partial r}\bigg|_{r=r_0} = \frac{U_i}{2\pi r_0 \ell}
$$

**Outer boundary** (bulk soil, $r = r_b$) — no-flux (closed system) or constant concentration:

$$
\frac{\partial C_i}{\partial r}\bigg|_{r=r_b} = 0 \quad \text{(no-flux)} \qquad \text{or} \qquad C_i(r_b, t) = C_i^{\infty} \quad \text{(constant bulk)}
$$

**Initial condition:**

$$
C_i(r, 0) = C_i^0 \quad \forall\, r \in [r_0,\, r_b]
$$

---

## 2. Root Nutrient Uptake

Uptake of nutrient $i$ follows Michaelis–Menten kinetics integrated over root length $\ell$:

$$
U_i = 2\pi r_0 \ell \cdot \frac{I_{\max,i}\, C_i^0}{K_{m,i} + C_i^0}
$$

| Symbol | Description | Units |
|--------|-------------|-------|
| $U_i$ | Total uptake rate of nutrient $i$ | mol s⁻¹ |
| $r_0$ | Root radius | m |
| $\ell$ | Active root length | m |
| $I_{\max,i}$ | Maximum uptake rate per unit root area | mol m⁻² s⁻¹ |
| $C_i^0$ | Nutrient concentration at root surface | mol m⁻³ |
| $K_{m,i}$ | Michaelis–Menten half-saturation constant | mol m⁻³ |

---

## 3. Leaf Area Index

The Leaf Area Index (LAI) is a function of leaf carbon $C_\ell$ and structural biomass $C_p$:

$$
\text{LAI} = C_\ell \cdot C_p^{3}
$$

| Symbol | Description | Units |
|--------|-------------|-------|
| $C_\ell$ | Specific leaf area coefficient | m² (g C)⁻⁴ |
| $C_p$ | Structural (biomass) carbon pool | g C m⁻² |

> **Note:** The exponent 3 encodes an allometric scaling between canopy leaf area and plant structural size. This form is consistent with power-law allometries commonly reported for woody plants.

---

## 4. Carbon Assimilation (Photosynthesis)

Gross canopy photosynthesis uses a Beer–Lambert light-extinction model combined with Michaelis–Menten light saturation:

$$
A(t) = A_{\max} \left(1 - e^{-k\,\text{LAI}}\right) \frac{U}{K_U + U}
$$

| Symbol | Description | Units |
|--------|-------------|-------|
| $A(t)$ | Gross carbon assimilation rate | g C m⁻² d⁻¹ |
| $A_{\max}$ | Maximum photosynthetic capacity | g C m⁻² d⁻¹ |
| $k$ | Canopy light extinction coefficient | dimensionless |
| $U$ | Absorbed radiation (or photon flux) | µmol photons m⁻² s⁻¹ |
| $K_U$ | Half-saturation irradiance | µmol photons m⁻² s⁻¹ |

### Boundary Conditions

$$
A(t) \geq 0, \qquad A(t) \to A_{\max}\!\left(1 - e^{-k\,\text{LAI}}\right) \;\text{ as }\; U \to \infty
$$

---

## 5. Carbon Allocation

Assimilated carbon $A$ is partitioned between a **growth flux** $G$ and a **storage flux** $S$:

$$
A = G + S
$$

$$
G = f_g \, A \qquad \text{(growth flux)}
$$

$$
S = (1 - f_g)\, A \qquad \text{(storage flux)}
$$

| Symbol | Description | Units |
|--------|-------------|-------|
| $f_g$ | Growth allocation fraction ($0 < f_g < 1$) | dimensionless |
| $G$ | Carbon flux to growth | g C m⁻² d⁻¹ |
| $S$ | Carbon flux to storage pool | g C m⁻² d⁻¹ |

---

## 6. Storage Carbon Dynamics

The storage (non-structural carbohydrate) pool $C_s$ changes according to:

$$
\frac{dC_s}{dt} = S - k_g C_s - R_m
$$

where:

$$
R_m = r_m C_p \qquad \text{(maintenance respiration)}
$$

| Symbol | Description | Units |
|--------|-------------|-------|
| $C_s$ | Storage carbon pool | g C m⁻² |
| $S$ | Incoming storage flux from allocation | g C m⁻² d⁻¹ |
| $k_g$ | First-order growth mobilisation rate constant | d⁻¹ |
| $k_g C_s$ | Growth respiration flux drawn from storage | g C m⁻² d⁻¹ |
| $R_m$ | Maintenance respiration | g C m⁻² d⁻¹ |
| $r_m$ | Maintenance respiration coefficient | d⁻¹ |
| $C_p$ | Structural biomass carbon | g C m⁻² |

> **Note:** Maintenance respiration $R_m = r_m C_p$ reflects that metabolic upkeep costs scale with the size of the existing structural biomass (e.g., protein turnover, membrane maintenance). Typical values: $r_m \approx 0.01$–$0.02\ \text{d}^{-1}$ at 20 °C.

---

## 7. Structural Carbon (Biomass) Dynamics

Structural biomass $C_p$ accumulates from the growth flux mobilised from storage, minus senescence/tissue turnover losses:

$$
\frac{dC_p}{dt} = \alpha\, k_g C_s - \delta\, C_p
$$

The first term $\alpha k_g C_s$ represents the fraction $\alpha$ (growth efficiency, $0 < \alpha \leq 1$) of mobilised storage carbon that is actually incorporated into new structural tissue — the remainder $(1-\alpha)k_g C_s$ is lost as **growth respiration** $R_g$:

$$
R_g = (1-\alpha)\, k_g C_s
$$

The second term $\delta C_p$ represents first-order senescence (tissue turnover, mortality):

$$
\delta C_p \quad \text{(senescence/litter flux)}
$$

| Symbol | Description | Units |
|--------|-------------|-------|
| $C_p$ | Structural biomass carbon | g C m⁻² |
| $\alpha$ | Growth efficiency (fraction of mobilised C→structure) | dimensionless |
| $k_g$ | Storage mobilisation rate constant | d⁻¹ |
| $C_s$ | Storage carbon pool | g C m⁻² |
| $\delta$ | Senescence/turnover rate constant | d⁻¹ |

### Complete Biomass Equation

$$
\boxed{\frac{dC_p}{dt} = \alpha\, k_g C_s - \delta\, C_p}
$$

**At steady state** ($dC_p/dt = 0$):

$$
C_p^* = \frac{\alpha\, k_g C_s^*}{\delta}
$$

### Carbon Budget Check

Total respiration from the plant:

$$
R_{\text{total}} = R_g + R_m = (1-\alpha)\,k_g C_s + r_m C_p
$$

---

## 8. Boundary & Initial Conditions Summary

| Equation | Condition | Expression |
|----------|-----------|------------|
| Soil diffusion | $r = r_0$ (root surface) | $-D_i \partial C_i/\partial r = U_i / (2\pi r_0 \ell)$ |
| Soil diffusion | $r = r_b$ (bulk soil) | $\partial C_i/\partial r = 0$ or $C_i = C_i^\infty$ |
| Soil diffusion | $t = 0$ | $C_i(r,0) = C_i^0$ |
| Storage pool | $t = 0$ | $C_s(0) = C_{s,0} \geq 0$ |
| Biomass pool | $t = 0$ | $C_p(0) = C_{p,0} > 0$ |
| Photosynthesis | Physical | $A(t) \geq 0$ |
| Biomass | Physical | $C_p(t) \geq 0$, $C_s(t) \geq 0$ |

---

## 9. Model Coupling Diagram

```
Soil nutrients C_i  ──(diffusion)──►  Root surface
                                           │
                                    Uptake U_i
                                           │
                          ┌────────────────▼────────────────┐
                          │         Plant Carbon Model       │
                          │                                  │
            Light U ─────►  Photosynthesis A(t)             │
            LAI ─────────►  (Beer-Lambert × Michaelis-Menten)│
                          │          │                       │
                          │    Allocation (f_g)              │
                          │    G = f_g·A    S = (1-f_g)·A   │
                          │          │           │           │
                          │   Structural C_p   Storage C_s  │
                          │   dC_p/dt =        dC_s/dt =    │
                          │   α·kg·Cs - δ·Cp   S-kg·Cs-Rm  │
                          └──────────────────────────────────┘
```

---

## References

- Barber, S.A. (1984). *Soil Nutrient Bioavailability*. Wiley.
- Thornley, J.H.M. & Johnson, I.R. (1990). *Plant and Crop Modelling*. Oxford University Press.
- Amthor, J.S. (2000). The McCree–de Wit–Penning de Vries–Thornley respiration paradigms: 30 years later. *Annals of Botany*, 86, 1–20.
- Cannell, M.G.R. & Thornley, J.H.M. (2000). Modelling the components of plant respiration. *Annals of Botany*, 85, 55–67.