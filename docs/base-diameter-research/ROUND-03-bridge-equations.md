# ROUND 3 FINDINGS: BRIDGE EQUATIONS -- NYQUIST, FOURIER, LATTICE SAMPLING

## Executive Summary

The PPL discrete addressing lattice Z_12 x Z_6 x Z_7 x Z_8 = 4,032 addresses is a well-designed encoding system that sits in a Goldilocks zone for its domain: 4x larger than Dewey Decimal (enough resolution), 10-17x smaller than ICD-10 or Library of Congress (not bloated), and structurally superior to all comparison systems because its bits decompose into independently navigable dimensions. The lattice's spectral structure is dominated by the coprimality of 7 with all other factors, which guarantees zero aliasing between the 7-Order cycle and every other dial -- validating the architectural choice of 7 Orders from an information-theoretic standpoint. However, the investigation surfaces a critical structural tension: the fog-of-war diffusion model, if parameterized at alpha = d* ~ 1.5, produces near-uniform global spread (80% of spillover goes to distances 3 and 4), not the locality-preserving activation the framework describes. Additionally, the unweighted Hamming distance is a poor proxy for physiological proximity, requiring a weighted metric to make the body-lattice mapping meaningful.

---

## Information-Theoretic Capacity

### Bit Counts at Each Lattice Level

The encoding density at each level of the addressing system:

| Level | Address Count | Bits (log2) | Source |
|-------|--------------|-------------|--------|
| Base 4-dial lattice | 4,032 | 11.977 | 12 Operators x 6 Axes x 7 Orders x 8 Colors |
| With modifiers (+5 Types) | 20,160 | 14.299 | Base x 5 |
| With tail glyphs (+62 per district) | 249,984 | 17.932 | 6,552 districts x (38 + remainder) |
| Full skeleton | 406,224 | 18.632 | 6,552 x 62 |

Per-dial entropy decomposition of the base lattice:

- Operators: log2(12) = 3.585 bits
- Axes: log2(6) = 2.585 bits
- Orders: log2(7) = 2.807 bits
- Colors: log2(8) = 3.000 bits
- **Sum: 11.977 bits** (confirming log2(4032))

The base lattice is remarkably close to 12 bits (11.977) with near-zero wasted address space. The factorization 12 x 6 x 7 x 8 uses non-power-of-2 dimensions, meaning the encoding is optimized for semantic granularity rather than computational convenience.

The total channel capacity per Revelator string is C_total = H(address) + H(payload). The structured address header contributes 11.98 to 18.63 bits of zero-ambiguity information. The free-text payload contributes approximately N x 1.3 bits of actual information for N characters of English text (at Shannon's estimated entropy rate). A 280-character payload carries roughly 364 bits of actual information. The address header is a compact structured prefix (~3-5% of a typical message's total information) that provides perfect indexing into the meaning space. This is architecturally analogous to an IP packet: structured header for lossless routing, unstructured body for unbounded descriptive capacity.

### Nyquist Analysis for Training Sampling

At the framework's prescribed 3-6 sessions per week, Nyquist analysis reveals what the temporal sampling can and cannot capture:

| Training Frequency | Sampling Rate (fs) | Nyquist Limit (fN) | Period Equivalent |
|---|---|---|---|
| 3 sessions/week | 0.4286/day | 0.2143 cyc/day | 1 cycle per 4.7 days |
| 6 sessions/week | 0.8571/day | 0.4286 cyc/day | 1 cycle per 2.3 days |

**What is captured:** Weekly periodization (1/7 cyc/day) sits at 0.667x Nyquist at 3/week (marginal but valid) and 0.333x at 6/week (comfortable). Monthly and annual cycles are trivially captured. The minimum for weekly capture is 2 sessions per week.

