
## Feature flagging

Feature flagging is a software development technique that lets teams turn application features on or off at runtime without deploying new code or modifying the source code. 


## What is a Feature Flag?

• **Conditional logic:** It uses simple if-else statements or boolean configurations in code to decide whether a specific code path runs.
• **Decoupling deployment from release:** Code can be shipped to production safely while remaining hidden from users until the flag is flipped. 


## Main Types of Feature Flags

• **Release Toggles:** Used for progressive or canary rollouts, gradually exposing a feature to a small percentage of users before a full launch.
• **Experiment Toggles:** Used for A/B testing different variations of a feature to analyze performance and user behavior.
• **Operational (Ops) Toggles:** Act as a "kill switch" to immediately disable a broken or high-load feature in production without rolling back code.
• **Permissioning Toggles:** Tailor features to specific user roles, beta tester groups, or enterprise accounts. 

## Key Benefits

• Instant Incident Response: Cuts **Mean Time to Remediate (MTTR)** by letting teams disable a faulty feature in seconds.
• Trunk-Based Development: Allows developers to merge incomplete features into the main branch safely using short-lived branches.
• Safer Refactoring & Testing: Enables testing in production with live traffic while keeping risks contained.