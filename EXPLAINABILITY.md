# Decision

The agent decides what to teach next by evaluating the student's current question, answer, lesson concept, learner level, language, and learning progress. Its reasoning uses the evaluation result and the number of consecutive struggles on the current concept to decide whether to advance, reinforce, clarify a gap, or provide a new and simpler explanation.

# Inputs

The agent uses input from the student's questions and answers, the current lesson and concept, uploaded educational materials, topic information, learner level, language, assessment results, and stored learning progress. These data sources are used to evaluate the student's understanding, identify misconceptions, determine the appropriate teaching action, and continue the lesson from the correct concept.

# Limitations

The agent has limitations because its decisions depend on the educational material, learning context, stored session state, and information available at runtime. Known issues include missing or insufficient context and uncertainty in evaluating an answer, so the agent should communicate limitations instead of inventing information or treating an uncertain evaluation as fact.
