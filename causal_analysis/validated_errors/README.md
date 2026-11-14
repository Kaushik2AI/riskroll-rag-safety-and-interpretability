# Validated Natural Errors

Store manually validated natural errors here.

Each retained case should record:
- task ID and question
- natural erroneous span
- minimally corrected span
- exact retrieved evidence shown to the model
- evidence that the correct fact was available
- sentence/token location of the error
- amount of downstream text
- case type (primary, self-recovery control, retrieval-conflict secondary, reject)

Do not treat an automatic mismatch as a validated hallucination.