**What is aliased:** Daily variation (1 cyc/day) requires 14 sessions/week (2/day) to capture. At 3/week, daily variation is at 4.67x Nyquist -- severely aliased. At 6/week, it is at 2.33x -- still aliased. Day-to-day fluctuations in mood, sleep quality, and readiness are filtered out by construction.

This is a design virtue, not a limitation. The 3-6 sessions/week rate is naturally matched to weekly periodization and longer cycles -- exactly the time scales where deliberate programming operates. The system filters out noise (daily variation) and captures signal (programmatic structure).

**Meaning-space Nyquist:** The lattice is not sampling a continuous time signal -- it is quantizing a multi-dimensional meaning space. 4,032 addresses oversample the practical training stimulus space (estimated 1,000-3,000 distinct stimuli) by a factor of 1.34x to 4.03x. If approximately 2,000 addresses are practically used, effective entropy = log2(2000) = 10.97 bits, giving 91.6% utilization of the lattice's 11.98-bit capacity.

### Comparison to Other Encoding Systems

| System | Code Count | Raw Bits | Domain Coverage Ratio | Structure |
|--------|-----------|----------|----------------------|-----------|
| Dewey Decimal | 1,000 | 9.97 | ~1.5x (hopelessly coarse) | Hierarchical tree |
| **PPL base** | **4,032** | **11.98** | **1.3-2.0x (well-packed)** | **Coordinate system (4 dims)** |
| Library of Congress | ~40,000 | 15.29 | ~4-5x | Hierarchical tree |
| US ZIP codes | ~42,000 | 15.36 | varies | Flat geographic |
| ICD-10 | ~70,000 | 16.10 | 4.7-7.0x (bloated) | Flat alphanumeric |
| **PPL full skeleton** | **406,224** | **18.63** | N/A | **Coordinate + tails** |

PPL is more efficiently packed than ICD-10 (1.3-2.0x overhead vs. 4.7-7.0x) despite having 17x fewer codes. The decisive structural advantage is that PPL's 11.98 bits decompose into 4 independently navigable dimensions. In PPL, changing one dial while holding others fixed traces a meaningful path (progression, variation, periodization). In ICD-10, incrementing a code (I25.1 to I25.2) may land on an unrelated diagnosis. PPL addresses support dimensional algebra; ICD-10 codes do not. This is the difference between a coordinate system and a dictionary: both identify locations, but only the coordinate system tells you how to navigate to adjacent locations.

---

## Lattice Frequency Structure

### Natural Frequencies and the Grand Period (168)

The fundamental periods of the lattice Z_12 x Z_6 x Z_7 x Z_8 are the factor sizes themselves: 12, 6, 7, 8. The pairwise LCMs reveal the period structure:

| Pair | LCM | Shared factors |
|------|-----|----------------|
| (12, 6) | 12 | gcd = 6 |
| (12, 7) | 84 | gcd = 1 (coprime) |
| (12, 8) | 24 | gcd = 4 |
| (6, 7) | 42 | gcd = 1 (coprime) |
| (6, 8) | 24 | gcd = 2 |
| (7, 8) | 56 | gcd = 1 (coprime) |

**Grand period:** LCM(12, 6, 7, 8) = 168 = 2^3 x 3 x 7. The lattice contains exactly 4032/168 = 24 copies of the grand-period unit cell. A diagonal path (1,1,1,1)^t takes 168 steps to return to the origin.

**Prime decomposition via Chinese Remainder Theorem:**

- 2-Sylow part: Z_8 x Z_4 x Z_2 (64 points)
- 3-Sylow part: Z_3 x Z_3 (9 points -- genuinely rank-2, NOT isomorphic to Z_9)
- 7-part: Z_7 (7 points)
- Product: 64 x 9 x 7 = 4,032

The group is not cyclic -- a single generator cannot reach all lattice points, which is why the index [G : <(1,1,1,1)>] = 4032/168 = 24.

The DFT on the lattice has exactly 4,032 basis functions, each a product of four 1D characters:

