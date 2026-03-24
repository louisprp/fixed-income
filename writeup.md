# a) Constructing interest rate trees

## Yield-curve data source and treatment

The valuation date used in this assignment is 30 January 2026. The zero curve is constructed from UK government spot-curve data obtained from the Bank of England nominal government liability curve dataset. This source was chosen because it is a reputable public provider, it is available at a range of maturities, and it is consistent with the objective of valuing a sterling fixed-rate mortgage product issued in the UK.

The model requires zero-coupon discount factors on a regular semi-annual grid from 0.5 years to 10 years. The raw data do not necessarily provide observations exactly on every required maturity, so the observed spot rates are converted into discount factors first, and the discount curve is then interpolated in log discount-factor space. This choice is justified for two reasons. First, the tree calibration is based on zero-coupon prices rather than on yields themselves. Second, interpolating log discount factors tends to preserve monotonicity and produces economically sensible discount curves, while direct interpolation of spot rates can create small inconsistencies in discount prices.

Formally, if z(t) denotes the continuously compounded zero rate at maturity t, the corresponding zero-coupon price is
P(0,t) = exp(-z(t)t).
The observed discount prices are interpolated across maturity, and the continuously compounded zero rate on the model grid is then recovered from
z(t) = -ln(P(0,t))/t.

This approach is appropriate because both the Ho-Lee and Black-Derman-Toy trees in this assignment are calibrated to match the term structure of zero-coupon bond prices exactly.

## Compounding convention

The assignment specifies continuously compounded short rates for the interest-rate models. For that reason, all discounting inside the Ho-Lee and BDT trees uses continuous compounding over intervals of length Delta = 0.5. In particular, one-step discounting is performed using exp(-r Delta).

However, the mortgage cash flows themselves are modeled as standard fixed-rate mortgage payments made semi-annually. This means the mortgage coupon rate is treated as a quoted annual rate converted into a per-period mortgage rate by multiplying by Delta. This choice reflects standard mortgage-amortization practice and is also consistent with the lecture methodology, where short-rate discounting and mortgage payment conventions are conceptually separate objects. The short-rate model determines discounting under the risk-neutral measure, while the mortgage contract determines the promised cash-flow schedule.

This distinction is important. The continuously compounded convention applies to the short-rate tree, not to the mortgage payment formula.

## Choice of time step

A semi-annual time step, Delta = 0.5, is used throughout. This is imposed directly by the assignment and is also natural for two reasons. First, it keeps the tree aligned with the mortgage payment frequency in the model. Second, it is fine enough to capture prepayment timing and interest-rate variation over a 10-year horizon without making the recombining tree excessively large.

## Choice of Ho-Lee and BDT models

Two short-rate models are used: Ho-Lee and Black-Derman-Toy. The reason for estimating both is robustness. The Ho-Lee model is simple, additive, and easy to calibrate exactly to the initial term structure. The BDT model is lognormal in rates and therefore ensures positive short rates. Comparing results across the two models helps identify how much the mortgage valuation depends on assumptions about the shape of rate uncertainty rather than only on the initial yield curve.

The Ho-Lee model is useful as a benchmark because of its tractability. Its main drawback is that, because the model is additive in the short rate, negative rates may arise in sufficiently low-rate states. The BDT model avoids this by modeling the logarithm of the short rate instead. This makes BDT attractive for longer-horizon mortgage valuation, especially when prepayment behavior depends heavily on the distribution of future refinancing opportunities.

## Calibration of the yield curve

The trees are calibrated so that the model reproduces the observed zero-coupon prices exactly on the semi-annual grid. This is done recursively, level by level. At each maturity step, the free level parameter in the tree is chosen so that the model price of the corresponding zero-coupon bond equals the observed market price.

This exact-fit approach is appropriate because the purpose of the exercise is valuation under a risk-neutral model. If the tree did not fit the initial discount curve, all subsequent mortgage and MBS valuations would be internally inconsistent with current market prices.

## Estimation of volatility parameters

