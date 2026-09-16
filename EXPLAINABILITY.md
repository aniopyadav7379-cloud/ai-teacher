# AI Teacher Explainability

## Decision Logic

The agent decides what to teach next by evaluating the student's current question, answer, lesson concept, learner level, language, and learning progress. It uses the evaluation result and the number of consecutive struggles on the current concept to determine whether to advance, reinforce the concept, clarify a learning gap, or provide a new and simpler explanation.

## Data Inputs

The primary data sources are the student's questions and answers, the current lesson and concept, uploaded educational materials, topic information, learner level, language, assessment results, and stored learning progress. The agent also uses retrieved educational content from the RAG pipeline to provide context for teaching and evaluation.

## Known Limitations

One limitation is that the quality of teaching decisions depends on the educational material, available lesson context, stored session state, and information available at runtime. Another known issue is that answer evaluation and misconception detection can be uncertain, so the agent should communicate insufficient context or uncertainty instead of inventing information.