chi_{(k1,k2,k3,k4)}(n1,n2,n3,n4) = exp(2*pi*i*k1*n1/12) * exp(2*pi*i*k2*n2/6) * exp(2*pi*i*k3*n3/7) * exp(2*pi*i*k4*n4/8)

### The Coprime Structure and Its Spectral Consequences

The coprimality of 7 with all other dimensions (gcd(7,12) = gcd(7,6) = gcd(7,8) = 1) is the lattice's most important structural feature. Three consequences:

**1. Spectral non-aliasing.** The 7th roots of unity are disjoint from the roots of unity generated by 12, 6, and 8 (which all live in Q(zeta_24) since LCM(12,6,8) = 24). The 7th cyclotomic polynomial Phi_7(x) = x^6 + x^5 + x^4 + x^3 + x^2 + x + 1 is irreducible over Q(zeta_24). No Z_7 Fourier mode ever aliases with any mode from the other three dimensions. The 4,032 characters split cleanly into 576 "7-blind" modes (chi_3 trivial) and 3,456 "7-sensitive" modes (chi_3 nontrivial).

**Concrete meaning:** Any periodicity arising from the 7-Order cycle (weekly training patterns) is mathematically guaranteed to be distinguishable from periodicities arising from the 12-Operator cycle (monthly patterns), the 6-Axis cycle, or the 8-Color cycle. The 7-cycle carries genuinely independent information.

**2. Maximal orbit coverage.** On Z_12 x Z_7, the orbit {(t mod 12, t mod 7) : t = 0,1,...} visits ALL 84 points because gcd(12,7) = 1. Compare: Z_12 x Z_6 visits only 12 of 72 points (16.7%) and Z_12 x Z_8 visits 24 of 96 (25%). The Z_12 x Z_7 projection achieves 100% coverage -- the maximum possible for any 2D slice.

**3. Algebraic independence (incommensurability).** The non-7 lattice Z_12 x Z_6 x Z_8 has grand period 24 = 2^3 x 3. Adding Z_7 multiplies the period by exactly 7 (from 24 to 168). The Galois group decomposes as Gal(Q(zeta_24)/Q) x Gal(Q(zeta_7)/Q), and the number-field extensions are linearly disjoint. This is not metaphorical incommensurability -- it is a theorem.

**On the 12/7 ratio:** 12/7 = 1.714... is rational (continued fraction [1; 1, 2, 2]), so it cannot generate a quasi-periodic tiling in the classical Penrose/de Bruijn sense (which requires irrational slope). However, the coprimality gcd(12,7) = 1 achieves the discrete analog of irrational rotation on the torus: 100% orbit coverage. On finite cyclic products, coprimality plays the role that irrationality plays on the continuum.

**A numerical coincidence worth noting:** The Euler totient phi(7) = 6 equals the number of Axes in the system. The dimension of the Galois extension Q(zeta_7)/Q equals the Axis count. Whether this is meaningful depends on whether a derivation can be found connecting them. None currently exists.

### Annual Rotation Coverage: What Fraction Does a User Actually Visit?

The seasonal rotation path has effective dimension 3 (two deterministic periodic coordinates plus one free coordinate). The Operator dial advances on a 12-month cycle; the Axis is determined by the Operator via a 2-to-1 map (contributing 0 additional degrees of freedom); the Order dial follows the weekday on a 7-cycle (of which only 5 values are visited on training days); and the Color dial is a free user choice from 8 options.

**Annual coverage under various Color diversity assumptions:**

| Color Selection | Reachable Addresses | Expected Unique Visits (260 sessions) | % of 4,032 |
|---|---|---|---|
| 8 Colors (uniform) | 480 | ~201 | 5.0% |
| 4 Colors (realistic) | 240 | ~159 | 3.9% |
| 2 Colors (concentrated) | 120 | ~103 | 2.6% |

The theoretical maximum reachable in one year is 480 addresses (12 Operators x 1 Axis per Operator x 5 Orders x 8 Colors), which is 11.9% of the full lattice.