The Ho-Lee and BDT models each require a volatility input. These parameters are not directly observable from the cross-sectional yield curve used for calibration, so an additional time-series estimate is needed.

For the Ho-Lee model, volatility is estimated from changes in the 6-month spot rate. This is appropriate because Ho-Lee assumes additive dynamics in rates, so the natural empirical object is the change in the short rate itself.

For the BDT model, volatility is estimated from changes in the logarithm of the 6-month spot rate. This is appropriate because BDT assumes lognormal rate dynamics, so the natural empirical object is the change in log rates.

The 6-month maturity is used because the model time step is semi-annual and the short rate in the tree should correspond as closely as possible to the shortest maturity represented in the model grid. A monthly time series is used for the estimation window from January 2023 to January 2026. This window is a compromise between having enough observations for a stable estimate and keeping the estimate relevant to the current rate environment. A much longer sample would increase precision but could incorporate regimes that are less informative for conditions prevailing at the valuation date. A much shorter sample would better reflect current conditions but would make the estimate noisy.

This is not the only possible estimation choice. One could instead estimate volatility from short-maturity forward rates, short OIS rates, or use a longer time series. The present choice is justified by transparency, data availability, and consistency with the model time step.

## Practical limitations

The ideal calibration input for a short-rate model would be a clean term structure of default-free zero-coupon discount factors and a separate estimate of instantaneous short-rate volatility under a well-specified statistical model. In practice, publicly available data are imperfect. The spot curve is an estimated government curve rather than a directly observed full set of zero-coupon prices, and the volatility estimate is based on historical variation in one maturity rather than on a full dynamic term-structure model. These compromises are acceptable for the purposes of the assignment, provided they are clearly documented and their implications are acknowledged.

# b) Valuing the mortgage contract

## Benchmark assumption on borrower behavior

In this benchmark part, borrowers are assumed to prepay optimally and never default. This assumption is intentionally stylized. It isolates the pure value of the embedded prepayment option and therefore provides a clean benchmark for comparing the two interest-rate models.

The mortgage is valued as a fixed-rate amortizing loan with an embedded American-style prepayment option. The no-prepayment value is first computed by backward induction. Then the value of the borrower’s option to refinance is computed by comparing, at each node, the continuation value of the option with the value obtained from immediate exercise. The mortgage value is the no-prepayment value minus the value of this prepayment option.

This framework is appropriate because prepayment is economically equivalent to a call option held by the borrower: when refinancing becomes attractive enough, the borrower retires the old loan and replaces it with a new one. The lender therefore owns a callable fixed-income asset.

## Why solve for the mortgage rate that makes value equal to par

The objective is to recommend a fixed rate for a new mortgage product. From the lender’s perspective, the natural benchmark is the contract rate that makes the mortgage worth approximately its principal at origination. If the rate is set lower than that, the lender originates the loan at an economic loss. If it is set higher, the contract is more valuable to the lender but also less attractive to borrowers.

Solving for the par mortgage rate is therefore the correct way to translate the model into a pricing recommendation.

## Interpretation of differences between Ho-Lee and BDT

The model-implied par rate under BDT is slightly higher than under Ho-Lee. This is economically plausible. Although both trees fit the same initial term structure, they generate different distributions of future short rates. Ho-Lee is additive and more symmetric in rate space, while BDT is lognormal and produces a positively skewed distribution of future rates with no negative-rate states. Since mortgage value depends on both discounting and the borrower’s refinancing option, the shape of the future rate distribution matters. Even with the same current yield curve, different models can therefore imply different prepayment-option values and hence different par mortgage rates.

A slightly higher BDT mortgage rate suggests that, under the BDT distribution of future rates, the lender requires a somewhat higher coupon to offset the value of the borrower’s option.

# c) Constructing MBSs

## Why the pass-through coupon is set 50 basis points below the mortgage rate

The assignment states that the pass-through, IO, and PO securities are issued with a coupon rate 50 basis points below the mortgage rate to recover securitization costs. This means the mortgage pool generates the original mortgage cash flows, but investors in the securitized products receive a lower pass-through coupon. The difference represents an excess spread retained by the issuer or used to cover fees and servicing costs.

