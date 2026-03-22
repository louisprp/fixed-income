SW Summative work: Monte Carlo Simulation [150 marks] In this summative, you will build and calibrate a quantitative mortgage valuation model as described below by writing an appropriate code in Matlab/R/Excel/Python etc or by building up Excel spreadsheets. If you use Excel sheets, please use T = 5 years and N = 1000 simulations at all points applicable below. If you are writing code, please use T = 10 and N = 100 000. Otherwise, the choice of the software is yours. You can use AI to help you writing your code. (You have to hand in the code itself, we are not interested in prompts.) Make sure that your code follows the method we have described in Chapter 3-4. Please organize your assignment as follows:

• There should be a detailed write up, which includes figures and procedures to get your answers. This should be self-contained and well-explained. In principal, your mark is based on this document. The other files are for us to replicate how you got your results.

• We also expect three sets of codes/Excel sheets (building on each other) in a zip folder. Ideally, after expanding your folder, we can run your code/see your Excel sheet generating all the figures and output on which the write-up is based.

– The first set should correspond to problem (a): calibrating the interest rate models. This should be set up in a way that it is for us to vary the input (i.e. feed in different yield curve data or calibrated parameters) for the estimation.

– The second one should correspond to problems (b)-(e): evaluating the securities with different methodologies

– The third one should correspond to problem (f): introducing new factors into the prepayment model.

It is January 2026 and you are working in the back-office of the University Building Society (UBS) providing mortgages to university students and employees all over UK and issuing mortgage backed securities based on those mortgages. UBS has just decided to market a novel product, a T-year fixed rate mortgage. Your boss asks you to develop a model which helps to come up with the right interest rate for this product. If the interest rate is too high, no one will buy the product. If it is too low, UBS will lose on the mortgages. (Hint: These problems build on the example in 13.6 in Veronesi (2010) with longer maturity and a different yield curve. Perhaps a good way to start is to write the code using the original data in that example, so you can verify whether your code gives the same numbers. Then you can modify the input according to the problem below.)

(a) Constructing interest rate trees. [30 marks] You decide to work with the binomial tree methodology. For this, you have to start with a binomial tree model of risk-neutral short rates. For robustness and simplicity, you decide to experiment both with the Ho-Lee model (HL) and the Black-Derman-Toy (BDT) model, with semi-annual (Δ = 0.5), continuously compounded short-rates.

Data requirements: You must source yield curve data yourself from a reputable provider (e.g. Bank of England, Federal Reserve, Bloomberg). In your write-up, clearly document: (i) the source and date of your yield curve data, (ii) how do you obtain the missing parameters for your calibrations (iii) how you handled the compounding convention. Justify your choices. (Hint: if you do not find the ideal data, it is ok to settle for a second-best. However, explain clearly the compromises you are making. )

(b) Valuing the mortgage contract [10 marks] As a benchmark, assume that the buyers of the mortgage will prepay optimally and will not default. Following our method of valuing mortgages in Chapter 4 of the lecture notes, find the fixed rates for which the value of the T-year mortgage is (approximately) par under the Ho-Lee model and under the Black-Derman-Toy model. Which one is higher? Do you have any intuition for that?

(c) Constructing MBSs [20 marks] As the new product is very successful, UBS decides to issue a pass-through security, an interest rate only security and a principal only security backed by these mortgages. The maturity of these MBSs are the same. However, to recover the cost of securitization, UBS decides to offer them with an interest rate 50 bp lower than the mortgage rate you recommend in problem (b). Following our method in Chapter 4, can you find the fair value for these new products? What is the difference if you use BDT vs Ho-Lee?

(d) Interest rate trees with MC [20 marks] Now you switch to the Monte Carlo methodology. Using N simulations plot a histogram of the simulated interest rates in year T under each of the short rate models. Can you comment on the difference?

(e) Valuing the mortgage with MC [20 marks] Let us proceed with BDT from here. Use the corresponding mortgage rate you have found in problem (b). As a check on your calculations, you decide to revalue the mortgage contract using a Monte Carlo methodology. What is your point estimate and your confidence interval using N simulations? Is that consistent with your answer in (b)?

(f) Prepayment modelling [50 marks] You decide to incorporate additional assumptions on prepayment behaviour. (You continue with the BDT model and Monte Carlo.) Real-world mortgage prepayment is driven by multiple factors beyond pure interest rate optimality. Your task is to design, justify, calibrate, and implement a prepayment model that captures realistic borrower behaviour.

Factors to consider. The following is a non-exhaustive list of factors that may influence prepayment. You are not expected to model all of them, but your model should capture at least two distinct economic mechanisms, justified by data or literature:

• Exogenous prepayment: Mortgages are sometimes prepaid even when suboptimal (e.g. due to house sales, divorce, inheritance, job relocation). These events may exhibit seasonality (e.g. housing transactions peak in summer) and may depend on the age of the mortgage.

• Suboptimal exercise: Borrowers may fail to refinance even when optimal, due to inattention, transaction costs, credit constraints, or behavioural frictions. The probability of exercising the prepayment option when in-the-money may depend on how far in-the-money the option is (the “moneyness” of refinancing).

• Burnout: Pools of mortgages that have experienced low interest rate environments may exhibit lower prepayment rates subsequently, as the most rate-sensitive borrowers have already refinanced.

• Media and sentiment effects: Prepayment activity may spike following media coverage of low rates or advertising campaigns by lenders, even controlling for rate levels.

• Path dependence: Prepayment may depend not just on current rates but on the path of rates (e.g. whether rates have been declining steadily versus a sudden drop).

• Borrower heterogeneity: Different borrower types (by income, credit score, loan-to-value ratio, or property type) may exhibit systematically different prepayment behaviour.

Data sources. You are encouraged to ground your model in empirical evidence. Possible data sources include (but are not limited to):

• Fannie Mae and Freddie Mac loan-level performance data (freely available)

• UK Finance mortgage statistics and FCA product sales data

• Bank of England mortgage market reports

• Academic studies on prepayment behaviour

• Industry prepayment models (e.g. PSA benchmark, Bloomberg prepayment vectors)

You may also use reasonable assumptions where data is unavailable, but this should be clearly flagged and justified.

Requirements. Your submission for this part must include:

(i) A clear description of the economic mechanisms your model captures and the functional forms you propose.

(ii) Economic and/or empirical justification for your modelling choices. Why do your specifications make sense? What evidence supports them?

(iii) Documentation of how you calibrated or estimated your parameters, including data sources, sample periods, and any limitations.

(iv) Sensitivity analysis: how do your mortgage valuations change under alternative plausible parameter values?

What is your point estimate and confidence interval for the mortgage value under your prepayment model, using the interest rate from part (b)?

How would you adjust the mortgage rate you recommend to UBS? Using your prepayment model, find the value of the pass-through security, the interest-only security, and the principal-only security with N Monte Carlo simulations. As in part (c), use a coupon rate 50 bp below the mortgage rate you recommend. Report point estimates and confidence intervals for each tranche.

Can you analyse how each of your introduced factor affected your answers?

Evaluation criteria. Marks will be awarded for the economic coherence of your model, the quality of your empirical grounding and the clarity of your exposition. A simple but well-justified model is preferable to a complex model with ad hoc assumptions. Ambitious models that incorporate richer data (e.g. actual prepayment time series, borrower-level heterogeneity) will be rewarded, provided the additional complexity is well-motivated and competently executed.