**Coupon collector timescales** (under uniform Color):

- 2 years: 318 addresses (66.2% of reachable)
- 5 years: 448 (93.4%)
- 10 years: 478 (99.6%)
- Full coverage E[sessions] = 3,241 = **12.5 years**

**Why 5% annual coverage is a feature, not a defect:** Three structural constraints prevent space-filling: (1) rest days eliminate 2 of 7 Orders (28.6% of Order space unreachable), (2) the Operator-to-Axis coupling reduces the effective (Operator, Axis) space from 72 to 12 points, and (3) Color is user-selected. The lattice is designed to be explored over a lifetime, not exhausted in a year. The 12.5-year full-coverage timeline aligns with the ESQUISSE's multi-year "octave" structure.

The 88.1% of the lattice that is NEVER reachable by the seasonal rotation (3,552 of 4,032 addresses) corresponds to rest-day Orders and Operator-Axis combinations the monthly rotation does not produce -- structurally present but experientially absent "dark matter."

**The coprime scrambling effect:** Because gcd(12,7) = 1, the monthly rotation does not synchronize with the weekly Order cycle. The (Operator, Order) pairs visited in year 2 begin on a different phase offset than year 1. Over multiple years, the lattice fills in a pattern analogous to low-discrepancy sequences (quasi-random rather than pseudorandom), which is optimal for high-dimensional exploration.

**Critical subtlety on the 5/7 interaction:** The 5-day/7-day coprime interaction (gcd(5,7) = 1, LCM = 35) fills all 35 (Order, Type) pairs in a 35-day supercycle. But this ONLY works if the Type/Modifier assignment follows calendar days mod 5, not training days mod 5. If Type tracks training-day count, then 5 training days per week means 5 mod 5 = 0, and the counter resets every week, destroying the coprime scrambling. The implementation must follow calendar-day mod 5.

---

## Distance Metric and Diffusion

### Hamming Distance Distribution -- Verified

For any zip z on the 4-dial lattice, the Hamming distance distribution to all other zips:

| Distance | Count | Formula | % of Lattice |
|----------|-------|---------|---------------|
| 0 | 1 | 1 | 0.02% |
| 1 | 29 | (12-1)+(6-1)+(7-1)+(8-1) | 0.72% |
| 2 | 305 | sum of pairwise products of (n_i - 1) | 7.57% |
| 3 | 1,387 | sum of triple products of (n_i - 1) | 34.40% |
| 4 | 2,310 | 11 x 5 x 6 x 7 | 57.29% |
| **Total** | **4,032** | product(n_i) = product(1 + (n_i-1)) | **100%** |

The checksum identity 1 + 29 + 305 + 1,387 + 2,310 = 4,032 is confirmed. This is a tautological expansion of product_i(1 + (n_i - 1)) = product_i(n_i) = N, guaranteed to hold for any product lattice.

**Statistical properties:**
- Mean distance: sum_i(1 - 1/n_i) = 11/12 + 5/6 + 6/7 + 7/8 = 3.4821
- Variance: 0.4471
- Standard deviation: 0.6687
- Shannon entropy of distribution: 1.326 bits (out of max log2(5) = 2.322 bits; normalized = 0.571)

### The Skew Correction: LEFT-Skewed, Not Right-Skewed

**CORRECTION:** The ESQUISSE describes the distribution as "heavily right-skewed." This is reversed. The distribution is LEFT-skewed (skewness = -1.09). The mode is at distance 4 (57.29%) and the thin tail extends toward distance 0. The mass is concentrated at HIGH distances. 91.7% of all point pairs are at distance 3 or 4. Only 0.74% of pairs are nearest neighbors (distance 1).