This is realistic from a securitization perspective. In practice, the coupon paid to MBS investors is typically below the gross coupon on the underlying mortgages because servicing, administration, credit enhancement, or structuring costs need to be funded.

## Why PT, IO, and PO are valued separately

Separating the pass-through into IO and PO strips is useful because each security is exposed differently to prepayment risk.

The PO receives principal only. Faster prepayment tends to increase the value of the PO because principal is returned earlier and therefore discounted less heavily.

The IO receives interest only. Faster prepayment tends to reduce the value of the IO because the remaining balance declines more quickly, shortening the stream of future interest payments.

The PT combines both principal and interest and can be viewed as the sum of the PO and IO. Reporting all three valuations helps show clearly how the embedded prepayment option redistributes value across tranches.

## Why model differences matter for the MBSs

Differences between Ho-Lee and BDT matter because PT, IO, and PO prices are highly sensitive to the timing of prepayment, and prepayment itself depends on future rates. Even if the two models fit today’s yield curve equally well, they produce different future rate distributions. This changes the likelihood and timing of refinancing and therefore changes the values of the strips.

The IO is usually the most model-sensitive component because its value depends strongly on mortgage survival. The PO is also sensitive, but often in the opposite direction.

# d) Interest rate trees with Monte Carlo

## Why Monte Carlo is introduced after tree valuation

The tree methodology is convenient for solving optimal exercise problems because backward induction can be used directly. Monte Carlo is introduced as a complementary valuation method and as a way to examine the implied distribution of future rates under each calibrated model.

In this assignment, Monte Carlo is implemented by simulating paths through the calibrated recombining tree under the risk-neutral measure. This is a natural extension of the tree framework because it preserves consistency with the calibrated model while allowing distributional outputs such as histograms and simulation-based confidence intervals.

## Why simulate year-T short rates

The assignment asks for a histogram of simulated interest rates in year T. This provides a direct visual comparison of the terminal cross-sectional distribution implied by each short-rate model. The difference is economically informative because long-horizon mortgage and MBS valuation depends not only on the current curve but also on the shape of future rate uncertainty.

The simulated histogram under Ho-Lee is expected to be more symmetric and may include negative-rate outcomes because the model is additive in levels. The simulated histogram under BDT is expected to be positively skewed and strictly positive because the model is lognormal in rates. This difference is one of the main reasons for comparing the two models in the first place.

# e) Valuing the mortgage with Monte Carlo

## Why revalue the mortgage under Monte Carlo

The mortgage is revalued under Monte Carlo as a consistency check on the tree-based valuation. In part (b), the mortgage rate is chosen so that the tree value is approximately par. If the Monte Carlo implementation is correct and uses the same model and exercise logic, the simulated mortgage value should also be close to par, up to sampling error.

This is an important validation step because the tree and Monte Carlo methods use different computational procedures. Agreement between them increases confidence that the implementation is correct.

## Why trigger rates are used in the simulation

The tree solution identifies the borrower’s optimal exercise region. To simulate prepayment path by path, this optimal exercise policy is converted into trigger rates for each period. Along a simulated path, prepayment occurs when the realized node is inside the exercise region.

This is computationally convenient and fully consistent with the tree solution. It allows the Monte Carlo step to inherit the exercise rule already solved by backward induction instead of re-solving the optimal stopping problem path by path.

## Why report a confidence interval

Monte Carlo produces an estimate rather than an exact value, so it is necessary to report statistical uncertainty. The confidence interval quantifies the precision of the estimate and allows a direct check of whether par lies within the simulation error band. If the par principal lies inside the interval, the Monte Carlo result is consistent with the tree valuation.

# f) Prepayment modelling

## Economic motivation

The benchmark assumption in part (b) is that borrowers refinance optimally whenever it is value-maximizing to do so. This is useful for pricing a pure embedded option, but it is not a realistic description of actual mortgage prepayment. In practice, borrowers also prepay for non-rate reasons, may fail to refinance even when it is optimal, and may become less responsive to low rates over time.

