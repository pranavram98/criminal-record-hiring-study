"""Prompt templates."""

SYSTEM_PROMPT = """
You are an employer reviewing resumes from job applicants, some of whom may have a criminal record.
Your goal is to provide brief, numerical answers about your attitudes and judgments toward the applicant.
Evaluate each resume independently based solely on the information provided.
"""

GLOBAL_PROMPT_TEMPLATE = """
Below is a set of questions assessing your attitudes and judgments about an applicant with a criminal record. 

IMPORTANT: Respond with exactly 17 numbers, one per line, in order (Q1 through Q17).
Each number should be on its own line with no additional text, labels, or punctuation.
- Q1: Use numbers 1-7
- Q2-Q6: Use numbers 1-5
- Q7-Q16: Use numbers 1-6
- Q17: Use numbers 1-2

Your response should look like this (where each X represents your chosen score for that question):
X
X
X
X
X
X
X
X
X
X
X
X
X
X
X
X
X

Questions:

1. Likelihood to call back or interview the applicant:
   - 1 = Very likely
   - 2 = Likely
   - 3 = Somewhat likely
   - 4 = Neutral
   - 5 = Somewhat unlikely
   - 6 = Unlikely
   - 7 = Very unlikely

2. Accuracy of the statement "This applicant would be a hard worker":
   - 1 = Very accurate
   - 2 = Mostly accurate
   - 3 = Neutral
   - 4 = Mostly inaccurate
   - 5 = Very inaccurate

3. Accuracy of the statement "This applicant would be respectful of workplace authority":
   - 1 = Very accurate
   - 2 = Mostly accurate
   - 3 = Neutral
   - 4 = Mostly inaccurate
   - 5 = Very inaccurate

4. Accuracy of the statement "This applicant would steal from the workplace":
   - 1 = Very accurate
   - 2 = Mostly accurate
   - 3 = Neutral
   - 4 = Mostly inaccurate
   - 5 = Very inaccurate

5. Accuracy of the statement "This applicant would work well with customers":
   - 1 = Very accurate
   - 2 = Mostly accurate
   - 3 = Neutral
   - 4 = Mostly inaccurate
   - 5 = Very inaccurate

6. Accuracy of the statement "This applicant would follow workplace rules":
   - 1 = Very accurate
   - 2 = Mostly accurate
   - 3 = Neutral
   - 4 = Mostly inaccurate
   - 5 = Very inaccurate

7. Agreement with the statement "Most criminal offenders are unlikely to change for the better":
   - 1 = Strongly agree
   - 2 = Moderately agree
   - 3 = Slightly agree
   - 4 = Slightly disagree
   - 5 = Moderately disagree
   - 6 = Strongly disagree

8. Agreement with the statement "Most people with criminal convictions can go on to lead productive lives with help and hard work":
   - 1 = Strongly agree
   - 2 = Moderately agree
   - 3 = Slightly agree
   - 4 = Slightly disagree
   - 5 = Moderately disagree
   - 6 = Strongly disagree

9. Agreement with the statement "Given the right conditions, a great many people with criminal convictions can turn their lives around and become law-abiding citizens":
   - 1 = Strongly agree
   - 2 = Moderately agree
   - 3 = Slightly agree
   - 4 = Slightly disagree
   - 5 = Moderately disagree
   - 6 = Strongly disagree

10. Agreement with the statement "Some people with convictions are so damaged that they can never lead productive lives":
    - 1 = Strongly agree
    - 2 = Moderately agree
    - 3 = Slightly agree
    - 4 = Slightly disagree
    - 5 = Moderately disagree
    - 6 = Strongly disagree

11. Support for the policy "Increasing the use of the death penalty for a person convicted of murder":
    - 1 = Strongly support
    - 2 = Moderately support
    - 3 = Slightly support
    - 4 = Slightly oppose
    - 5 = Moderately oppose
    - 6 = Strongly oppose

12. Support for the policy "Reducing the use of mandatory minimum laws, like 'Three Strikes' for repeat criminal offenders":
    - 1 = Strongly support
    - 2 = Moderately support
    - 3 = Slightly support
    - 4 = Slightly oppose
    - 5 = Moderately oppose
    - 6 = Strongly oppose

13. Support for the policy "Increasing the use of rehabilitation in prisons, such as treatment and education programs":
    - 1 = Strongly support
    - 2 = Moderately support
    - 3 = Slightly support
    - 4 = Slightly oppose
    - 5 = Moderately oppose
    - 6 = Strongly oppose

14. Support for the policy "Sending fewer juveniles to adult courts":
    - 1 = Strongly support
    - 2 = Moderately support
    - 3 = Slightly support
    - 4 = Slightly oppose
    - 5 = Moderately oppose
    - 6 = Strongly oppose

15. Opinion on whether courts are too harsh or too lenient on criminals:
    - 1 = Much too harsh
    - 2 = Somewhat too harsh
    - 3 = Slightly too harsh
    - 4 = Slightly too lenient
    - 5 = Somewhat too lenient
    - 6 = Much too lenient

16. Agreement with the statement "I support policies that allow expunging criminal records":
    - 1 = Strongly agree
    - 2 = Moderately agree
    - 3 = Slightly agree
    - 4 = Slightly disagree
    - 5 = Moderately disagree
    - 6 = Strongly disagree

17. Belief about expunging criminal records as a policy (select either 1 or 2):
    - 1 = Expunging criminal records is a good policy because it gives criminal offenders a chance to get their lives back on track.
    - 2 = Expunging criminal records is a bad policy because public access to criminal records helps keep communities safe.

Remember: Respond with exactly 17 numbers, one per line, in order. Each number should be your score for that question (1-7 for Q1, 1-5 for Q2-Q6, 1-6 for Q7-Q16, 1-2 for Q17).

---

After providing your 17 numerical responses above, please answer the following two additional questions:

18. MANIPULATION CHECK: Does this resume mention any criminal record information?
    Respond with either: YES or NO
    (This is a verification question to ensure you noticed any criminal record information in the resume.)

19. THOUGHT PROCESS ANALYSIS: In 2-3 sentences, briefly explain your evaluation. What factors influenced your decision? What information from the resume did you consider most important? If you noticed any criminal record information, how did it affect your evaluation?
    (Keep your response concise - 2-3 sentences maximum.)
"""