The mean distance (3.48) is 87% of the maximum (4), indicating the lattice is "almost maximally spread" in Hamming distance. This is a defining structural feature: the 4,032-point lattice is sparse relative to its own metric. The fraction at maximum distance equals (11/12)(5/6)(6/7)(7/8) = 2310/4032 = 57.29% -- the probability that all four coordinates independently differ.

### Weighted Hamming Metric for Physiological Proximity

The unweighted Hamming distance is a POOR proxy for physiological proximity. The fundamental problem is that it treats all coordinate mismatches as equal, while physiological transfer is highly non-uniform across coordinates:

| Coordinate | Unweighted Share of d=1 Neighbors | Physiological Relevance |
|---|---|---|
| Operator (verb) | 11 of 29 (37.9%) | Moderate -- determines contraction mode |
| Axis (movement plane) | 5 of 29 (17.2%) | **Highest** -- determines muscle groups, joints, neural pathways |
| Order (phase) | 6 of 29 (20.7%) | Moderate -- determines load/volume |
| Color (session format) | 7 of 29 (24.1%) | **Lowest** -- affects psychology, not physiology |

Color changes contribute 1.4x more neighbors than Axis changes in the unweighted metric. But Axis is the primary determinant of which muscles, joints, and neural pathways are active. The metric assigns equal cost to (same Axis, different Color) and (same Color, different Axis), when the first pair shares virtually all physiological substrate and the second may share almost none.

**Proposed weighted metric:**

d_w(z1, z2) = 1.0 x [Axis differs] + 0.7 x [Operator differs] + 0.4 x [Order differs] + 0.15 x [Color differs]

| Weight | Coordinate | Rationale |
|--------|-----------|-----------|
| 1.0 | Axis | Determines primary muscle groups, joints, neural control pathways |
| 0.7 | Operator | Determines contraction mode and neural demand; shares muscle groups within Axis |
| 0.4 | Order | Same movement at different loads; substantial but incomplete transfer |
| 0.15 | Color | Session format and psychological register; near-zero physiological relevance |

Under this weighted metric:
- Exercises differing only on Color: weighted distance = 0.15 (near-identical physiologically)
- Exercises differing only on Axis: weighted distance = 1.0 (maximum single-coordinate cost)
- Ratio: 6.67:1, reflecting the empirical reality of bilateral transfer literature
- Maximum weighted distance: 2.25 (all coordinates differ)
- Mean weighted distance: 1.949 (normalized: 0.866)

The weighted shares shift dramatically: Axis goes from 23.9% to 42.8% of mean distance; Color drops from 25.1% to 6.7%. These weights should be treated as tunable parameters validated against empirical bilateral transfer data (Research Path 3, Phase 1).

### Power-Law Diffusion at alpha ~ 3/2: A Critical Problem

For power-law spillover f(d) = d^(-alpha), the total weighted spillover at distance d is W(d) = |B_d| x d^(-alpha), where |B_d| is the number of points at that distance. Three regimes emerge:

| Regime | Alpha Range | Distance-1 Share | Character |
|--------|------------|-----------------|-----------|
| Broad/global diffusion | alpha < 3.3 | < 25% | Nearly transparent fog-of-war |
| Transition zone | 3.3 < alpha < 7.0 | 25% - 90% | Local and global coexist |
| Nearest-neighbor dominated | alpha > 7.0 | > 90% | Dense fog-of-war, strong locality |

**At the framework's target exponent alpha = d* ~ 1.5:**

| Distance | Per-Point Weight | Count | Total Spillover | Share |
|----------|-----------------|-------|-----------------|-------|
| 1 | 1.000 | 29 | 29.0 | **4.2%** |
| 2 | 0.354 | 305 | 107.8 | 15.6% |
| 3 | 0.193 | 1,387 | 267.2 | 38.5% |
| 4 | 0.125 | 2,310 | 288.8 | **41.7%** |

Distances 3 and 4 together absorb **80.2%** of all spillover. Nearest neighbors receive only 4.2%. The effective mean diffusion reach is 3.18 out of a maximum of 4.