For that reason, the prepayment model in this part extends the benchmark by introducing additional reduced-form behavioral mechanisms. The objective is not to capture every possible feature of household behavior, but to move from a purely frictionless optimal-exercise model to a more realistic model that still remains transparent and computationally tractable.

## Overview of chosen mechanisms

The model incorporates three mechanisms:

1. Exogenous prepayment
2. Suboptimal refinancing
3. Burnout

These were chosen because they represent three distinct and economically important drivers of mortgage prepayment.

Exogenous prepayment captures turnover-related events such as moving house, family change, inheritance, or job relocation. These events can occur even when refinancing is not financially optimal.

Suboptimal refinancing captures the fact that many borrowers do not exercise the prepayment option immediately even when refinancing is in the money. Borrowers may face inertia, limited financial sophistication, transaction costs, affordability constraints, or delays in attention and search.

Burnout captures the idea that pools that have survived previous low-rate environments become less rate-sensitive over time, because the most refinance-responsive borrowers have already exited.

Together, these mechanisms are sufficient to move beyond the benchmark while keeping the model interpretable.

## Functional form for exogenous prepayment

Exogenous prepayment is modeled as a hazard-based probability:
p_exo(k) = 1 - exp(-lambda_k Delta).

This functional form is appropriate because turnover-type prepayment is naturally modeled as an arrival event over time. The hazard specification guarantees probabilities between zero and one and scales appropriately with the model time step.

The hazard is allowed to vary with seasoning and seasonality:
lambda_k = lambda_0 s_k eta_k.

Here s_k is a seasoning term and eta_k is a seasonal multiplier.

The seasoning component reflects the empirical idea that very new mortgages often prepay less than more seasoned mortgages. Borrowers are less likely to refinance or move immediately after origination, while prepayment intensity tends to build up over the early life of the loan. A linear ramp-up over the first few periods is used here as a parsimonious approximation.

The seasonality component reflects the fact that housing transactions often vary across the year. Since the time step is semi-annual, a simple alternating multiplier is used to capture higher and lower turnover seasons. This is deliberately simple and should be interpreted as a reduced-form seasonal effect rather than a literal month-by-month housing market model.

## Functional form for suboptimal refinancing

Suboptimal refinancing is modeled using a logistic probability:
p_refi(k,j) = logistic(beta_0 + beta_1 Incentive(k,j)).

The incentive variable is defined from the tree as the refinancing gain relative to the outstanding balance:
Incentive(k,j) = max(V_np(k,j) - L_k, 0) / L_k.

This is an economically sensible state variable because it measures how attractive refinancing is at the node. The larger the gain from refinancing, the more likely the borrower should be to act.

The logistic functional form is chosen because it is simple, bounded between zero and one, and widely used for reduced-form participation and exercise decisions. It captures the idea that refinancing is unlikely when the gain is very small, increases as the mortgage moves more deeply in the money, and eventually approaches high probabilities when the incentive becomes large.

The model also gates refinancing by optimality. If refinancing is out of the money, the refinancing probability is set to zero. This restriction is imposed to preserve economic coherence in the baseline behavioral extension. It ensures that the stochastic refinance mechanism describes delayed or incomplete exercise of a valuable option rather than arbitrary irrational exercise in unfavorable states.

## Functional form for burnout

Burnout is modeled by reducing the refinancing probability according to accumulated past incentive:
p_refi,eff = p_refi exp(-gamma B_k),

where B_k is a cumulative measure of prior refinancing incentive experienced by the surviving loan.

The purpose of this term is to capture the fact that a mortgage pool that has already been exposed to multiple favorable refinancing opportunities becomes progressively less responsive. Borrowers who were most sensitive to rate incentives tend to refinance earlier, leaving behind a survivor population that is less reactive.

The exponential damping form is used because it is simple, smooth, and guarantees that burnout only reduces, rather than increases, refinancing intensity. It is not intended as a structural behavioral law, but as a reduced-form way to represent declining responsiveness in seasoned pools.

