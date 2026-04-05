Below is the **final refined system (without 3D)**, keeping:

* Root growth + branching (as total length dynamics)
* Water + nutrient coupling
* Improved photosynthesis
* Carbon splitting (storage + structure)

This is a **1D radial (around root) + lumped plant model**, which is much more tractable.

---

# 1. Soil Water Dynamics

[
\frac{\partial \theta(r,t)}{\partial t}
=======================================

\frac{1}{r}\frac{\partial}{\partial r}
\left(
r K(\theta)\frac{\partial \psi}{\partial r}
\right)
-------

S_w(r,t)
]

---

# 2. Nutrient Transport (for (i = N,P,K))

[
\frac{\partial C_i}{\partial t}
===============================

D_i
\left(
\frac{1}{r}\frac{\partial}{\partial r}
\left(r \frac{\partial C_i}{\partial r}\right)
\right)
-------

## v(\theta)\frac{\partial C_i}{\partial r}

S_i(r,t)
]

---

# 3. Root Uptake (Sink Terms)

## Nutrient sink

[
S_i(r,t)
========

\delta(r - r_0)
\cdot
\frac{I_{max,i} C_i(r_0,t)}{K_{m,i} + C_i(r_0,t)}
\cdot L(t)
]

---

## Water sink

[
S_w(r,t)
========

\delta(r - r_0)
\cdot
k_w L(t)
\cdot
\frac{\theta(r_0,t)}{\theta(r_0,t) + K_w}
]

---

# 4. Total Uptake

[
U_i =
2\pi r_0 L(t)
\cdot
\frac{I_{max,i} C_{i0}}{K_{m,i} + C_{i0}}
]

---

# 5. Effective Nutrient

[
U_{eff} =
\left(
\frac{1}{U_N} + \frac{1}{U_P} + \frac{1}{U_K}
\right)^{-1}
]

---

# 6. Root Growth + Branching (Lumped)

[
\frac{dL}{dt}
=============

k_L C_s
\cdot
\frac{U_{eff}}{K_U + U_{eff}}
-----------------------------

\delta_L L
+
\gamma_b L
\cdot
\frac{C_{eff}}{C_{eff} + K_b}
\cdot
\frac{\theta}{\theta + K_\theta}
]

* Growth + decay + branching contribution

---

# 7. Photosynthesis (Improved Form)

[
A =
\min(W_c, W_j)
\cdot
(1 - e^{-k \cdot LAI})
]

---

# 8. Water–Stomatal Coupling

[
g_s = g_{max} \cdot \frac{\theta}{\theta + K_\theta}
]

[
W_c \propto g_s
]

* Low water → reduced assimilation

---

# 9. Carbon Dynamics

## Storage Carbon

[
\frac{dC_s}{dt}
===============

## A

## k_g C_s

## r_m C_p

c_r \frac{dL}{dt}
]

---

## Structural Carbon (Biomass)

[
\frac{dC_p}{dt}
===============

## \alpha k_g C_s

\delta C_p \cdot \frac{C_{crit}}{C_s + \epsilon}
]

---

# 10. Leaf Area Index

[
LAI = c_L \cdot C_p^{\beta}
]

---

# 11. Boundary Conditions

## At root surface ( r = r_0 )

[

* D_i \frac{\partial C_i}{\partial r}
  =
  \frac{I_{max,i} C_{i0}}{K_{m,i} + C_{i0}}
  ]

[

* K(\theta)\frac{\partial \psi}{\partial r}
  =
  k_w \frac{\theta}{\theta + K_w}
  ]

---

## At outer boundary ( r = R )

[
C_i(R,t) = C_{b,i}(t), \quad \theta(R,t) = \theta_b(t)
]

---

# 12. System Flow

```text
Soil (C_i, θ)
     ↓
 Uptake (U_i)
     ↓
 Effective nutrient U_eff
     ↓
 Photosynthesis A
     ↓
 Storage C_s
     ↓
 Biomass C_p → LAI
     ↓
 Root growth L
     ↓
 Feedback to uptake
```

---

# 13. What This Version Achieves

* Keeps **physics-based soil transport**
* Adds **water–nutrient coupling**
* Includes **root growth + branching (lumped)**
* Uses **biochemical photosynthesis approximation**
* Maintains **carbon realism**

---

# 14. Key Insight

This model is:

* Much simpler than 3D
* Still captures:

  * Feedback loops
  * Resource competition
  * Growth vs death
  * Root expansion effects

---

# Final Summary

You now have a **balanced model**:

* PDEs: soil water + nutrients
* ODEs: carbon, biomass, root length
* Coupling: water ↔ nutrients ↔ carbon ↔ growth

---

This is **complex enough for realistic simulation**, but still **numerically feasible to implement and experiment with**.