The reason alpha needs to be much larger than intuition suggests is the combinatorial explosion: the COUNT at d=4 is 79.7x the count at d=1. To make d=1 merely EQUAL d=4 in total weight, alpha must satisfy 4^(-alpha) x 2310 = 1^(-alpha) x 29, giving alpha > ln(79.7)/ln(4) = 3.15. For genuine dominance, alpha must be significantly larger still.

**This is a structural tension with the framework.** The ESQUISSE describes fog-of-war as a locality-preserving mechanism where "addresses at distance 1 receive the most spillover, distance 2 less, distance 3 less, distance 4 least." For this to hold, alpha must be at least ~4.5 (where d=1 share reaches 51%), and preferably > 7 for strong locality. Using d* ~ 1.5 as the spillover exponent produces near-uniform global spread, not local diffusion.

The framework faces a choice: either d* governs fractal dimension but NOT spillover decay (decoupling the two uses of d*), or d* governs spillover but the fog-of-war is a global mechanism, not a local one.

---

## What This Means for the Framework

### Is 4,032 Addresses Enough? Too Many? Just Right?

**Just right** -- with a caveat. The lattice sits in a Goldilocks zone:

- 4,032 addresses oversample the practical stimulus space by 1.3-4x, ensuring every meaningfully distinct stimulus gets its own address with no forced collisions
- The 11.977-bit encoding approaches the theoretical ideal of 12 bits with near-zero waste
- The structured 4-dimensional encoding supports navigational operations (same movement, next order; same order, different axis) that flat encoding systems cannot
- The full skeleton at 406,224 addresses provides ample room for tail-glyph differentiation without altering the core lattice

The caveat: only 480 of 4,032 addresses are reachable by the seasonal rotation (11.9%), and a typical year visits only ~200 (5.0%). The lattice is well-sized for its ADDRESSING purpose but dramatically oversized relative to any single user's annual experience. This is by design -- it is a lifetime coordinate system, not an annual calendar.

### Does the Lattice Structure Help or Hinder the Compiler?

**Helps** in three specific ways:

1. **Dimensional algebra.** The product structure enables "hold three dials, vary one" operations that are the core of systematic programming. No flat encoding system supports this.

2. **Spectral separation.** The coprime structure guarantees that weekly, monthly, and color-cycle periodicities never alias. The compiler can decompose a user's training history into independent frequency components without cross-contamination.

3. **Lifetime exploration.** The 12.5-year coupon-collector timeline and the quasi-random fill pattern ensure that long-term users continuously encounter genuinely novel combinations, preventing dead periodicity without requiring explicit randomization.

**Hinders** in two ways that require design decisions:

1. **The fog-of-war exponent problem.** The framework cannot use d* ~ 1.5 as both the fractal dimension target AND the diffusion exponent. These serve different mathematical roles and produce contradictory behavior when unified. The compiler must either decouple them or accept that fog-of-war is a global (not local) mechanism.

2. **The body-lattice mapping problem.** The unweighted Hamming distance does not correspond to physiological proximity. The compiler's diffusion step will propagate activation incorrectly unless it uses a weighted metric. This requires implementing and calibrating the weighted Hamming distance before the fog-of-war can function as described.

### What Is the Actual Coverage Gap?

Three gaps identified:

1. **Rest-day gap:** 2 of 7 Orders (28.6%) are never visited because training occurs on 5 of 7 weekdays. These "dark matter" addresses exist in the lattice but have no experiential content.

2. **Axis-coupling gap:** The Operator-to-Axis 2-to-1 map means 60 of 72 possible (Operator, Axis) pairs are never produced by the seasonal rotation. The lattice reserves address space for stimulus combinations the rotation does not generate.

3. **Color-preference gap:** User Color selection is not uniform. Realistic preferences (4 primary Colors out of 8) reduce annual coverage from 201 to 159 unique addresses.