## Why these mechanisms were chosen over a more complex model

The assignment allows either a simple but well-justified model or a richer model. The present specification is intentionally moderate in complexity. It introduces multiple realistic economic mechanisms but remains easy to explain, calibrate, and simulate. This is preferable to a much more complicated model with many borrower-level covariates that cannot be adequately estimated with the available data and time.

The model therefore trades off realism against transparency. It is rich enough to show how mortgage valuation changes once prepayment departs from frictionless optimal exercise, but still simple enough that each parameter has a clear interpretation.

## Calibration strategy

Not all parameters are directly observable from the available market data, so calibration uses a combination of public evidence, institutional plausibility, and transparent judgment.

The exogenous annual hazard is set to represent a modest baseline turnover-related prepayment intensity. This is intended to capture the fact that a non-trivial share of mortgages prepay for reasons unrelated to refinancing incentives.

The seasoning term is introduced because immediate early-life prepayment is generally less likely than prepayment after the mortgage has aged somewhat. A short ramp-up period is used to reflect this.

The refinancing logit parameters are chosen so that the refinancing probability remains low when the option is only slightly in the money, rises materially when the gain becomes meaningful, and stays below one even in strongly favorable states. This captures the idea that borrowers do not exercise deterministically, even when there is a financial benefit.

The burnout parameter is calibrated so that repeated past low-rate episodes reduce future refinancing sensitivity but do not eliminate it entirely.

Where fully empirical estimation is not possible, these values should be presented as calibrated assumptions rather than estimated structural parameters. This distinction is important and should be stated clearly in the report.

## Limitations of the prepayment model

This model remains a reduced-form approximation. It does not include default, house-price dynamics, borrower income, credit constraints, transaction-cost heterogeneity, or explicit media effects. It also does not model borrower heterogeneity directly across different loan types. Instead, it summarizes realistic prepayment behavior through a small number of economically motivated components.

This simplification is deliberate. The aim is to extend the benchmark model in a tractable and well-justified way rather than to build a full industrial prepayment engine.

## Why part (f) can change the recommended mortgage rate

Under the benchmark model, borrowers refinance optimally and therefore the lender bears the full value of a frictionless prepayment option. Once exogenous prepayment, delayed exercise, and burnout are introduced, the timing and probability of principal return changes. In particular, suboptimal exercise and burnout generally reduce the value of the borrower’s refinancing option from the lender’s perspective, which tends to increase mortgage value at a given coupon and therefore reduce the par mortgage rate required by the lender. Exogenous prepayment can have either mitigating or amplifying effects depending on timing and interaction with the coupon structure.

For this reason, the recommended mortgage rate from part (b) need not remain appropriate once a richer prepayment model is introduced. Re-solving for the par mortgage rate under the new model is therefore necessary.

## Sensitivity analysis

Sensitivity analysis is essential because some prepayment parameters are calibrated judgmentally rather than estimated precisely. The purpose is to assess whether the qualitative conclusions are robust to alternative plausible assumptions.

The key parameters to vary are:
- the exogenous annual hazard
- the seasoning speed
- the slope of the refinancing logit
- the burnout strength

This analysis is important for two reasons. First, it reveals which assumptions matter most for mortgage, PT, IO, and PO values. Second, it helps distinguish model-driven conclusions from parameter-specific conclusions.

A model whose main valuation conclusions change dramatically under small, plausible parameter changes should be interpreted more cautiously than one whose conclusions remain stable across a reasonable range.

## Effect on PT, IO, and PO tranches

The richer prepayment model affects the tranches differently.

If prepayment is slowed by suboptimal exercise or burnout, the IO usually gains value because interest payments persist for longer. The PO usually loses value because principal is returned later. The PT can move in either direction depending on the balance between slower interest decay and delayed principal recovery.

Exogenous prepayment often works in the opposite direction by generating earlier principal return even when refinancing is not attractive. This tends to support the PO and reduce the IO.

Reporting the tranche values under alternative factor combinations is therefore useful because it shows which mechanisms drive each security’s valuation.