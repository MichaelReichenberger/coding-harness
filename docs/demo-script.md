# Demo video script — approximately 3:30 minutes

Use `qwen2.5-coder:7b` and the [README prompt](../README.md#beispielprompt).
Record an actual run. If it fails, show the failure honestly or clearly identify a
previous successful run. The Stage-1 limit is four minutes.

| Time | Show | Say |
|---|---|---|
| 0:00–0:25 | Interface, target repository and commit | This is my own coding harness built in Python. It connects a local Ollama model to restricted file tools and isolated tests. The target is the Supermarket Receipt Kata at a fixed starting commit. |
| 0:25–0:50 | Task field and model name | The task fixes receipt printing. EACH quantities should appear as whole numbers. Weights keep three decimal places and prices keep two. The prompt describes behavior without supplying a patch. |
| 0:50–1:10 | Environment check, enter prompt, start | Each run begins with a fresh repository copy. The baseline acceptance test fails as expected, while both regression checks pass. |
| 1:10–1:50 | Progress and tool calls | The model reads the printing code and requests an edit. The controller validates each call and permits changes only in the configured scope. The model then requests the checks. |
| 1:50–2:20 | Actual diff | In this successful run, only EACH quantity formatting changed. Stored quantities, weight formatting and pricing remain unchanged. The diff shows the exact edit. |
| 2:20–2:50 | Independent final checks and report | A completion message does not prove success. The harness independently repeats the protected checks. Here, acceptance and both regression checks pass. The report and diff are downloadable. |
| 2:50–3:15 | README architecture diagram | The controller manages the loop, file tools enforce permissions, and Docker isolates repository code and tests. Action, time and output limits bound the run. The model cannot edit tests or execute arbitrary shell commands. |
| 3:15–3:30 | README and repository link | Setup was checked using a fresh clone. Manual assistance consisted of task selection, protected test preparation and a refined prompt with a file hint. No ready-made patch was supplied. |