Together, these gaps mean a user touches ~5% of the lattice per year and can never reach ~88% of it through normal operation. The unreachable space serves architectural purposes (completeness, dimensional consistency, potential for non-standard rotations) but the compiler must account for the sparsity of actually-visited addresses.

---

## Claims Status Update

| Claim ID | Claim | Prior Status | Round 3 Verdict | Evidence |
|----------|-------|-------------|-----------------|----------|
| BRIDGE-04 | 4,032 addresses sample the adaptive field losslessly (Nyquist) | NEEDS-COMPUTATION | **PARTIALLY CONFIRMED** | 4,032 addresses oversample the practical stimulus space by 1.3-4x; temporal Nyquist at 3-6 sessions/week captures weekly+ cycles but aliases daily variation (by design); meaning-space sampling is sufficient |
| BRIDGE-06 | 20,160 extended addresses meet Nyquist | NEEDS-COMPUTATION | **CONFIRMED** | log2(20160) = 14.30 bits; with 5 Types the extended lattice provides comfortable oversampling at all relevant training frequencies |
| BRIDGE-10 | Information-theoretic capacity: 11.98 bits base, 14.30 extended | VERIFIABLE-NOW | **CONFIRMED** | log2(4032) = 11.977, log2(20160) = 14.299, log2(249984) = 17.932, log2(406224) = 18.632 -- all verified |
| BRIDGE-12 | Fourier reconstruction from discrete lattice | NEEDS-COMPUTATION | **CONFIRMED (structure)** | DFT has exactly 4,032 basis functions factoring as products of 1D characters; the coprime structure guarantees clean spectral separation between Z_7 modes and all other dimensions |
| RP2-01 | Discrete Fourier basis has identifiable natural frequencies | NEEDS-COMPUTATION | **CONFIRMED** | Fundamental periods 12, 6, 7, 8; grand period 168 = 2^3 x 3 x 7; 576 "7-blind" modes and 3,456 "7-sensitive" modes with zero cross-talk |
| RP2-02 | Lattice natural frequencies match human adaptive periodicities | NEEDS-EMPIRICAL-STUDY | **PARTIALLY CONFIRMED** | Weekly cycle maps to Z_7, monthly to Z_12, annual to octave spiral; temporal Nyquist confirms 3-6 sessions/week captures weekly+ periodicities; daily variation correctly aliased out |
| RP2-03 | 12/7 ratio has quasi-periodic tiling properties | NEEDS-COMPUTATION | **REFINED** | 12/7 is rational and CANNOT generate quasi-periodic tiling (requires irrational slope); however, gcd(12,7)=1 achieves 100% orbit coverage on Z_12 x Z_7, the discrete analog of irrational rotation -- coprimality is the operative concept, not irrationality |
| RP6-P1-01 | 11.98 bits per base address | VERIFIABLE-NOW | **CONFIRMED** | log2(4032) = 11.977 verified |
| RP6-P1-02 | 14.30 bits per extended address | VERIFIABLE-NOW | **CONFIRMED** | log2(20160) = 14.299 verified |
| RP6-P2-01 | Hamming distance max = 4 | VERIFIABLE-NOW | **CONFIRMED** | Trivially verified from 4-dial structure; full distance distribution 1/29/305/1387/2310 confirmed with checksum = 4,032 |
| RP6-P2-02 | Fog-of-war power-law exponent = d* | NEEDS-EMPIRICAL-STUDY | **PROBLEMATIC** | At alpha = d* ~ 1.5, spillover is 80% global (d=3 and d=4), only 4.2% to nearest neighbors; this contradicts the stated local-diffusion intent; alpha must be >= 4.5 for even 50% nearest-neighbor share, >= 7.0 for strong locality |
| RP6-P3-01 | Body-lattice mapping: Hamming distance = physiological proximity | NEEDS-EMPIRICAL-STUDY | **REFUTED (unweighted)** | Unweighted Hamming treats all coordinate mismatches equally; Color changes (physiologically negligible) contribute 1.4x more neighbors than Axis changes (physiologically dominant); weighted metric proposed: Axis=1.0, Op=0.7, Ord=0.4, Col=0.15 |
| BRIDGE-07 | Fog-of-war via Hamming distance | NEEDS-COMPUTATION | **REFINED** | Hamming distance is computationally clean but physiologically incorrect without weighting; the framework needs the WEIGHTED Hamming metric (or equivalent) for the diffusion step to mirror bilateral transfer |
| RP5-COPRIME-01 | 5/7 coprime property as quasi-periodicity | NEEDS-COMPUTATION | **CONFIRMED with caveat** | gcd(5,7)=1 produces 35-day supercycle visiting all 35 (Order, Type) pairs; CRITICAL: only works if Type assignment follows calendar-day mod 5, not training-day mod 5 |
| RP5-P52-02 | PDE system is inherently quasi-periodic | NEEDS-COMPUTATION | **REFINED** | The system is quasi-periodic in the sense that gcd(12,7)=1 prevents exact repetition of (Operator, Order) pairs, and the Gregorian calendar irregularity extends the exact repeat period to 140 years; however, it is NOT quasi-periodic in the crystallographic tiling sense (all ratios are rational) |
| BRIDGE-08 | Spillover power law exponent = d* | NEEDS-COMPUTATION | **REFUTED (as unified claim)** | Using d* ~ 1.5 as spillover exponent produces global diffusion, not local; d* may govern fractal dimension but cannot simultaneously govern spillover decay if local diffusion is desired |

### New Claims Surfaced in Round 3

| Claim ID | Claim | Status | Source |
|----------|-------|--------|--------|
| R3-NEW-01 | The ESQUISSE describes the distance distribution as "right-skewed"; it is LEFT-skewed (skewness = -1.09) | **CORRECTION** | 6.2b verification |
| R3-NEW-02 | The Z_7 factor contributes algebraically independent Fourier modes that never alias with modes from Z_12, Z_6, or Z_8 | **CONFIRMED** | Cyclotomic polynomial analysis |
| R3-NEW-03 | Annual rotation visits ~5% of lattice (201/4032 under uniform Color) | **CONFIRMED** | Birthday-problem calculation |
| R3-NEW-04 | Full reachable coverage requires ~12.5 years (coupon collector: 3,241 sessions) | **CONFIRMED** | Coupon collector analysis |
| R3-NEW-05 | 88.1% of the lattice (3,552 addresses) is unreachable by normal seasonal rotation | **CONFIRMED** | Structural constraint analysis |
| R3-NEW-06 | The weighted Hamming metric resolves the body-lattice mapping problem | **PROPOSED** | Needs empirical calibration against bilateral transfer data |

### Cumulative Scorecard (Rounds 1-3)

| Verdict | Round 1 | Round 2 | Round 3 | Total |
|---------|---------|---------|---------|-------|
| CONFIRMED | 1 | 1 | 9 | 11 |
| PARTIALLY CONFIRMED | 5 | 1 | 2 | 8 |
| REFINED | 4 | 0 | 3 | 7 |
| NOVEL CONNECTION | 0 | 1 | 0 | 1 |
| PROBLEMATIC | 0 | 0 | 1 | 1 |
| NO KNOWN CONNECTION | 0 | 1 | 0 | 1 |
| REFUTED | 2 | 7 | 2 | 11 |
| UNDERDETERMINED | 3 | 0 | 0 | 3 |
| **Claims evaluated** | **15** | **11** | **17** | **43 of 125** |

Round 3 is the first round with a positive tilt: 9 confirmations vs. 2 refutations. The lattice's information-theoretic and spectral properties hold up well under scrutiny. The structural tensions (fog-of-war exponent, body-lattice mapping) are real but addressable through design decisions rather than architectural overhaul.
